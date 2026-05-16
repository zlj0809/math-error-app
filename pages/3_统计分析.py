"""统计分析 — 薄弱点可视化"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import init_db, get_conn
from utils import check_password

st.set_page_config(page_title="统计分析", page_icon="📊",
                   layout="centered", initial_sidebar_state="collapsed")
init_db()
check_password()

st.title("📊 统计分析")

conn = get_conn()

# ── Load data ──
problems = conn.execute("""
    SELECT p.*, s.name as source_name
    FROM problems p LEFT JOIN sources s ON p.source_id = s.id
""").fetchall()
conn.close()

if not problems:
    st.info("还没有错题数据，去录入几道吧！")
    st.stop()

df = pd.DataFrame([dict(p) for p in problems])

# ── Row 1: Error type + Status ──
c1, c2 = st.columns(2)

with c1:
    st.markdown("### 错误类型分布")
    err_counts = df["error_type"].value_counts().reset_index()
    err_counts.columns = ["错误类型", "数量"]
    fig = px.pie(err_counts, values="数量", names="错误类型", hole=0.4)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("### 掌握状态")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["状态", "数量"]
    status_colors = {"未掌握": "#ff6b6b", "模糊": "#ffd93d", "已吃透": "#6bcb77"}
    fig = px.bar(
        status_counts, x="状态", y="数量", color="状态",
        color_discrete_map=status_colors, text="数量"
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Chapter breakdown ──
st.markdown("### 各章节错题分布")
ch_counts = df.groupby(["module", "chapter"]).size().reset_index(name="数量")
ch_counts = ch_counts.sort_values("数量", ascending=False)

fig = px.bar(
    ch_counts.head(20), y="chapter", x="数量", color="module",
    orientation="h", text="数量",
    title="错题最多的章节 (Top 20)"
)
fig.update_layout(yaxis=dict(categoryorder="total ascending"))
st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Knowledge points ranking ──
st.markdown("### 薄弱知识点排行")
kp_counter = {}
for kps in df["core_knowledge_points"].dropna():
    for kp in kps.split(","):
        kp = kp.strip()
        if kp:
            kp_counter[kp] = kp_counter.get(kp, 0) + 1

if kp_counter:
    kp_df = pd.DataFrame(
        sorted(kp_counter.items(), key=lambda x: x[1], reverse=True)[:15],
        columns=["知识点", "出现次数"]
    )
    fig = px.bar(kp_df, x="出现次数", y="知识点", orientation="h", text="出现次数")
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("暂无知识点数据")

# ── Row 4: Review calendar ──
st.markdown("### 复习日历")
df["next_review_date"] = pd.to_datetime(df["next_review_date"])
today = pd.Timestamp(datetime.now().date())
week_later = today + timedelta(days=7)
due_soon = df[(df["next_review_date"] >= today) & (df["next_review_date"] <= week_later)]

if not due_soon.empty:
    day_counts = due_soon.groupby(due_soon["next_review_date"].dt.date).size()
    day_counts = day_counts.reset_index()
    day_counts.columns = ["日期", "待复习数"]

    fig = go.Figure(data=go.Bar(
        x=day_counts["日期"], y=day_counts["待复习数"],
        text=day_counts["待复习数"], textposition="outside",
        marker_color="#ff6b6b"
    ))
    fig.update_layout(
        title="未来 7 天待复习错题",
        xaxis_title="", yaxis_title="数量",
        xaxis=dict(tickformat="%m-%d")
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("未来 7 天暂无待复习错题 🎉")

# ── Summary metrics ──
st.markdown("---")
st.markdown("### 总览")
cm1, cm2, cm3, cm4 = st.columns(4)
cm1.metric("学科覆盖", df["module"].nunique())
cm2.metric("章节覆盖", df["chapter"].nunique())
cm3.metric("平均难度", f"{df['difficulty'].mean():.1f}")
cm4.metric("平均复习次数", f"{df['review_count'].mean():.1f}")
