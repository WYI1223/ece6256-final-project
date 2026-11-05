# 11/5 提案草稿（ACL 格式）

生成日期 2026-11-03。文件：

| 文件 | 说明 |
|---|---|
| `proposal.pdf` | 编译好的 PDF。**注意：11/4–11/5 的修改（见下）之后尚未重新编译，提交前必须重跑 `build.sh` 并确认正文仍在 2 页内** |
| `proposal.tex` | 正文，`\usepackage[final]{acl}`（显示作者，不带行号） |
| `proposal.bib` | 参考文献，每条都核过来源（见下） |
| `acl.sty`, `acl_natbib.bst` | 官方 ACL 模板文件，取自 github.com/acl-org/acl-style-files @ d5adc82（2026-06-29）；直接和 tex/bib 一起上传 Overleaf 即可 |
| `build.sh` | 一键编译：`bash build.sh`（需要 pdflatex + bibtex，本机 TeX Live 2022） |

## 提交前必须改的地方

1. **作者行**：已填全（Zimo Fan, Ruihuan Gao, Ruize Sun, Weiyi Sun，按姓氏字母序；zfan321 / rgao302 / rsun98 / wsun377@gatech.edu）。顺序或署名要调整直接改 `proposal.tex` 第 14 行。
2. **页数口径**：作业要求 "2 pages in ACL format, plus references"，参考文献不计页数。11/4 的修改让正文比原稿多约 40 词，编译后若溢出到第 3 页，可删：第 3 节 G0 的 "It ports pVAD/IRAF to an open model"、第 7 节风险 (2)、第 1 节 Kyutai 一句。
3. **分工未写人名**：第 6 节 "One member each on …" 需要换成具体姓名（作业必填项 Division of labor）。
4. **真人录音集 (iv)**：若录音者不全是组员，按 Human subjects 政策需在提案截止前得到老师批准；若只用组员，在第 4 节注明。

## 11/4–11/5 修改记录（对照作业要求）

- 标题区加 "Anchored in"（Unit 6 L18–L21；Unit 7 L22–L23）。
- 新增多轮测试集 (v) 及 per-session 指标；时间表补入。
- 新增两条针对 side-talk 的基线门控：呼语规则、ASR + 本地 LLM 受话人分类器。
- H2 改为"side-talk onset rate 至少减半"，主指标名称全文统一。
- 摘要 "three 2026 benchmarks" → "three recent benchmarks"（FDB v1.5 是 2025 年）。
- 第 5 节补 FDB 单一 TTS 用户声音的混杂（voice-matched AUC 0.61）。
- 第 6 节补算力估算（≈150 L40S-h 推理、≈60 H100-h LoRA、≈\$150 API）。
- 删除 Plan B（ConFormBench）一段；fallback 改为覆盖全部非 LoRA 条件和五个测试集。
- 补 6 条引用（见下表）。

## 引用核对记录（"team-verified citations" 的依据）

| bib key | 核对方式（2026-11-03） |
|---|---|
| defossez2024moshi, roy2026personaplex, lin2025fdb15, wang2026humdial, xiong2026msibench, lu2026survey, zhong2026iraf, chen2025fireredchat, ohashi2026alignment, antgroup2026venus | arXiv API 按编号拉取，标题和作者与 API 返回一致 |
| lee2025behaviorsd | HF 数据卡 `yhytoto12/behavior-sd` 自带 bibtex：NAACL 2025，aclanthology 2025.naacl-long.484 |
| veigel2026conformbench（已不在正文引用） | ACL Anthology EMNLP 2026 main 卷目录，ID 2026.emnlp-main.2137 |
| xie2022correctable（已不在正文引用） | ACL Anthology 官方 bib：2022.emnlp-main.56，pp. 876–889 |
| wang2024freezeomni, desplanques2020ecapa, ding2019pvad, openai2024gpt4o | arxiv.org/abs 页面 citation meta（2026-11-04），标题与作者一致 |
| panayotov2015librispeech | Crossref DOI 10.1109/ICASSP.2015.7178964，pp. 5206–5210 |
| resemble2025chatterbox | github.com/resemble-ai/chatterbox 可访问（2026-11-04）；年份 2025 未核实 |
| google2026gemini38live | ai.google.dev 模型页：proactive audio "permanently enabled"；capabilities 页原话 "can proactively decide not to respond if the content is not relevant"（2026-11-03 访问） |

正文里引用的数字来源：FDB v1.5 的 respond 率（GPT-4o .91、Freeze-Omni .58、Moshi .20 + .59 unknown）和"must strengthen addressee detection"出自 2507.23159；"models often respond even when no one addressed them"出自 MSI-Bench 2609.24812；"not shown solved"出自综述 2606.19453；Realtime-Venus 88% 出自 2609.13814。这些是提案调研时从论文正文摘的，建议组内再各自翻一遍原文确认。

## 正文结构（对应队友讨论稿的格式）

1. Problem and gap：三个 2026 评测只测不治；闭源已交付无论文；开源方案全是说话人身份门控；FDB v1.5 的两格（不同声音 vs 同声音）说明身份门控只能解一半。
2. RQ1–RQ3 + H1–H3：身份门控能解哪一格；LoRA 能否在同声音 side-talk 下保持话轮（≥20 点下降、≤5 点误伤）；学到的是词汇线索还是声学线索。
3. Proposed system：Moshiko-7B LoRA；G0 身份门控（无训练）；Behavior-SD + LLM 插话 + Chatterbox 声音克隆 + 三种声学条件的数据管线。
4. Experimental design：四个测试集（FDB v1.5、HumDial、自建去捷径集、小规模真人录音）；六个条件；指标；主估计量与配对 bootstrap。
5. Pilot evidence：11/2 本机 pilot 的表（身份门控放过 88–92% 同声音 side-talk）和两个捷径（99/100 呼语开头、远场/近场分离）。
6. Plan, roles and feasibility：周计划、四人分工、算力。
7. Risks and fallback：四条风险；LoRA 失败时的测量论文退路；Plan B（ConFormBench 证据溯源版，含补跑数据）。
