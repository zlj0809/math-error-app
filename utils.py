"""Common utilities: KaTeX rendering, page chrome."""

import streamlit as st
import os
import uuid
from PIL import Image

KATEX_CDN = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {delimiters: [
        {left:'$$', right:'$$', display:true},
        {left:'$', right:'$', display:false}
    ]});">
</script>
"""


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title("🔐 考研数学错题本")
    pwd = st.text_input("请输入访问密码", type="password")
    if st.button("进入"):
        if pwd == st.secrets.get("APP_PASSWORD", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密码错误")
    st.stop()


def inject_katex():
    st.markdown(KATEX_CDN, unsafe_allow_html=True)


def render_latex(text: str, display: bool = False):
    """Wrap LaTeX in delimiters for KaTeX auto-render."""
    if not text:
        return ""
    if display:
        return f"$$\n{text}\n$$"
    return f"${text}$"


def math_textarea(label: str, value: str = "", height: int = 150, key: str = None):
    """Textarea for LaTeX content with live preview toggle."""
    text = st.text_area(label, value=value, height=height, key=key)
    if text:
        with st.expander("预览", expanded=False):
            st.markdown(text)
    return text


def render_problem_detail(problem, show_solution: bool = False):
    """Render a full problem detail card."""
    if not isinstance(problem, dict):
        problem = dict(problem)
    st.markdown(f"**来源:** {problem.get('source_name') or '—'}  |  "
                f"**学科:** {problem['module']}  |  "
                f"**章节:** {problem['chapter']}")
    st.markdown(f"**错误类型:** {problem['error_type']}  |  "
                f"**难度:** {'⭐' * problem['difficulty']}  |  "
                f"**状态:** {problem['status']}")

    if problem.get("core_knowledge_points"):
        st.markdown(f"**知识点:** {problem['core_knowledge_points']}")

    st.markdown("### 📷 题干")
    if problem.get("question_text"):
        st.markdown(problem["question_text"])
    _show_image(problem.get("question_image"))

    if problem.get("image_path"):
        _show_image(problem.get("image_path"))

    if show_solution:
        st.markdown("### ✅ 正解")
        if problem.get("standard_solution"):
            st.markdown(problem["standard_solution"])
        _show_image(problem.get("solution_image"))

        if problem.get("my_wrong_solution"):
            st.markdown("### ❌ 我的错误解法")
            st.markdown(problem["my_wrong_solution"])
        if problem.get("key_insight"):
            st.markdown(f"### 💡 关键彻悟\n> {problem['key_insight']}")


def _show_image(rel_path):
    if not rel_path:
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_full = os.path.join(base_dir, rel_path)
    if os.path.exists(img_full):
        st.image(Image.open(img_full), use_container_width=True)


def save_uploaded_image(uploaded_file) -> str:
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")
    os.makedirs(img_dir, exist_ok=True)
    ext = os.path.splitext(uploaded_file.name)[1] or ".png"
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(img_dir, fname)
    img = Image.open(uploaded_file)
    img.save(fpath)
    return os.path.join("data", "images", fname)
