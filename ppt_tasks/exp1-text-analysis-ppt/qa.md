# QA 与验收记录 — exp1-text-analysis-ppt（final2）

## 渲染与结构检查

| 检查 | 命令 / 工具 | 结果 |
|---|---|---|
| 渲染路径 | `render_pptx.ps1`（PowerPoint COM） | PPTX → PDF + 14 张 PNG（1280×720） |
| 结构检查 | `inspect_pptx.py --pretty` | 14 页；13.333 × 7.5 in（16:9）；shape 正常 |
| 科学基线 | `check_scientific_baseline.py --expected-slides 14` | **FAILURES: 0**（小于 12pt 的项均为图注/页脚/表内元数据） |
| 逐页 PNG 审阅 | LLM 直接查看 final2/slide01–14.png | 通过（见下表） |

## 验收契约逐条结果

| ID | 要求 | 结果 | 证据 |
|---|---|---|---|
| R1 | 16:9、14 页、页码连续 | PASS | 封面不编号，内容页 2–14 连续；inspect_pptx 14 页 |
| R2 | 白底深蓝学术风、全篇一致 | PASS | 全篇 #FFFFFF 底、#1E3A5F 标题、#E8A838 仅作强调 |
| R3 | 首页含题目、副标题、组员与分工占位 | PASS | slide01：组员 A/B/C 分工 + 学号/班级/指导教师占位 |
| R4 | 数据质量三大发现 | PASS | slide03：3.6 伪值 27.45%、2009-07 前无评分、店均 3 条 |
| R5 | 标签口径 A/B 与好评率定义 | PASS | slide04 口径说明；slide09 A/B 对照；slide11 好评率定义 |
| R6 | 关键结果数字可见 | PASS | slide07 大号 0.9403；slide09 对比条 0.9395 / 0.7522（13pt） |
| R7 | 词云、Top10、周趋势、雷达、单店图清晰 | PASS | slide10–13 原图完整，无裁切拉伸；图注可读 |
| R8 | 正文 ≥12pt（图注 ≥9pt） | PASS | 正文 12pt；表内 10–11pt、图注 9pt、页脚 8pt 属元数据 |
| R9 | 中文无乱码/缺字 | PASS | 全部页面中文正常，eastAsia 统一 Microsoft YaHei |
| R10 | 无溢出/重叠/遮挡 | PASS | 逐页检查边缘、页脚与图注间距 |
| R11 | 结论页含结论、不足、分工 | PASS | slide14 |
| R12 | 页型有节奏 | PASS | 封面/KPI/三卡/左表右图/流程/大图/双图/结论共 8 种页型 |

## 视觉迭代记录

| 版本 | 问题 | 修订 |
|---|---|---|
| v1 | slide02 KPI “8 列 / 1.9 GB” 换行遮挡标签 | 改为 “1.9 GB / 主数据 · 8 列” |
| v1 | slide06、slide09 下半区欠填充 | 增加指标卡（480,000 / 120,000 / 50,000）与 A/B accuracy 对比条 |
| v1 | slide10 词云偏小、下方留白大 | 放大三张词云 + 增加好评/差评 Top10 词表 |
| v1 | slide13 好评率小图不可读 | 改为 “0.944” 数字卡 + 全站 88.62% 对照 |
| v2 | slide08 第三条推理引号换行 | 精简文案；step 列表与结论页字号提到 12pt |
| v3/final | 结论页 “2009 年前” 与正文口径不一致 | 统一为 “2009-07 前” |

## 交付物

- `exp1-text-analysis-v1.pptx`（14 页，Build Mode 生成，PPT 内文字/形状/表格可编辑）
- `renders/final2/`：PDF + 14 张 PNG（审阅证据）
- `build.py`：可复现脚本（`C:\mlenv\Scripts\python.exe build.py`）
- `resolved-theme-v1.json` + `manifest.json`：主题版本、包版本、SHA-256（d33230c7…）
