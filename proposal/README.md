# 11/5 提案草稿（ACL 格式）

生成日期 2026-11-03。文件：

| 文件 | 说明 |
|---|---|
| `proposal.pdf` | 编译好的 PDF：正文 2 页整 + 参考文献第 3 页（14 条） |
| `proposal.tex` | 正文，`\usepackage[final]{acl}`（显示作者，不带行号） |
| `proposal.bib` | 参考文献，每条都核过来源（见下） |
| `acl.sty`, `acl_natbib.bst` | 官方 ACL 模板文件，取自 github.com/acl-org/acl-style-files @ d5adc82（2026-06-29）；直接和 tex/bib 一起上传 Overleaf 即可 |
| `build.sh` | 一键编译：`bash build.sh`（需要 pdflatex + bibtex，本机 TeX Live 2022） |

## 提交前必须改的地方

1. **作者行**：`proposal.tex` 第 14–16 行是占位符 `Team Member 1 … 4` 和 `{member1,…}@gatech.edu`，换成真实姓名和邮箱。
2. **页数口径**：队友讨论稿写的是"two-page ACL-format document with at least five team-verified citations"。现在正文正好 2 页，参考文献溢到第 3 页。ACL 惯例参考文献不计页数；如果老师要求连参考文献一起 2 页，把 bib 砍到 6–7 条（保留 lu2026survey、lin2025fdb15、wang2026humdial、defossez2024moshi、lee2025behaviorsd、zhong2026iraf、veigel2026conformbench），再从第 1 节删掉对应的句子即可。
3. **Plan B 一段**：如果团队最终不想在提案里露出备选题，直接删第 7 节最后一段，正文会空出约 12 行，可以把第 4 节的 Conditions 和第 5 节的 Slurm 状态补回去。

## 引用核对记录（"team-verified citations" 的依据）

| bib key | 核对方式（2026-11-03） |
|---|---|
| defossez2024moshi, roy2026personaplex, lin2025fdb15, wang2026humdial, xiong2026msibench, lu2026survey, zhong2026iraf, chen2025fireredchat, ohashi2026alignment, antgroup2026venus | arXiv API 按编号拉取，标题和作者与 API 返回一致 |
| lee2025behaviorsd | HF 数据卡 `yhytoto12/behavior-sd` 自带 bibtex：NAACL 2025，aclanthology 2025.naacl-long.484 |
| veigel2026conformbench | ACL Anthology EMNLP 2026 main 卷目录，ID 2026.emnlp-main.2137 |
| xie2022correctable | ACL Anthology 官方 bib：2022.emnlp-main.56，pp. 876–889 |
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
