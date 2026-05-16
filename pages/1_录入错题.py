"""引导式录入错题"""

import streamlit as st
from database import (
    init_db, get_sources, add_source, add_problem,
    get_all_knowledge_points
)
from utils import inject_katex, save_uploaded_image, check_password

st.set_page_config(page_title="录入错题", page_icon="✍️",
                   layout="centered", initial_sidebar_state="collapsed")
inject_katex()
check_password()
init_db()

st.title("✍️ 录入新错题")

# ── Step 1: 分类定位 ──
st.markdown("### 📂 分类定位")

c1, c2, c3 = st.columns(3)
with c1:
    sources = get_sources()
    source_options = {s["name"]: s["id"] for s in sources}
    source_choice = st.selectbox(
        "来源（练习册/试卷）",
        options=["+ 新建来源"] + list(source_options.keys()),
        key="source_select"
    )
    if source_choice == "+ 新建来源":
        new_source = st.text_input("输入新来源名称", key="new_source")
        source_id = add_source(new_source) if new_source else None
    else:
        source_id = source_options.get(source_choice)

with c2:
    module = st.selectbox(
        "一级学科 *",
        options=["高等数学", "线性代数", "概率统计"],
        key="module"
    )

with c3:
    chapter = st.text_input(
        "具体章节 *",
        placeholder="如：一元积分学-定积分的应用",
        key="chapter"
    )

# ── Step 2: 题干（拍照为主） ──
st.markdown("### 📷 题干")
question_image = None
q_img = st.file_uploader(
    "拍题目照片", type=["png", "jpg", "jpeg", "webp"],
    key="question_image_upload",
    help="直接拍照上传题干"
)
if q_img:
    question_image = save_uploaded_image(q_img)
    st.image(q_img, width=400)

question_text = st.text_area(
    "题干补充说明（可选，支持 $LaTeX$）",
    height=80, key="question_text",
    placeholder="可留空。如需补充公式或额外描述再填写……",
    label_visibility="visible"
)

# ── Step 3: 正解（拍照为主） ──
st.markdown("### ✅ 正确解法")
solution_image = None
s_img = st.file_uploader(
    "拍标准答案", type=["png", "jpg", "jpeg", "webp"],
    key="solution_image_upload",
    help="拍照上传正确解析过程"
)
if s_img:
    solution_image = save_uploaded_image(s_img)
    st.image(s_img, width=400)

standard_solution = st.text_area(
    "正解补充说明（可选，支持 $LaTeX$）",
    height=80, key="standard_solution",
    placeholder="可留空。关键步骤的文字说明……",
    label_visibility="visible"
)

# ── Step 4: 我的错误解法 ──
st.markdown("### ❌ 我当时的错误解法")
st.caption("记录思维偏差是归纳的关键——当时你是怎么想的？")
my_wrong_solution = st.text_area(
    "错误解法",
    height=120,
    key="my_wrong_solution",
    placeholder="写下你当时错误的思路...",
    label_visibility="collapsed"
)

# ── Step 5: 认知与归纳 ──
st.markdown("### 🧠 认知与归纳")

c4, c5 = st.columns(2)
with c4:
    error_type = st.selectbox(
        "错误类型 *",
        options=["概念模糊", "计算失误", "经典套路未识别", "条件漏看", "其他"],
        key="error_type"
    )

with c5:
    difficulty = st.slider("难度", min_value=1, max_value=5, value=3, key="difficulty")

existing_kps = get_all_knowledge_points()
core_knowledge_points = st.text_input(
    "核心知识点",
    placeholder="如：泰勒公式、介值定理、o(x^n)处理（逗号分隔）",
    key="core_knowledge_points"
)
if existing_kps:
    with st.expander(f"📚 已录知识点（{len(existing_kps)}个，点击可补充）", expanded=False):
        cols = st.columns(3)
        for i, kp in enumerate(existing_kps):
            with cols[i % 3]:
                if st.button(kp, key=f"kp_{kp}"):
                    current = st.session_state.core_knowledge_points or ""
                    if kp not in current:
                        new_val = f"{current}, {kp}" if current else kp
                        st.session_state.core_knowledge_points = new_val
                        st.rerun()

key_insight = st.text_input(
    "💡 一句话大彻大悟",
    placeholder="例如：看到有界闭区间上连续函数，先想介值定理和零点定理",
    key="key_insight"
)

# ── Submit ──
st.markdown("---")
if st.button("💾 保存错题", type="primary", use_container_width=True):
    errors = []
    if not question_text.strip() and not question_image:
        errors.append("请至少拍照上传题干，或输入题干文字")
    if not chapter.strip():
        errors.append("章节不能为空")
    if source_id is None:
        errors.append("请选择或输入来源")

    if errors:
        for e in errors:
            st.error(e)
    else:
        data = {
            "source_id": source_id,
            "module": module,
            "chapter": chapter.strip(),
            "question_text": question_text,
            "question_image": question_image,
            "standard_solution": standard_solution,
            "solution_image": solution_image,
            "my_wrong_solution": my_wrong_solution,
            "image_path": None,
            "error_type": error_type,
            "core_knowledge_points": core_knowledge_points,
            "key_insight": key_insight,
            "difficulty": difficulty,
        }
        pid = add_problem(data)
        st.success(f"✅ 错题已保存（ID: {pid}），下次复习日期：明天")
        for k in ("question_text", "standard_solution", "my_wrong_solution",
                  "core_knowledge_points", "key_insight",
                  "question_image_upload", "solution_image_upload"):
            st.session_state[k] = None if k.endswith("_upload") else ""
        st.session_state.chapter = ""
        st.rerun()
