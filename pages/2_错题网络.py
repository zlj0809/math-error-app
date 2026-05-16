"""错题网络 — 横向+纵向多维度检索"""

import streamlit as st
from database import (
    init_db, get_sources, search_problems, get_problem,
    update_problem, delete_problem, get_chapters, add_chapter
)
from utils import inject_katex, render_problem_detail, check_password

st.set_page_config(page_title="错题网络", page_icon="🔍",
                   layout="centered", initial_sidebar_state="collapsed")
inject_katex()
check_password()
init_db()

st.title("🔍 错题网络")

# ── Collapsible filter panel ──
with st.expander("🔎 筛选条件", expanded=True):
    sources = get_sources()
    source_map = {s["name"]: s["id"] for s in sources}

    f1, f2 = st.columns(2)
    with f1:
        source_filter = st.selectbox(
            "来源", options=["全部"] + list(source_map.keys()), key="f_source"
        )
        module_filter = st.selectbox(
            "学科", options=["全部", "高等数学", "线性代数", "概率统计"], key="f_module"
        )
        chapters = get_chapters()
        chapter_options = {c["name"]: c["name"] for c in chapters}
        chapter_filter = st.selectbox(
            "章节", options=["全部"] + list(chapter_options.keys()), key="f_chapter"
        )
    with f2:
        error_type_filter = st.selectbox(
            "错误类型",
            options=["全部", "概念模糊", "计算失误", "经典套路未识别", "条件漏看", "其他"],
            key="f_error"
        )
        status_filter = st.selectbox(
            "状态", options=["全部", "未掌握", "模糊", "已吃透"], key="f_status"
        )
        keyword = st.text_input("🔎 全文搜索", key="f_keyword",
                                placeholder="题干/知识点/彻悟")

# ── Results ──
src_id = source_map.get(source_filter) if source_filter != "全部" else None
mod = module_filter if module_filter != "全部" else None
ch = chapter_filter if chapter_filter != "全部" else None
et = error_type_filter if error_type_filter != "全部" else None
st_ = status_filter if status_filter != "全部" else None
kw = keyword if keyword else None

results = search_problems(
    source_id=src_id, module=mod, chapter=ch,
    error_type=et, status=st_, keyword=kw
)

st.markdown(f"**找到 {len(results)} 道错题**")

if not results:
    st.info("没有匹配的错题，去录入几道吧！")
else:
    for prob in results:
        prob = dict(prob)
        # Build summary line for expander title
        qt = (prob["question_text"] or "").strip()
        summary = qt[:50] if qt else (f"[图片] {prob['chapter']}")
        if len(qt) > 50:
            summary += "…"

        with st.expander(
            f"[{prob['module']}] {summary}",
            expanded=False
        ):
            tab1, tab2 = st.tabs(["查看", "编辑"])
            with tab1:
                render_problem_detail(prob, show_solution=True)
                st.caption(f"复习次数: {prob['review_count']}  |  "
                          f"下次复习: {prob['next_review_date']}  |  "
                          f"阶段: {prob['review_stage']}")

            with tab2:
                st.markdown("#### 编辑错题")
                new_module = st.selectbox(
                    "学科", options=["高等数学", "线性代数", "概率统计"],
                    index=["高等数学", "线性代数", "概率统计"].index(prob["module"]),
                    key=f"em_{prob['id']}"
                )
                edit_chapter_options = list(chapter_options.keys())
                # Ensure the current chapter appears in the selectbox
                if prob["chapter"] and prob["chapter"] not in edit_chapter_options:
                    edit_chapter_options = [prob["chapter"]] + edit_chapter_options
                edit_chapter_idx = (edit_chapter_options.index(prob["chapter"])
                                    if prob["chapter"] in edit_chapter_options else 0)
                new_chapter = st.selectbox(
                    "章节", options=edit_chapter_options,
                    index=edit_chapter_idx,
                    key=f"ec_{prob['id']}"
                )
                src_names = list(source_map.keys())
                default_src_idx = src_names.index(prob["source_name"]) if prob["source_name"] in src_names else 0
                new_source_name = st.selectbox(
                    "来源", options=src_names,
                    index=default_src_idx,
                    key=f"es_{prob['id']}"
                )
                new_error_type = st.selectbox(
                    "错误类型",
                    options=["概念模糊", "计算失误", "经典套路未识别", "条件漏看", "其他"],
                    index=["概念模糊", "计算失误", "经典套路未识别", "条件漏看", "其他"].index(
                        prob["error_type"]
                    ),
                    key=f"ee_{prob['id']}"
                )
                new_status = st.selectbox(
                    "状态", options=["未掌握", "模糊", "已吃透"],
                    index=["未掌握", "模糊", "已吃透"].index(prob["status"]),
                    key=f"est_{prob['id']}"
                )
                new_difficulty = st.slider(
                    "难度", 1, 5, prob["difficulty"], key=f"ed_{prob['id']}"
                )
                new_insight = st.text_input(
                    "关键彻悟", value=prob.get("key_insight", ""), key=f"ei_{prob['id']}"
                )
                new_kp = st.text_input(
                    "核心知识点", value=prob.get("core_knowledge_points", ""),
                    key=f"ekp_{prob['id']}"
                )

                c_edit, c_del = st.columns(2)
                with c_edit:
                    if st.button("💾 保存修改", key=f"save_{prob['id']}",
                                use_container_width=True):
                        update_problem(prob["id"], {
                            "module": new_module,
                            "chapter": new_chapter,
                            "source_id": source_map.get(new_source_name, prob["source_id"]),
                            "error_type": new_error_type,
                            "status": new_status,
                            "difficulty": new_difficulty,
                            "key_insight": new_insight,
                            "core_knowledge_points": new_kp,
                        })
                        st.success("已保存")
                        st.rerun()
                with c_del:
                    if st.button("🗑️ 删除", key=f"del_{prob['id']}",
                                use_container_width=True):
                        delete_problem(prob["id"])
                        st.success("已删除")
                        st.rerun()
