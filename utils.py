"""Common utilities: KaTeX rendering, page chrome, handwriting pad."""

import streamlit as st
import os
import re
import uuid
import base64
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

HANDWRITING_PAD_HTML = r"""
<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
    <button onclick="clearPad_%%KEY%%()" style="padding:4px 12px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;">清除</button>
    <input type="color" id="penColor_%%KEY%%" value="#000000" oninput="ctx_%%KEY%%.strokeStyle=this.value" style="width:28px;height:24px;border:none;cursor:pointer;">
    <button id="eraserBtn_%%KEY%%" onclick="toggleEraser_%%KEY%%()" style="padding:4px 12px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;">橡皮</button>
    <input type="range" id="penSize_%%KEY%%" min="1" max="8" value="2" oninput="ctx_%%KEY%%.lineWidth=this.value" style="width:60px;">
  </div>
  <canvas id="pad_%%KEY%%" width="350" height="180"
    style="border:1px solid #ccc;border-radius:6px;touch-action:none;width:100%;max-width:350px;">
  </canvas>
</div>
<script>
(function() {
  var canvas = document.getElementById('pad_%%KEY%%');
  var ctx = canvas.getContext('2d');
  window['ctx_%%KEY%%'] = ctx;
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  var existing = '%%DATA%%';
  if (existing) {
    var img = new Image();
    img.onload = function() { ctx.drawImage(img, 0, 0); };
    img.src = existing;
  }

  var drawing = false;
  var erasing = false;
  window['toggleEraser_%%KEY%%'] = function() {
    erasing = !erasing;
    var btn = document.getElementById('eraserBtn_%%KEY%%');
    btn.textContent = erasing ? '画笔' : '橡皮';
  };

  window['clearPad_%%KEY%%'] = function() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    window.parent.postMessage({isStreamlitMessage: true, type: 'streamlit:setComponentValue', data: ''}, '*');
  };

  function getPos(e) {
    var rect = canvas.getBoundingClientRect();
    var scaleX = canvas.width / rect.width;
    var scaleY = canvas.height / rect.height;
    return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
  }

  canvas.addEventListener('pointerdown', function(e) {
    drawing = true;
    var p = getPos(e);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  });

  canvas.addEventListener('pointermove', function(e) {
    if (!drawing) return;
    e.preventDefault();
    var p = getPos(e);
    if (erasing) {
      ctx.clearRect(p.x - 8, p.y - 8, 16, 16);
    } else {
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
    }
  });

  canvas.addEventListener('pointerup', function() {
    drawing = false;
    ctx.closePath();
    window.parent.postMessage({isStreamlitMessage: true, type: 'streamlit:setComponentValue', data: canvas.toDataURL('image/png')}, '*');
  });
})();
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
    _show_image(problem.get("question_handwriting"))

    if problem.get("image_path"):
        _show_image(problem.get("image_path"))

    if show_solution:
        st.markdown("### ✅ 正解")
        if problem.get("standard_solution"):
            st.markdown(problem["standard_solution"])
        _show_image(problem.get("solution_image"))
        _show_image(problem.get("solution_handwriting"))

        if problem.get("my_wrong_solution"):
            st.markdown("### ❌ 我的错误解法")
            st.markdown(problem["my_wrong_solution"])
        _show_image(problem.get("wrong_solution_handwriting"))

        if problem.get("key_insight"):
            st.markdown(f"### 💡 关键彻悟\n> {problem['key_insight']}")


def _show_image(rel_path):
    if not rel_path:
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_full = os.path.normpath(os.path.join(base_dir, rel_path))
    if os.path.isfile(img_full):
        st.image(Image.open(img_full), use_container_width=True)


def save_uploaded_image(uploaded_file) -> str:
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")
    os.makedirs(img_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.png"
    fpath = os.path.join(img_dir, fname)
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.save(fpath, "PNG")
    return os.path.join("data", "images", fname)


def save_base64_image(data_url: str) -> str:
    """Save a base64 data-URL to the images directory. Returns relative path or ''."""
    if not data_url or not data_url.startswith("data:image/"):
        return ""
    match = re.match(r"data:image/\w+;base64,(.+)", data_url)
    if not match:
        return ""
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")
    os.makedirs(img_dir, exist_ok=True)
    img_data = base64.b64decode(match.group(1))
    fname = f"hw_{uuid.uuid4().hex}.png"
    fpath = os.path.join(img_dir, fname)
    with open(fpath, "wb") as f:
        f.write(img_data)
    return os.path.join("data", "images", fname)


def handwriting_component(key: str, label: str, existing_path: str = "") -> str:
    """Embed a handwriting pad and return a saved image path on change, or ''."""
    st.caption(label)
    existing_data = ""
    if existing_path:
        img_full = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), existing_path))
        if os.path.isfile(img_full):
            with open(img_full, "rb") as f:
                existing_data = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

    html = HANDWRITING_PAD_HTML.replace("%%KEY%%", key).replace("%%DATA%%", existing_data)
    result = st.components.v1.html(html, height=260)

    if result is None:
        return ""

    if not isinstance(result, str) or not result.startswith("data:image/png;base64,"):
        # User cleared the pad (empty string)
        return "clear"

    # Compare with existing to avoid re-saving unchanged drawings
    if result == existing_data:
        return existing_path

    return save_base64_image(result)
