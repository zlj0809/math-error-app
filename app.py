"""考研数学错题归纳 — 首页仪表盘 & 盲盒复习"""

import streamlit as st
import datetime

from database import init_db, get_stats, get_module_due_counts, add_review
from database import export_db_bytes, import_db
from review import draw_blindbox
from utils import inject_katex, render_problem_detail, check_password

st.set_page_config(page_title="错题盲盒", page_icon="🎲",
                   layout="centered", initial_sidebar_state="collapsed")
inject_katex()
check_password()
init_db()

# ── Sidebar: Backup / Restore ──
with st.sidebar:
    st.markdown("### 数据备份")
    st.caption("定期下载备份，推送代码前先备份！")

    db_bytes = export_db_bytes()
    today = datetime.date.today().isoformat()
    st.download_button(
        label="下载备份",
        data=db_bytes,
        file_name=f"math_errors_backup_{today}.db",
        mime="application/octet-stream",
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### 恢复备份")
    uploaded = st.file_uploader("上传备份文件", type=["db"], label_visibility="collapsed")
    if uploaded:
        if st.button("确认恢复", type="primary", use_container_width=True):
            if import_db(uploaded):
                st.success("恢复成功！页面将自动刷新。")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("恢复失败，请检查文件是否正确。")

st.title("🎲 考研数学错题归纳")

# ── Dashboard ──
stats = get_stats()
c1, c2, c3 = st.columns(3)
c1.metric("总错题数", stats["total"])
c2.metric("今日待复习", stats["due"], delta=f"{stats['due']} 题需要复习" if stats["due"] else None)
c3.metric("已吃透", stats["mastered"])

# Module breakdown
if stats["due"]:
    st.markdown("---")
    module_due = get_module_due_counts()
    st.markdown("**各学科待复习:**  " + "  |  ".join(
        f"{mod}: {cnt}题" for mod, cnt in module_due.items()
    ))

# ── Blind Box Review ──
st.markdown("---")

# Session state for blind box
if "box" not in st.session_state:
    st.session_state.box = []           # remaining problems
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "revealed" not in st.session_state:
    st.session_state.revealed = False
if "review_done" not in st.session_state:
    st.session_state.review_done = False
if "box_size" not in st.session_state:
    st.session_state.box_size = 5

# Start button
if not st.session_state.box:
    if st.button("🎯 开始盲盒复习", type="primary", use_container_width=True):
        drawn = draw_blindbox(st.session_state.box_size)
        if drawn:
            st.session_state.box = drawn
            st.session_state.current_idx = 0
            st.session_state.revealed = False
            st.session_state.review_done = False
            st.rerun()
        else:
            st.success("暂时没有待复习的错题，去录入几道吧！")
    st.session_state.box_size = st.number_input(
        "每次抽取", min_value=1, max_value=20, value=st.session_state.box_size,
        step=1, key="box_size_widget"
    )

# Review flow
if st.session_state.box:
    problems = st.session_state.box
    idx = st.session_state.current_idx

    if idx >= len(problems):
        st.success(f"🎉 本轮盲盒已完成！共复习 {len(problems)} 道错题。")
        if st.button("再来一轮"):
            st.session_state.box = []
            st.rerun()
    else:
        prob = problems[idx]
        total = len(problems)
        st.progress(idx / total, text=f"第 {idx + 1}/{total} 题")

        if not st.session_state.revealed:
            # Show question only
            st.markdown("### 📝 请用草稿纸重做此题")
            render_problem_detail(prob, show_solution=False)

            if st.button("揭晓答案 ✨", type="primary"):
                st.session_state.revealed = True
                st.rerun()
        else:
            # Show full solution
            render_problem_detail(prob, show_solution=True)

            st.markdown("### 自我评估")
            rating = st.radio(
                "这道题你做得怎么样？",
                options=[1, 2, 3],
                format_func=lambda x: {
                    1: "❌ 没做出来",
                    2: "🟡 做出来了但不够熟练",
                    3: "✅ 完全掌握"
                }[x],
                horizontal=False,
                key=f"rating_{idx}"
            )

            notes = st.text_input("复习备注（可选）", key=f"notes_{idx}")

            if st.button("提交并下一题 ➡️", type="primary"):
                add_review(prob["id"], rating, notes)
                st.session_state.current_idx += 1
                st.session_state.revealed = False
                st.rerun()
