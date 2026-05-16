# 考研数学错题归纳

Streamlit Web 应用，用于考研数学错题拍照录入、盲盒复习、多维检索。

## 运行

```bash
streamlit run app.py
```

## 技术栈

- Python Streamlit (UI)
- SQLite (数据存储 `data/math_errors.db`)
- KaTeX (数学公式渲染)
- Plotly (图表)

## 核心功能

1. **录入** — 拍照上传题干和正解，引导式填表（来源→学科→章节→错误类型→知识点→彻悟）
2. **错题网络** — 来源/学科/章节/错误类型/状态 五维筛选
3. **盲盒复习** — 遗忘曲线驱动的随机抽题，先出题干后揭晓答案
4. **统计分析** — 薄弱知识点排行、错误类型分布

## 数据结构

- `sources` — 练习册来源
- `problems` — 错题主表（question_image + solution_image 为主，文字可选）
- `reviews` — 复习记录

移动端已适配（centered layout + collapsed sidebar）。
