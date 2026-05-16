import sqlite3
import os
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "data", "math_errors.db")
IMG_DIR = os.path.join(DB_DIR, "data", "images")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER REFERENCES sources(id),
            module TEXT NOT NULL,
            chapter TEXT NOT NULL,
            question_text TEXT DEFAULT '',
            question_image TEXT,
            standard_solution TEXT,
            solution_image TEXT,
            my_wrong_solution TEXT,
            image_path TEXT,
            error_type TEXT NOT NULL,
            core_knowledge_points TEXT,
            key_insight TEXT,
            difficulty INTEGER DEFAULT 3,
            review_count INTEGER DEFAULT 0,
            status TEXT DEFAULT '未掌握',
            next_review_date TEXT,
            review_stage INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER REFERENCES problems(id),
            reviewed_at TEXT DEFAULT (datetime('now','localtime')),
            self_rating INTEGER,
            notes TEXT
        );
    """)

    # Migration: add new columns if they don't exist
    for col, col_type in [
        ("question_image", "TEXT"),
        ("solution_image", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE problems ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.commit()
    conn.close()


# ── Sources ──

def get_sources():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sources ORDER BY name").fetchall()
    conn.close()
    return rows


def add_source(name):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO sources (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        row = conn.execute("SELECT id FROM sources WHERE name=?", (name.strip(),)).fetchone()
        return row["id"]
    finally:
        conn.close()


# ── Problems ──

REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30]


def add_problem(data: dict) -> int:
    conn = get_conn()
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    cur = conn.execute("""
        INSERT INTO problems (source_id, module, chapter, question_text,
            question_image, standard_solution, solution_image,
            my_wrong_solution, image_path, error_type,
            core_knowledge_points, key_insight, difficulty, next_review_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data["source_id"], data["module"], data["chapter"],
        data.get("question_text", ""), data.get("question_image", ""),
        data.get("standard_solution", ""), data.get("solution_image", ""),
        data.get("my_wrong_solution", ""), data.get("image_path", ""),
        data["error_type"], data.get("core_knowledge_points", ""),
        data.get("key_insight", ""), data.get("difficulty", 3),
        tomorrow
    ))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def update_problem(problem_id: int, data: dict):
    conn = get_conn()
    fields = []
    values = []
    for k in ["source_id", "module", "chapter", "question_text",
              "question_image", "standard_solution", "solution_image",
              "my_wrong_solution", "image_path",
              "error_type", "core_knowledge_points", "key_insight",
              "difficulty", "status"]:
        if k in data:
            fields.append(f"{k}=?")
            values.append(data[k])
    if not fields:
        conn.close()
        return
    values.append(problem_id)
    conn.execute(f"UPDATE problems SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_problem(problem_id: int):
    conn = get_conn()
    row = conn.execute(
        "SELECT image_path, question_image, solution_image FROM problems WHERE id=?",
        (problem_id,)
    ).fetchone()
    if row:
        for field in ["image_path", "question_image", "solution_image"]:
            if row[field]:
                img_full = os.path.join(DB_DIR, row[field])
                if os.path.exists(img_full):
                    os.remove(img_full)
    conn.execute("DELETE FROM reviews WHERE problem_id=?", (problem_id,))
    conn.execute("DELETE FROM problems WHERE id=?", (problem_id,))
    conn.commit()
    conn.close()


def get_problem(problem_id: int):
    conn = get_conn()
    row = conn.execute("""
        SELECT p.*, s.name as source_name
        FROM problems p LEFT JOIN sources s ON p.source_id = s.id
        WHERE p.id=?
    """, (problem_id,)).fetchone()
    conn.close()
    return row


def search_problems(source_id=None, module=None, chapter=None,
                    error_type=None, status=None, keyword=None, limit=200):
    conn = get_conn()
    query = """
        SELECT p.*, s.name as source_name
        FROM problems p LEFT JOIN sources s ON p.source_id = s.id
        WHERE 1=1
    """
    params = []
    if source_id:
        query += " AND p.source_id=?"
        params.append(source_id)
    if module:
        query += " AND p.module=?"
        params.append(module)
    if chapter:
        query += " AND p.chapter=?"
        params.append(chapter)
    if error_type:
        query += " AND p.error_type=?"
        params.append(error_type)
    if status:
        query += " AND p.status=?"
        params.append(status)
    if keyword:
        query += """ AND (p.question_text LIKE ? OR p.core_knowledge_points LIKE ?
                   OR p.key_insight LIKE ? OR p.chapter LIKE ?)"""
        kw = f"%{keyword}%"
        params.extend([kw, kw, kw, kw])
    query += " ORDER BY p.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_due_problems():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT p.*, s.name as source_name
        FROM problems p LEFT JOIN sources s ON p.source_id = s.id
        WHERE p.status IN ('未掌握','模糊')
          AND p.next_review_date <= ?
        ORDER BY p.next_review_date ASC
    """, (today,)).fetchall()
    conn.close()
    return rows


def get_stats():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    total = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
    due = conn.execute("""
        SELECT COUNT(*) FROM problems
        WHERE status IN ('未掌握','模糊') AND next_review_date <= ?
    """, (today,)).fetchone()[0]
    mastered = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE status='已吃透'"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "due": due, "mastered": mastered}


def get_all_knowledge_points():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT core_knowledge_points FROM problems WHERE core_knowledge_points != ''"
    ).fetchall()
    conn.close()
    points = set()
    for r in rows:
        for pt in r["core_knowledge_points"].split(","):
            pt = pt.strip()
            if pt:
                points.add(pt)
    return sorted(points)


# ── Review ──

def add_review(problem_id: int, self_rating: int, notes: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO reviews (problem_id, self_rating, notes) VALUES (?,?,?)",
        (problem_id, self_rating, notes)
    )
    prob = conn.execute(
        "SELECT review_stage, review_count, status FROM problems WHERE id=?",
        (problem_id,)
    ).fetchone()

    stage = prob["review_stage"]
    count = prob["review_count"] + 1

    if self_rating == 1:
        stage = max(0, stage - 1)
    elif self_rating == 3:
        stage = min(5, stage + 1)

    days = REVIEW_INTERVALS[stage]
    next_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    new_status = "已吃透" if stage >= 5 else ("模糊" if stage >= 2 else "未掌握")

    conn.execute("""
        UPDATE problems SET review_stage=?, review_count=?,
        next_review_date=?, status=? WHERE id=?
    """, (stage, count, next_date, new_status, problem_id))
    conn.commit()
    conn.close()


def get_module_due_counts():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT module, COUNT(*) as cnt FROM problems
        WHERE status IN ('未掌握','模糊') AND next_review_date <= ?
        GROUP BY module
    """, (today,)).fetchall()
    conn.close()
    return {r["module"]: r["cnt"] for r in rows}
