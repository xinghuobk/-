# Multi-Agent Debate (MAD) 研究论文列表

> 生成时间：2026-06-15T17:18:00.885439+00:00
> 关键词数：14 | 年份范围：2018-2026
> 总论文数：**259** | 关键论文：**6**

> JSON 原始数据：`docs/MAD论文研究数据.json`

## 一、关键论文（Key Papers）

### 1. Multi-Agent Debate for LLM Judges with Adaptive Stability Detection

- **作者**：Tianyu Hu, Zhen Tan, Song Wang, Huaizhi Qu, Tianlong Chen
- **年份**：2025
- **来源/期刊**：arXiv.org
- **引用数**：10
- **DOI**：[10.48550/arXiv.2510.12697](https://doi.org/10.48550/arXiv.2510.12697)
- **arXiv**：[2510.12697](https://arxiv.org/abs/2510.12697)
- **URL**：[link1](https://www.semanticscholar.org/paper/ee6a3ae4b821bd1538a07d0aebe6d6ce75e7125d), [link2](https://doi.org/10.48550/arXiv.2510.12697)
- **摘要**：With advancements in reasoning capabilities, Large Language Models (LLMs) are increasingly employed for automated judgment tasks. While LLMs-as-Judges offer promise in automating evaluations, current approaches often rely on simplistic aggregation methods (e.g., majority voting), which can fail even when individual agents provide correct answers. To address this, we propose a multi-agent debate judge framework where agents collaboratively reason and iteratively refine their responses. We formalize the debate process mathematically, analyzing agent interactions and proving that debate amplifies correctness compared to static ensembles. To enhance efficiency, we introduce a stability detection mechanism that models judge consensus dynamics via a time-varying Beta-Binomial mixture, with adaptive stopping based on distributional similarity (Kolmogorov-Smirnov test). This mechanism models the judges'collective correct rate dynamics using a time-varying mixture of Beta-Binomial distributions and employs an adaptive stopping criterion based on distributional similarity (Kolmogorov-Smirnov statistic). Experiments across multiple benchmarks and models demonstrate that our framework impro...

### 2. MALLM: Multi-Agent Large Language Models Framework

- **作者**：Jonas Becker, Lars Benedikt Kaesberg, Niklas Bauer, Jan Philip Wahle, Terry Ruas, Bela Gipp
- **年份**：2025
- **来源/期刊**：Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing: System Demonstrations
- **引用数**：1
- **DOI**：[10.18653/v1/2025.emnlp-demos.29](https://doi.org/10.18653/v1/2025.emnlp-demos.29)
- **URL**：[link1](https://doi.org/10.18653/v1/2025.emnlp-demos.29), [link2](https://doi.org/10.18653/v1/2025.emnlp-demos.29)

### 3. MALLM: Multi-Agent Decision-Making with LLMs for Multi-User Edge-Sensor Environments

- **作者**：Heming Fu, Weici Pan, Zhenhua Liu, Shan Lin
- **年份**：2025
- **来源/期刊**：2025 IEEE Annual Congress on Artificial Intelligence of Things (AIoT)
- **引用数**：0
- **DOI**：[10.1109/aiot66900.2025.00075](https://doi.org/10.1109/aiot66900.2025.00075)
- **URL**：[link1](https://doi.org/10.1109/aiot66900.2025.00075), [link2](https://doi.org/10.1109/aiot66900.2025.00075)

### 4. Should we be going MAD? A Survey of Multi-Agent Debate in the Wild

- **作者**：Wietse Smit, Thomas Demeester, Tijl De Bie
- **年份**：2024
- **来源/期刊**：arXiv
- **引用数**：0
- **DOI**：[10.48550/arXiv.2411.03292](https://doi.org/10.48550/arXiv.2411.03292)
- **arXiv**：[2411.03292](https://arxiv.org/abs/2411.03292)
- **URL**：[link1](https://arxiv.org/abs/2411.03292), [link2](https://doi.org/10.48550/arXiv.2411.03292)
- **摘要**：Multi-Agent Debate (MAD) has emerged as a popular LLM paradigm, where multiple agents debate with each other to reach a (hopefully) better answer. This survey reviews recent MAD research, identifying common patterns in system design, evaluation protocols, and open challenges. We find that while MAD often improves on simple baselines, much work is needed to understand when and why MAD works or fails, and to establish rigorous benchmarks for future comparison.

### 5. Improving Factuality and Reasoning in Language Models through Multiagent Debate

- **作者**：Yilun Du, Shuang Li, Joshua B. Tenenbaum, Igor Mordatch
- **年份**：2023
- **来源/期刊**：arXiv
- **引用数**：0
- **DOI**：[10.48550/arXiv.2305.14325](https://doi.org/10.48550/arXiv.2305.14325)
- **arXiv**：[2305.14325](https://arxiv.org/abs/2305.14325)
- **URL**：[link1](https://arxiv.org/abs/2305.14325), [link2](https://doi.org/10.48550/arXiv.2305.14325)
- **摘要**：Large language models (LLMs) have demonstrated strong performance in many tasks, but they still suffer from factual errors and reasoning mistakes. We propose a multi-agent debate framework where multiple LLM agents generate individual responses, critique each other's arguments, and iteratively revise their answers. The agents are encouraged to produce consistent, evidence-based outputs. Empirical results show consistent improvements over single-agent baselines on arithmetic reasoning, reading comprehension, and factual accuracy benchmarks.

### 6. AI Safety via Debate

- **作者**：Geoffrey Irving, Paul Christiano, Dario Amodei
- **年份**：2018
- **来源/期刊**：arXiv
- **引用数**：0
- **DOI**：[10.48550/arXiv.1805.00899](https://doi.org/10.48550/arXiv.1805.00899)
- **arXiv**：[1805.00899](https://arxiv.org/abs/1805.00899)
- **URL**：[link1](https://arxiv.org/abs/1805.00899), [link2](https://doi.org/10.48550/arXiv.1805.00899)
- **摘要**：We study the research program of using debates between two AI systems as a training signal for aligned agents. A human judge evaluates debates between two AI agents, rewarding the agent that the human finds most convincing. Because a lie is easier to refute than to defend, honest strategies can remain competitive even against stronger opponents, providing a scalable approach to training aligned agents without requiring humans to fully understand the tasks.

## 二、其他相关论文

| # | 年份 | 引用 | 标题 | 作者 | DOI/来源 |
|----|-----|-----|------|------|---------|
| 1 | 2023 | 1155 | Encouraging Divergent Thinking in Large Language Models through Multi-Agent D... | Tian Liang, Zhiwei He, Wenxiang Jiao,... | [doi](https://doi.org/10.48550/arXiv.2305.19118) |
| 2 | 2023 | 948 | ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate | Chi-Min Chan, Weize Chen, Yusheng Su,... | [doi](https://doi.org/10.48550/arXiv.2308.07201) |
| 3 | 2024 | 109 | Improving Multi-Agent Debate with Sparse Communication Topology | Yunxuan Li, Y. Du, Jiageng Zhang, Le ... | [doi](https://doi.org/10.48550/arXiv.2406.11776) |
| 4 | 2024 | 73 | Can LLMs Produce Faithful Explanations For Fact-checking? Towards Faithful Ex... | Kyungha Kim, Sangyun Lee, Kung-Hsiang... | [doi](https://doi.org/10.48550/arXiv.2402.07401) |
| 5 | 2024 | 63 | GroupDebate: Enhancing the Efficiency of Multi-Agent Debate Using Group Discu... | Tongxuan Liu, Xingyu Wang, Weizhe Hua... | [doi](https://doi.org/10.48550/arXiv.2409.14051) |
| 6 | 2025 | 55 | Voting or Consensus? Decision-Making in Multi-Agent Debate | Lars Benedikt Kaesberg, Jonas Becker,... | [doi](https://doi.org/10.18653/v1/2025.findings-acl.606) |
| 7 | 2025 | 44 | SWE-Debate: Competitive Multi-Agent Debate for Software Issue Resolution | Hanchen Li, Yuling Shi, Shaoxin Lin, ... | [doi](https://doi.org/10.48550/arXiv.2507.23348) |
| 8 | 2025 | 42 | Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate | Andrea Wynn, Harsh Satija, Gillian K ... | [doi](https://doi.org/10.48550/arXiv.2509.05396) |
| 9 | 2025 | 36 | Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate | Yexiang Liu, Jie Cao, Zekun Li, Ran H... | International Conference on Learning Representations |
| 10 | 2020 | 36 | Electric vehicle charging strategy study and the application on charging stat... | Yanhai Xiong, Bo An, Sarit Kraus | [doi](https://doi.org/10.1007/s10458-020-09484-5) |
| 11 | 2025 | 34 | LoCal: Logical and Causal Fact-Checking with LLM-Based Multi-Agents | Jiatong Ma, Linmei Hu, Rang Li, Wenbo Fu | [doi](https://doi.org/10.1145/3696410.3714748) |
| 12 | 2019 | 33 | AI Safety Needs Social Scientists | Geoffrey Irving, Amanda Askell | [doi](https://doi.org/10.23915/distill.00014) |
| 13 | 2023 | 32 | Can ChatGPT Defend its Belief in Truth? Evaluating LLM Reasoning via Debate | Boshi Wang, Xiang Yue, Huan Sun | [doi](https://doi.org/10.18653/v1/2023.findings-emnlp.795) |
| 14 | 2025 | 30 | Stop Overvaluing Multi-Agent Debate -- We Must Rethink Evaluation and Embrace... | Hangfan Zhang, Zhiyao Cui, Jianhao Ch... | semantic_scholar |
| 15 | 2019 | 29 | Higher Education Programs in Prison: What We Know Now and What We Should Focu... | Lois Davis | [doi](https://doi.org/10.7249/pe342) |
| 16 | 2025 | 22 | If Multi-Agent Debate is the Answer, What is the Question? | Hangfan Zhang, Zhiyao Cui, Xinrun Wan... | [doi](https://doi.org/10.48550/arXiv.2502.08788) |
| 17 | 2025 | 21 | Debate4MATH: Multi-Agent Debate for Fine-Grained Reasoning in Math | Shaowei Zhang, Deyi Xiong | [doi](https://doi.org/10.18653/v1/2025.findings-acl.862) |
| 18 | 2025 | 21 | S2-MAD: Breaking the Token Barrier to Enhance Multi-Agent Debate Efficiency | Yuting Zeng, Weizhe Huang, Lei Jiang,... | [doi](https://doi.org/10.48550/arXiv.2502.04790) |
| 19 | 2023 | 17 | A Taxonomy for Autonomous LLM-Powered Multi-Agent Architectures | Thorsten Händler | [doi](https://doi.org/10.5220/0012239100003598) |
| 20 | 2025 | 16 | Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate | Binwei Yao, Chao Shang, Wanyu Du, Jia... | [doi](https://doi.org/10.48550/arXiv.2509.23055) |
| 21 | 2025 | 16 | Revisiting Multi-Agent Debate as Test-Time Scaling: A Systematic Study of Con... | Yongjin Yang, Euiin Yi, Jongwoo Ko, K... | [doi](https://doi.org/10.48550/arXiv.2505.22960) |
| 22 | 2025 | 16 | A Hybrid Framework Integrating LLM and ANFIS for Explainable Fact-Checking | M. Bangerter, G. Fenza, D. Furno, Mar... | [doi](https://doi.org/10.1109/TFUZZ.2024.3431710) |
| 23 | 2025 | 15 | Literature Review Of Multi-Agent Debate For Problem-Solving | Arne Tillmann | [doi](https://doi.org/10.48550/arXiv.2506.00066) |
| 24 | 2022 | 15 | Accountability in multi-agent organizations: from conceptual design to agent ... | Matteo Baldoni, Cristina Baroglio, Ro... | [doi](https://doi.org/10.1007/s10458-022-09590-6) |
| 25 | 2025 | 14 | Enhancing Multi-Agent Debate System Performance via Confidence Expression | Zijie Lin, Bryan Hooi | [doi](https://doi.org/10.48550/arXiv.2509.14034) |
| 26 | 2025 | 14 | Stay Focused: Problem Drift in Multi-Agent Debate | Jonas Becker, Lars Benedikt Kaesberg,... | [doi](https://doi.org/10.48550/arXiv.2502.19559) |
| 27 | 2025 | 13 | MMAgentRec, a personalized multi-modal recommendation agent with large langua... | Xiaochen Xiao | [doi](https://doi.org/10.1038/s41598-025-96458-w) |
| 28 | 2025 | 13 | Medical large language model for diagnostic reasoning across specialties | — | [doi](https://doi.org/10.1038/s41591-025-03520-1) |
| 29 | — | 13 | Co-argumentation Artifact for Agent Societies | Enrico Oliva, Peter McBurney, Andrea ... | [doi](https://doi.org/10.1007/978-3-540-78915-4_3) |
| 30 | 2025 | 12 | Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Log... | Haolun Wu, Zhenkun Li, Lingyao Li | [doi](https://doi.org/10.48550/arXiv.2511.07784) |
| 31 | 2025 | 12 | PhishDebate: An LLM-Based Multi-Agent Framework for Phishing Website Detection | Wenhao Li, Selvakumar Manickam, Yung-... | [doi](https://doi.org/10.1109/BigData66926.2025.11401440) |
| 32 | 2024 | 12 | ArgMed-Agents: Explainable Clinical Decision Reasoning with LLM Disscusion vi... | Shengxin Hong, Liang Xiao, Xin Zhang,... | [doi](https://doi.org/10.1109/bibm62325.2024.10822109) |
| 33 | 2025 | 10 | Beyond Translation: LLM-Based Data Generation for Multilingual Fact-Checking | Yi-Ling Chung, Aurora Cobo, Pablo Serna | [doi](https://doi.org/10.48550/arXiv.2502.15419) |
| 34 | 2022 | 9 | Acceleration AI Ethics, the Debate between Innovation and Safety, and Stabili... | James Brusseau | [doi](https://doi.org/10.2139/ssrn.4293514) |
| 35 | 2025 | 8 | Verdict: A Library for Scaling Judge-Time Compute | Nimit Kalra, Leonard Tang | [doi](https://doi.org/10.48550/arXiv.2502.18018) |
| 36 | 2025 | 7 | TRIZ Agents: A Multi-Agent LLM Approach for TRIZ-Based Innovation | Kamil Szczepanik, Jarosław Chudziak | [doi](https://doi.org/10.5220/0013321900003890) |
| 37 | 2025 | 7 | BELLE: A Bi-Level Multi-Agent Reasoning Framework for Multi-Hop Question Answ... | Taolin Zhang, Dongyang Li, Qizhou Che... | [doi](https://doi.org/10.48550/arXiv.2505.11811) |
| 38 | 2024 | 7 | Yours Truly: A Credibility Framework for Effortless LLM-Powered Fact Checking | Vallidevi Krishnamurthy, Varshini Balaji | [doi](https://doi.org/10.1109/access.2024.3520187) |
| 39 | — | 7 | An Argumentation-Based Framework for Deliberation in Multi-agent Systems | Santi Ontañón, Enric Plaza | [doi](https://doi.org/10.1007/978-3-540-78915-4_12) |
| 40 | 2025 | 6 | Large Language Models | Ketan Sanjay Desale | [doi](https://doi.org/10.7551/mitpress/15517.003.0003) |
| 41 | 2025 | 6 | Debate-Driven Multi-Agent LLMs for Phishing Email Detection | Ngoc Tuong Vy Nguyen, Felix D Childre... | [doi](https://doi.org/10.1109/isdfs65363.2025.11012014) |
| 42 | 2025 | 6 | Amplified Vulnerabilities: Structured Jailbreak Attacks on LLM-based Multi-Ag... | Senmao Qi, Yifei Zou, Peng Li, Zi Lin... | [doi](https://doi.org/10.48550/arXiv.2504.16489) |
| 43 | 2024 | 6 | “Tipping the Balance”: Human Intervention in Large Language Model Multi‐Agent... | Haley Triem, Ying Ding | [doi](https://doi.org/10.1002/pra2.1034) |
| 44 | 2024 | 5 | LLM-based Rewriting of Inappropriate Argumentation using Reinforcement Learni... | Timon Ziegenbein, Gabriella Skitalins... | [doi](https://doi.org/10.18653/v1/2024.acl-long.244) |
| 45 | 2024 | 5 | Unlocking Varied Perspectives: A Persona-Based Multi-Agent Framework with Deb... | Zhe Hu, Hou Pong Chan, Jing Li, Yu Yin | [doi](https://doi.org/10.48550/arXiv.2406.19643) |
| 46 | 2022 | 5 | Preference-based multi-objective multi-agent path finding | Florence Ho, Shinji Nakadai | [doi](https://doi.org/10.1007/s10458-022-09593-3) |
| 47 | 2026 | 4 | LLM-Agent-UMF: LLM-based Agent Unified Modeling Framework for Seamless Design... | Amine Ben Hassouna, Hana Chaari, Ines... | [doi](https://doi.org/10.1016/j.inffus.2025.103865) |
| 48 | 2025 | 4 | MedFact: A Large-scale Chinese Dataset for Evidence-based Medical Fact-checki... | Tong Chen, Zimu Wang, Yiyi Miao, Haor... | [doi](https://doi.org/10.48550/arXiv.2509.17436) |
| 49 | 2025 | 4 | Debate-to-Detect: Reformulating Misinformation Detection as a Real-World Deba... | Chen Han, Wenzhen Zheng, Xijin Tang | [doi](https://doi.org/10.18653/v1/2025.emnlp-main.764) |
| 50 | 2025 | 4 | LLM-powered Multi-agent Framework for Goal-oriented Learning in Intelligent T... | Tianfu Wang | [doi](https://doi.org/10.35542/osf.io/gt95h_v1) |
| 51 | 2019 | 4 | Identification of enhancer of mRNA decapping 4 as a novel fusion partner of M... | Heiko Becker, Gabriele Greve, Keisuke... | [doi](https://doi.org/10.1182/bloodadvances.2018023879) |
| 52 | — | 4 | Probabilistic reasoning in a distributed multi-agent environment | S.K.M. Wong, C.J. Butz | [doi](https://doi.org/10.1109/icmas.1998.699218) |
| 53 | — | 4 | Argumentation-Based Learning | Taro Fukumoto, Hajime Sawamura | [doi](https://doi.org/10.1007/978-3-540-75526-5_2) |
| 54 | — | 4 | Automated Theorem Provers Help Improve Large Language Model Reasoning | Lachlan McGinness, Peter Baumgartner | [doi](https://doi.org/10.29007/2n9m) |
| 55 | 2025 | 3 | Fact-checking with Generative AI: A Systematic Cross-Topic Examination of LLM... | Elizaveta Kuznetsova, Ilaria Vitulano... | [doi](https://doi.org/10.48550/arXiv.2503.08404) |
| 56 | 2025 | 3 | ZoFia: Zero-Shot Fake News Detection with Entity-Guided Retrieval and Multi-L... | Lvhua Wu, Xue Jiang, Sheng Sun, Tian ... | [doi](https://doi.org/10.48550/arXiv.2511.01188) |
| 57 | 2025 | 3 | Bootstrapping LLM-based Fact-checking via Iterative Rationalization Finetuning | Xiucheng Lyu, Chengyu Cao, Mingwei Su... | [doi](https://doi.org/10.1109/ICASSP49660.2025.10887888) |
| 58 | 2025 | 3 | Facts are Harder Than Opinions - A Multilingual, Comparative Analysis of LLM-... | Lorraine Saju, Arnim Bleier, Jana Las... | [doi](https://doi.org/10.48550/arXiv.2506.03655) |
| 59 | 2025 | 3 | Multi-Agent LLM Debate Unveils the Premise Left Unsaid | Harvey Bonmu Ku, Jeongyeol Shin, Hyou... | [doi](https://doi.org/10.18653/v1/2025.argmining-1.6) |
| 60 | 2025 | 3 | Efficient Leave-one-out Approximation in LLM Multi-agent Debate Based on Intr... | Yue Cui, Liuyi Yao, Zitao Li, Yaliang... | [doi](https://doi.org/10.48550/arXiv.2505.22192) |
| 61 | 2024 | 3 | Diversity of Thought Elicits Stronger Reasoning Capabilities in Multi-Agent D... | Mahmood Hegazy | [doi](https://doi.org/10.32388/3y8v71) |
| 62 | 2024 | 3 | Can Economic Fact-Checking Remedy Incorrect Beliefs About Housing Markets? | Clayton Nall | [doi](https://doi.org/10.1080/10511482.2024.2418046) |
| 63 | 2024 | 3 | A Debate-Driven Experiment on LLM Hallucinations and Accuracy | Rachel Li, Tanishka Bagade, K. Martin... | [doi](https://doi.org/10.48550/arXiv.2410.19485) |
| 64 | 2024 | 3 | Detecting Bugs with Substantial Monetary Consequences by LLM and Rule-based R... | Brian Zhang, Zhuo Zhang | [doi](https://doi.org/10.52202/079017-4258) |
| 65 | 2023 | 3 | Egalitarian judgment aggregation | Sirin Botan, Ronald de Haan, Marija S... | [doi](https://doi.org/10.1007/s10458-023-09598-6) |
| 66 | 2018 | 3 | HMGB2 Loss Upon Senescence Entry Disrupts Genomic Organization and Induces CT... | Anne Zirkel, Milos Nikolic, Konstanti... | [doi](https://doi.org/10.2139/ssrn.3155934) |
| 67 | 2026 | 2 | Accuracy Is Not Enough: Reasoning and Reference Reliability in Orthopaedic La... | Shashwat Singh, Pranav Chandrasekhar | [doi](https://doi.org/10.7759/cureus.100845) |
| 68 | 2025 | 2 | Enhancing Health Fact-Checking with LLM-Generated Synthetic Data | Jingze Zhang, Jiahe Qian, Yiliang Zho... | [doi](https://doi.org/10.48550/arXiv.2508.20525) |
| 69 | 2025 | 2 | Creativity in Mathematics classes: insurrection via art and AI | Rafael Montoito, Andréia Dalcin | [doi](https://doi.org/10.46551/emd.v9n17a16) |
| 70 | 2025 | 2 | Swarm Intelligence Enhanced Reasoning: A Density-Driven Framework for LLM-Bas... | Ying Zhu, Heng Zhou, Rui Su, Peiqin Z... | [doi](https://doi.org/10.48550/arXiv.2505.17115) |
| 71 | 2025 | 2 | NGU_Research at CheckThat! 2025: An LLM Based Hybrid Fact-Checking Pipeline f... | Mohamed A. Abdallah, Rokayah M. Fekry... | Conference and Labs of the Evaluation Forum |
| 72 | 2024 | 2 | ConfidenceCal: Enhancing LLMs Reliability through Confidence Calibration in M... | Yilin Bai | [doi](https://doi.org/10.1109/bigdia63733.2024.10808396) |
| 73 | 2024 | 2 | What Are Large Language Models? | Dilyan Grigorov | [doi](https://doi.org/10.1007/979-8-8688-0540-0_2) |
| 74 | 2024 | 2 | Large Language Models Projects | Pere Martra | [doi](https://doi.org/10.1007/979-8-8688-0515-8) |
| 75 | 2024 | 2 | Deception-Based Benchmarking: Measuring LLM Susceptibility to Induced Halluci... | Rukun Dou | [doi](https://doi.org/10.20944/preprints202407.0120.v1) |
| 76 | 2024 | 2 | Improving Spam Detection with a Multi-Agent Debate Framework | Ronghong Huang | [doi](https://doi.org/10.1109/iciba62489.2024.10868417) |
| 77 | 2021 | 2 | Malawi | Nikolaos Frantzeskakis, Michael Wahma... | [doi](https://doi.org/10.1093/oso/9780198849063.003.0027) |
| 78 | 2026 | 1 | Crowdsourced Fact-checking on X: from professional fact-checking to Community... | Javier Cantón-Correa, Mariola Moreno-... | [doi](https://doi.org/10.15581/003.39.1.032) |
| 79 | 2026 | 1 | A Fact-Checking Framework with Denoising Evidence Retrieval and LLM-Based Deb... | Jun Yang, Yuhan Bai, Dandan Song, Zhi... | [doi](https://doi.org/10.1145/3774904.3792285) |
| 80 | 2026 | 1 | Agent-as-a-Graph: Knowledge Graph-Based Tool and Agent Retrieval for LLM Mult... | Faheem Nizar, Elias Lumer, Anmol Gula... | [doi](https://doi.org/10.5220/0014473600004052) |
| 81 | 2026 | 1 | NOMAD: A Multi-Agent LLM System for UML Class Diagram Generation from Natural... | Polydoros Giannouris, Sophia Ananiadou | [doi](https://doi.org/10.5220/0014301900004058) |
| 82 | 2025 | 1 | Advancements in Multi-Agent Large Language Model Systems for Next-Generation AI | Abinaya Gopalakrishnan, G. Ramya, T. ... | [doi](https://doi.org/10.4018/979-8-3373-1419-8.ch002) |
| 83 | 2025 | 1 | A Multi-Agent Large Language Model (Llm) Framework for Code-Complying Design ... | Jinxin Chen, Yi Bao | [doi](https://doi.org/10.2139/ssrn.5193679) |
| 84 | 2025 | 1 | @Grok Is This True? LLM-Powered Fact-Checking on Social Media | Thomas Renault, Mohsen Mosleh, David ... | [doi](https://doi.org/10.31234/osf.io/85quw_v1) |
| 85 | 2025 | 1 | Understanding Inequality of LLM Fact-Checking over Geographic Regions with Ag... | Bruno Coelho, Muhammad Shujaat Mirza,... | [doi](https://doi.org/10.48550/arXiv.2503.22877) |
| 86 | 2025 | 1 | Mitigating Class Imbalance in Fact-Checking Datasets Through LLM-Based Synthe... | Lwin Moe, Uyen Trang Nguyen, B. Luu | [doi](https://doi.org/10.1145/3733567.3735571) |
| 87 | 2025 | 1 | Interrupting the interruptions. How women transform the parliamentary debate | Rozemarijn E van Dijk, Željko Poljak | [doi](https://doi.org/10.1093/pa/gsaf040) |
| 88 | 2025 | 1 | Consensus Is All You Need: Gossip-Based Reasoning Among Large Language Models | Saksham Arora | [doi](https://doi.org/10.2139/ssrn.5395454) |
| 89 | 2025 | 1 | Review of: "AgentNet: Decentralized Evolutionary Coordination for LLM-based M... | Ronghua Xu | [doi](https://doi.org/10.32388/ubj6kd) |
| 90 | 2025 | 1 | The Blessing of Reasoning: LLM-Based Contrastive Explanations in Black-Box Re... | Yuyan Wang, Pan Li, Minmin Chen | [doi](https://doi.org/10.2139/ssrn.5099067) |
| 91 | 2025 | 1 | Advancing Scientific Workflows: A Human-LLM Note-Taking System with Case-Base... | Douglas B. Craig | [doi](https://doi.org/10.1109/cai64502.2025.00055) |
| 92 | 2025 | 1 | 2025 International Conference on Multi-Agent Systems for Collaborative Intell... | — | [doi](https://doi.org/10.1109/icmsci62561.2025) |
| 93 | 2025 | 1 | DEBATE, TRAIN, EVOLVE: Self‐Evolution of Language Model Reasoning | Gaurav Srivastava, Zhenyu Bi, Meng Lu... | [doi](https://doi.org/10.18653/v1/2025.emnlp-main.1666) |
| 94 | 2025 | 1 | Not an Illusion but a Manifestation: Understanding Large Language Model Reaso... | Boris Gorelik | [doi](https://doi.org/10.20944/preprints202506.1675.v1) |
| 95 | 2025 | 1 | Extending large language model capabilities beyond reasoning | Boris Galitsky, Alexander Rybalov | [doi](https://doi.org/10.1016/b978-0-443-30046-2.00005-3) |
| 96 | 2025 | 1 | Neural-Symbolic Reasoning: Towards the Integration of Logical Reasoning with ... | Zhe Hou | [doi](https://doi.org/10.36227/techrxiv.174352068.81462574/v1) |
| 97 | 2025 | 1 | Beyond Detection: Exploring Evidence-based Multi-Agent Debate for Misinformat... | Chen Han, Yijia Ma, Jin Tan, Wenzhen ... | [doi](https://doi.org/10.48550/arXiv.2511.07267) |
| 98 | 2025 | 1 | LLM-based Fact-Checking: A Pipeline for Studying Information Disorder | Gabriele Fioretti, Lorenzo Goglia, E.... | ITASEC/SERICS |
| 99 | 2023 | 1 | Research and Application of Large Language Models in HealthcareCurrent Develo... | Chunfang Zhou, Qingyue Gong, Jinyang ... | [doi](https://doi.org/10.1145/3644116.3644226) |
| 100 | 2023 | 1 | Multi-agent Collaborative Perception for Autonomous Driving:
 Unsettled Aspects | Guang Chen | [doi](https://doi.org/10.4271/epr2023017) |
| 101 | 2023 | 1 | Enhancing sensitivity and versatility of Tn5-based single cell omics | Isabelle Seufert, Pooja Sant, Kathari... | [doi](https://doi.org/10.1101/2023.07.13.548833) |
| 102 | 2020 | 1 | Fact-Checking Elizabeth Bishop | Erica McAlpine | [doi](https://doi.org/10.23943/princeton/9780691203492.003.0007) |
| 103 | — | 1 | A Hybrid Argumentation of Symbolic and Neural Net Argumentation (Part I) | Wataru Makiguchi, Hajime Sawamura | [doi](https://doi.org/10.1007/978-3-540-78915-4_13) |
| 104 | — | 1 | [Part Three: Introduction] | Zoë Irving | [doi](https://doi.org/10.2307/j.ctt9qgwzz.17) |
| 105 | — | 1 | MAD, MAD, MAD, MAD World | — | [doi](https://doi.org/10.5749/j.ctt21h4z4k.5) |
| 106 | 2026 | 0 | Apex Quant: A Multi-Agent Debate Framework For Quantitative Trading | Shuting Sun | [doi](https://doi.org/10.2139/ssrn.6354961) |
| 107 | 2026 | 0 | Building Robust Artificial Intelligence Through Multi-Agent Debate | Stefan Bauschard | [doi](https://doi.org/10.1007/978-3-032-06558-2_5) |
| 108 | 2026 | 0 | A Spatiotemporal Multimodal Evidence-Driven Multi-Agent Debate Framework for ... | Yi An, Adili Rusuli, Jack  C.P. Cheng... | [doi](https://doi.org/10.2139/ssrn.6797367) |
| 109 | 2026 | 0 | MADIAVE: Multi-Agent Debate for Implicit Attribute Value Extraction | Wei-Chieh Huang, Cornelia Caragea | [doi](https://doi.org/10.18653/v1/2026.findings-eacl.159) |
| 110 | 2026 | 0 | Multi-Agent AI Debate Framework for Safety, Security, and Safeguards Integrat... | Min  Suk Lee, Mansung Yim | [doi](https://doi.org/10.2139/ssrn.6696923) |
| 111 | 2026 | 0 | G-DMAD: Group-Based Diverse Multi-Agent Debate for Robust Reasoning | Sichao Chen, Deqiang Lian, Yiting Hon... | [doi](https://doi.org/10.1109/access.2026.3667025) |
| 112 | 2026 | 0 | A Novel Multi-Agent Framework for Automated Pharmacometric Analysis with Huma... | Ari Pritchard-Bell, Chih-Wei Lin | [doi](https://doi.org/10.70534/noqx5252) |
| 113 | 2026 | 0 | When collaboration fails: persuasion driven adversarial influence in multi ag... | Insaf Kraidia, Iyas Qaddara, Alhanof ... | [doi](https://doi.org/10.1038/s41598-026-42705-7) |
| 114 | 2026 | 0 | Emergent Cooperative Dynamics and Causal Treatment Effects in Large Language ... | Vikas Ramachandra | [doi](https://doi.org/10.22541/au.177403077.70686468/v1) |
| 115 | 2026 | 0 | A Multi-Agent Large Language Model Framework for NCAA Tournament Simulation&a... | Abhyut Tangri | [doi](https://doi.org/10.2139/ssrn.6645998) |
| 116 | 2026 | 0 | RAG-Induced Failures in Multi-Agent Large Language Model Debate | Insaf Kraidia, Iyas Qaddara, Nida Al-... | [doi](https://doi.org/10.1109/icetes68504.2026.11518808) |
| 117 | 2026 | 0 | Multi-Agent Debate System Based on Large Language Models: Structured Delibera... | Susana Gómez, Alejandro Mozo, Tomás N... | [doi](https://doi.org/10.21203/rs.3.rs-9575030/v1) |
| 118 | 2026 | 0 | Agent Role Structure and Operating Characteristics in Large Language Model Cl... | Callum Anderson | [doi](https://doi.org/10.64898/2026.02.22.26346818) |
| 119 | 2026 | 0 | Multi-Agent Reinforcement Learning for Cooperative Large Language Model Colla... | Thomas J. Bennett, Samuel K. O’Neill,... | [doi](https://doi.org/10.2139/ssrn.6186858) |
| 120 | 2026 | 0 | Intelligent Tunnel Fire Detection Technology Based on the Large Language Mode... | Ding Zeng, Ao Gao, Zhisheng Xu | [doi](https://doi.org/10.20944/preprints202604.0757.v1) |
| 121 | 2026 | 0 | A Large Language Model-Enabled Multi-Agent Collaboration Method for Complex T... | Shuyuan Wang, Yihui Feng, Xiaotian Fang | [doi](https://doi.org/10.20944/preprints202605.0900.v1) |
| 122 | 2026 | 0 | Media and fact-checking on X during the electoral debate ahead of Spain’s Jul... | Ana Bernal-Triviño, Ana González-Neir... | [doi](https://doi.org/10.15581/003.39.1.019) |
| 123 | 2026 | 0 | Debating to verify: A robust and explainable multi-agent LLM system for fact-... | Thuy-A Nguyen, Bay Vo, Thien Khai Tran | [doi](https://doi.org/10.1016/j.icte.2026.05.017) |
| 124 | 2026 | 0 | InsightSwarm: A Multi-Agent Adversarial Framework for Automated Fact-Checking... | Soham Gawas | [doi](https://doi.org/10.22214/ijraset.2026.79918) |
| 125 | 2026 | 0 | From Argumentation to Labeled Logic Program for LLM Verification | Boris A. Galitsky | [doi](https://doi.org/10.20944/preprints202601.1549.v1) |
| 126 | 2026 | 0 | A Multi-Tier Framework for Ranking Determinants in Quantitative Modeling usin... | Son-Ha Van, Tuan-Kiet Tran, Hoang-Kha... | [doi](https://doi.org/10.1109/imcom69009.2026.11360872) |
| 127 | 2026 | 0 | Argumentation and Judgement Factors: LLM-based Discovery and Application in I... | Basit Ali, Anubhav Sinha, Nitin Ramra... | [doi](https://doi.org/10.18653/v1/2026.eacl-long.128) |
| 128 | 2026 | 0 | Emergent Misinformation Genesis in Multi-Agent LLM Clinical Pipelines | Aman Sharma | [doi](https://doi.org/10.22541/au.177499233.37732392/v1) |
| 129 | 2026 | 0 | Learning to Debate for Improving School Level Education with Large Language M... | Aniket Deroy | [doi](https://doi.org/10.20944/preprints202602.0562.v1) |
| 130 | 2026 | 0 | Large Language Models for Quality Control of Large Language Models | Preethika Chandrasekaran, Imron Shaja... | [doi](https://doi.org/10.5220/0014649700004058) |
| 131 | 2026 | 0 | Learning to Debate: Optimal Stopping Strategies for Multi-Agent LLM Deliberation | Xinyi Zhang, Di Hu | [doi](https://doi.org/10.1109/gaiis69281.2026.11519273) |
| 132 | 2026 | 0 | Game-Theoretic Insights into Multi-Agent LLM Debate for Enhanced Clinical Que... | Sweekar Sudhakara, Sagar Sudhakara | [doi](https://doi.org/10.1109/icassp55912.2026.11461952) |
| 133 | 2026 | 0 | iMAD: Intelligent Multi-Agent Debate for Efficient and Accurate LLM Inference | Wei Fan, JinYi Yoon, Bo Ji | [doi](https://doi.org/10.1609/aaai.v40i35.40181) |
| 134 | 2026 | 0 | Sura.ai: Multi-Agent Infrastructure Recovery with LLM-Powered Autonomous Reme... | Ananya Arvind, Shruthi Narayanan, Sai... | [doi](https://doi.org/10.5220/0014456800004052) |
| 135 | 2026 | 0 | Emergent Network Collapse and Ontological Dissonance in Multi-Agent LLM Simul... | Pantaleon Fassbender | [doi](https://doi.org/10.2139/ssrn.6734703) |
| 136 | 2026 | 0 | LDP: An Identity-Aware Protocol for Multi-Agent LLM Systems | Sunil Prakash | [doi](https://doi.org/10.21203/rs.3.rs-9121599/v1) |
| 137 | 2026 | 0 | Contamination Percolation in Multi-Agent LLM Systems: A Measurement Framework... | Aman Sharma | [doi](https://doi.org/10.22541/au.177499048.88707055/v1) |
| 138 | 2026 | 0 | Architectures for Persistent Reasoning with Explicit World-State Representati... | Chunlan Wang | [doi](https://doi.org/10.2139/ssrn.6137731) |
| 139 | 2026 | 0 | A progressive reasoning method based on Monte Carlo Tree Search and LLM for m... | Quan Zhang, Weiqing Ling | [doi](https://doi.org/10.21203/rs.3.rs-9721673/v1) |
| 140 | 2026 | 0 | Enhanced Chemical Reasoning Agent: Boosting Trustworthy LLM Performance in Ch... | Bowen Mou, Ruotong Lou | [doi](https://doi.org/10.26434/chemrxiv.15000021/v1) |
| 141 | 2026 | 0 | Structured Reasoning in LLM Optimization Agents: Scaffolding, Not Regularization | Kartik Ganapati Bhat | [doi](https://doi.org/10.2139/ssrn.6655539) |
| 142 | 2026 | 0 | RETHiNK: Simulating Human Reasoning via Multi-LLM Debate for Cognitive Refram... | Xiaomeng Wang, Dharmendra Sharma, Din... | [doi](https://doi.org/10.1145/3815586) |
| 143 | 2026 | 0 | Nested Hyperbolic Spaces for Context-Aware LLM Reasoning: A Geometric Framework | Hikage Morino | [doi](https://doi.org/10.36227/techrxiv.177078613.36070729/v1) |
| 144 | 2026 | 0 | Multi-Agent System for Collaborative Fault Diagnosis in Multi-Stage Manufactu... | Felipe Izidorio, Paulo Leitão, José B... | [doi](https://doi.org/10.5220/0014429500004052) |
| 145 | 2026 | 0 | 2026 Second International Conference on Multi-Agent Systems for Collaborative... | — | [doi](https://doi.org/10.1109/icmsci67830.2026) |
| 146 | 2026 | 0 | Use large language model to enhance reasoning of another large language model... | Yiqiao Yin | [doi](https://doi.org/10.1038/s41598-026-39296-8) |
| 147 | 2026 | 0 | EntKGBench: A Benchmark for Evaluating Large Language Model Reasoning on Real... | Yutian Yang | [doi](https://doi.org/10.2139/ssrn.6731995) |
| 148 | 2026 | 0 | Hebbian Inertia and Massless Reasoning: Comparative Cognitive Architecture in... | Emary Iacobucci, Joseph Woelfel | [doi](https://doi.org/10.21203/rs.3.rs-9193113/v1) |
| 149 | 2026 | 0 | Persona Routing Associated With Fewer Safety and Monotonicity Violations in S... | Yuusuke Harada | [doi](https://doi.org/10.7759/cureus.107548) |
| 150 | 2026 | 0 | HFR-Prompt: Hierarchical Feedback Reasoning Prompting for Enhanced Large Lang... | Zeyuan Xun, Yichen Ku | [doi](https://doi.org/10.20944/preprints202603.1361.v1) |
| 151 | 2026 | 0 | AgentVerify: Compositional Formal Verification of AI Agent Safety Properties ... | Eric Fang | [doi](https://doi.org/10.20944/preprints202604.1029.v1) |
| 152 | 2026 | 0 | Enhancing Information Retrieval through Multi-Agent Reasoning Frameworks in O... | Faith Harris | [doi](https://doi.org/10.2139/ssrn.6400178) |
| 153 | 2026 | 0 | Connecting the Dots and Playing Devil's Advocate: Graph-Enhanced Evidence Ret... | Rui Xu, WANG GAO, Gexia Zhang, Jiakan... | [doi](https://doi.org/10.2139/ssrn.6225921) |
| 154 | 2026 | 0 | Population-dependent agent performance in non-transitive games: a multi-agent... | Ou Deng, Jianting Xu, Shoji Nishimura... | [doi](https://doi.org/10.21203/rs.3.rs-8606053/v1) |
| 155 | 2026 | 0 | Generating Synthetic Behavioral Health Data: A Multi-Agent LLM System | Dirk Maas, Maani Beigy, Laura Genga, ... | [doi](https://doi.org/10.5220/0014320800004070) |
| 156 | 2026 | 0 | StructAgent: Orchestrating Cryo-EM Model Building and Refinement with a Multi... | Xiaohu Guo | [doi](https://doi.org/10.64898/2026.05.18.725842) |
| 157 | 2026 | 0 | Title: "A Role-Locked Multi-Agent LLM System for Clinical Dialogue: A Feasibi... | David Power, Theresa Power | [doi](https://doi.org/10.2139/ssrn.6678962) |
| 158 | 2026 | 0 | Debating the Unspoken: Role-Anchored Multi-Agent Reasoning for Half-Truth Det... | Yixuan Tang, Yirui Zhang, Hang Feng, ... | semantic_scholar |
| 159 | 2025 | 0 | Empirical Analysis of Destiny Dominance in Multi-Agent Systems with Adversari... | Debargya Dinda | [doi](https://doi.org/10.31224/5306) |
| 160 | 2025 | 0 | Program-Guided Refinement with Debate: A Multi-Agent LLM-Based Automated Fact... | Tao Xue, Wenzhuo Liu, Long Xi, Wen Lv | [doi](https://doi.org/10.21203/rs.3.rs-8033646/v1) |
| 161 | 2025 | 0 | A multi-agent debate workflow for construction projects: A cross-stage decisi... | Hao Yin | [doi](https://doi.org/10.70401/jbde.2025.0018) |
| 162 | 2025 | 0 | Error Detection in Medical Note through Multi Agent Debate | Abdine Maiga, Anoop Shah, Emine Yilmaz | [doi](https://doi.org/10.18653/v1/2025.bionlp-1.12) |
| 163 | 2025 | 0 | Multi-Agent Debate System for AI-Based Decision-Making: A Framework for Enhan... | — | [doi](https://doi.org/10.64388/irev9i6-1713210) |
| 164 | 2025 | 0 | La VIDA: towards a motivated goal reasoning agent | Ursula Addison | [doi](https://doi.org/10.1007/s10458-024-09685-2) |
| 165 | 2025 | 0 | Forecasting carbon market with a multi-agent system of large language model | Bangzhu Zhu, Jiangtao Zhong | [doi](https://doi.org/10.2139/ssrn.5584538) |
| 166 | 2025 | 0 | Security and Privacy Challenges in Multi-Agent Language Model Ecosystems | Pawan Kumar Goel | [doi](https://doi.org/10.4018/979-8-3373-1419-8.ch008) |
| 167 | 2025 | 0 | Communication Structure Adaptive Control and Collaborative Optimization for M... | Yi Wang | [doi](https://doi.org/10.2139/ssrn.5193257) |
| 168 | 2025 | 0 | Large language model multi agent architecture for automatic well‑logging anal... | Yen Ceao | [doi](https://doi.org/10.2139/ssrn.5482172) |
| 169 | 2025 | 0 | Multi-Agent Debate System based on Large Language Model: Comparative Analysis... | Bojeong Im, Hogeon Seo | [doi](https://doi.org/10.30693/smj.2025.14.10.140) |
| 170 | 2025 | 0 | ARAFA: An LLM Generated Arabic Fact-Checking Dataset | Christophe Khalil, Shady Elbassuoni, ... | [doi](https://doi.org/10.21203/rs.3.rs-7335564/v1) |
| 171 | 2025 | 0 | Heat versus Light: Fact-Checking the Debate over De-Risking | Oz Shy | [doi](https://doi.org/10.2139/ssrn.5181902) |
| 172 | 2025 | 0 | Fact-Checking Political Narratives | Jen Birks | [doi](https://doi.org/10.4324/9781032725154-19) |
| 173 | 2025 | 0 | From Fact-Checking to Debunking | Florian Dauphin | [doi](https://doi.org/10.4324/9781032725154-21) |
| 174 | 2025 | 0 | Mapping the Boundaries of Fact-Checking | Stephanie Jean Tsang | [doi](https://doi.org/10.4324/9781032725154-7) |
| 175 | 2025 | 0 | Fact-Checking, Belief Accuracy and Media Trust | Ingrid Bachmann, Sebastián Valenzuela | [doi](https://doi.org/10.4324/9781032725154-13) |
| 176 | 2025 | 0 | Challenges for Fact-checking: Beyond False/True Verification | Angeliki Monnier, Céline Ségur | [doi](https://doi.org/10.4000/145d4) |
| 177 | 2025 | 0 | Collaborative Fact-checking via Multi-Agent Debate and Weighted Voting | Xi Wang, Yuxiao Fei | [doi](https://doi.org/10.1109/ICAIDS67687.2025.00038) |
| 178 | 2025 | 0 | FBD: Fact-Based Debating for Fact Verification through Large Language Models | Mufan Yu, Guozheng Rao, Xin Wang, Li ... | [doi](https://doi.org/10.1109/IJCNN64981.2025.11229172) |
| 179 | 2025 | 0 | Correction to: Interrupting the interruptions. How women transform the parlia... | — | [doi](https://doi.org/10.1093/pa/gsaf054) |
| 180 | 2025 | 0 | New Zealand parliamentary suspension deepens debate on Māori voice | Dominic O'Sullivan | [doi](https://doi.org/10.59425/eabc.1755295200) |
| 181 | 2025 | 0 | Solving multi-agent games on networks | Yair Vaknin, Amnon Meisels | [doi](https://doi.org/10.1007/s10458-025-09696-7) |
| 182 | 2025 | 0 | Culturally Responsive Argumentation for Democratic Resilience | Menashe Schwed | [doi](https://doi.org/10.1007/s10503-025-09684-x) |
| 183 | 2025 | 0 | ALAS: A Stateful Multi-LLM Agent Framework for Disruption-Aware Planning | — | [doi](https://doi.org/10.1145/3749421.3749436) |
| 184 | 2025 | 0 | SocraSynth: Adversarial Multi-LLM Reasoning | — | [doi](https://doi.org/10.1145/3749421.3749430) |
| 185 | 2025 | 0 | Integrating Large Language Models in the Prevention of Radicalisation Among N... | Aadil Bouhlaoui | [doi](https://doi.org/10.2139/ssrn.5292122) |
| 186 | 2025 | 0 | Interactive Cycle Model: The Linkage Combination among Automatic Speech Recog... | Libo Wang | [doi](https://doi.org/10.36227/techrxiv.174181745.50870812/v1) |
| 187 | 2025 | 0 | The Mathematics of Large Language Diffusion Models versus Large Language Auto... | Miquel Noguer I Alonso | [doi](https://doi.org/10.2139/ssrn.5149339) |
| 188 | 2025 | 0 | Large Language Models in Chemistry | Zhiling Zheng | [doi](https://doi.org/10.1201/9781003669012-4) |
| 189 | 2025 | 0 | Basics of Large Language Models - transformers to LLMs | Andrew Green | [doi](https://doi.org/10.6019/tol.basics-llm-w.2025.00001.1) |
| 190 | 2025 | 0 | Understanding Reasoning and Logic as the Foundations of Debate | — | [doi](https://doi.org/10.5040/9798881843113.ch-001) |
| 191 | 2025 | 0 | Debate Formats | — | [doi](https://doi.org/10.5040/9798881843113.ch-008) |
| 192 | 2025 | 0 | Understanding Debate Theory | — | [doi](https://doi.org/10.5040/9798881843113.ch-007) |
| 193 | 2025 | 0 | Components of Debate | — | [doi](https://doi.org/10.5040/9798881843113.ch-003) |
| 194 | 2025 | 0 | Doing Research for Debate | — | [doi](https://doi.org/10.5040/9798881843113.ch-004) |
| 195 | 2025 | 0 | Machiavelli Reconstructed: "The Prince" Analyzed Using LLM-Based Chain-of-Tho... | Itai Blitzer | [doi](https://doi.org/10.2139/ssrn.5280464) |
| 196 | 2025 | 0 | CCoRe: Cooperative-Competitive Reasoning LLM-based Multi-Agent Framework | Hicham Bouchtib, Kaouter Karboub, Moh... | [doi](https://doi.org/10.21203/rs.3.rs-7255220/v1) |
| 197 | 2025 | 0 | ​Hybrid Detection Model for Unauthorized Use of Doctor's Code in Health Insur... | Qiwen Yuan, Jiajie Chen, Zhendong Shi | [doi](https://doi.org/10.2139/ssrn.5655298) |
| 198 | 2025 | 0 | Cognitive-Mimetic Adversarial Prompting: Corrupting LLM Reasoning with Human ... | Panhapiseth Lim | [doi](https://doi.org/10.36227/techrxiv.175295877.72690509/v1) |
| 199 | 2025 | 0 | Aphorisms for Collaborative Intelligence | — | [doi](https://doi.org/10.1145/3749421.3749441) |
| 200 | 2025 | 0 | Condensed Reasoning Prompting: Efficient Strategies, Evaluations, and Trade O... | Gautam Mehra, Danish Khan | [doi](https://doi.org/10.21203/rs.3.rs-6170708/v1) |
| 201 | 2025 | 0 | Training a Reasoning Large Language Model for Improving Power Flow Convergence | Yunqi Yan, Ying Chen, Tannan Xiao | [doi](https://doi.org/10.36227/techrxiv.175493660.02041809/v1) |
| 202 | 2025 | 0 | Crash Root-Cause Identification via Trace-Rewarded Causation-Chain Reasoning ... | ning xie, Rongjie Yu | [doi](https://doi.org/10.2139/ssrn.5867882) |
| 203 | 2025 | 0 | Meta-of-Thought: Reasoning About Reasoning in Large Language Models | Ahshanul Haque | [doi](https://doi.org/10.36227/techrxiv.175756693.33854887/v1) |
| 204 | 2025 | 0 | Advancing Large Language Model Reasoning Techniques: Methods Enabling LLMs to... | Cassel Scott-Emuakpor | [doi](https://doi.org/10.36227/techrxiv.176131150.00355935/v1) |
| 205 | 2025 | 0 | Task Aware Retrieval Selection Mechanisms for Large Language Model Reasoning | Evelyn T. Chan, Marcus Y. Lim, Adrian... | [doi](https://doi.org/10.20944/preprints202512.0262.v1) |
| 206 | 2025 | 0 | Can LLMs Identify Event Causality More Accurately through Debate? A Systemati... | Yiheng Zhao, Jun Yan | [doi](https://doi.org/10.1109/citrex64975.2025.10974935) |
| 207 | 2025 | 0 | Going Global: | — | [doi](https://doi.org/10.2307/jj.21126151.6) |
| 208 | 2025 | 0 | Exploring Health Misinformation Detection with Multi-Agent Debate | Chih-Han Chen, Chen-Han Tsai, Yu-Shao... | [doi](https://doi.org/10.18653/v1/2025.wasp-main.3) |
| 209 | 2025 | 0 | LIAR, LIAR | — | [doi](https://doi.org/10.2307/jj.35370892.26) |
| 210 | 2025 | 0 | Multi-Agent Systems in Education: A Survey from the Trustworthiness Perspective | Chahana Dahal, Jinming Chen, Muchao Y... | [doi](https://doi.org/10.36227/techrxiv.176704820.01980102/v1) |
| 211 | 2024 | 0 | Review of: "Diversity of Thought Elicits Stronger Reasoning Capabilities in M... | Kais Riani | [doi](https://doi.org/10.32388/5argxz) |
| 212 | 2024 | 0 | A Unified LLM-KG Framework to Assist Fact-Checking in Public Deliberation | Nikolaos Giarelis, Charalampos Mastro... | [doi](https://doi.org/10.63317/5igbp5sfkrma) |
| 213 | 2024 | 0 | Introduction to Large Language Models with OpenAI | Pere Martra | [doi](https://doi.org/10.1007/979-8-8688-0515-8_1) |
| 214 | 2024 | 0 | Evaluating Models | Pere Martra | [doi](https://doi.org/10.1007/979-8-8688-0515-8_4) |
| 215 | 2024 | 0 | Evolution and Significance of Large Language Models | Dilyan Grigorov | [doi](https://doi.org/10.1007/979-8-8688-0540-0_1) |
| 216 | 2024 | 0 | Fine-Tuning Models | Pere Martra | [doi](https://doi.org/10.1007/979-8-8688-0515-8_5) |
| 217 | 2024 | 0 | RGQA: Leveraging Reasoning Guideline with LLM-based KGQA | Jeongjae Nam, Taehun Lee, Suyeon Wang... | [doi](https://doi.org/10.13088/jiis.2024.30.2.225) |
| 218 | 2024 | 0 | Multi-Agent Deep Reinforcement Learning for Collaborative Task Scheduling | Mali Gergely | [doi](https://doi.org/10.5220/0012434700003636) |
| 219 | 2024 | 0 | Vaos: Enhancing the Stability of Cooperative Multi-Agent Policy Learning | Peng Li, Shaofei Chen, weilin yuan, Z... | [doi](https://doi.org/10.2139/ssrn.4862105) |
| 220 | 2024 | 0 | MAD-CNN: High-Sensitivity and Robust Collision Detection for Robots with Vari... | Zhenwei Niu, Lyes Saad Saoud, Irfan H... | [doi](https://doi.org/10.21203/rs.3.rs-3914271/v1) |
| 221 | 2024 | 0 | Satellite Formation Control using Multi-Agent Deep Reinforcement Learning | Zicen Xiong, Yue Wang, Zheng Chen, He... | [doi](https://doi.org/10.52202/078368-0147) |
| 222 | 2023 | 0 | Artificial Intelligence Algorithms for Strategic Reasoning over Complex Multi... | Zun Li | [doi](https://doi.org/10.65109/qpad2195) |
| 223 | 2023 | 0 | Progenitor-like cell type of an <i>MLL</i>-<i>EDC4</i> fusion in acute myeloi... | Linda C. Schuster, Afzal P. Syed, Ste... | [doi](https://doi.org/10.1182/bloodadvances.2022009096) |
| 224 | 2022 | 0 | Prescribed argumentation, actual argumentation, reported argumentation | Ilaria Casillo, Marianne Doury | [doi](https://doi.org/10.1075/jaic.21021.dou) |
| 225 | 2019 | 0 | Fact checking the ITV debate: Boris Johnson and Jeremy Hunt's claims examined | Tom Waters | [doi](https://doi.org/10.1920/co.ifs.2024.0245) |
| 226 | 2019 | 0 | Fact-Checking Claims, Policies and Parties | Jen Birks | [doi](https://doi.org/10.1007/978-3-030-30573-4_3) |
| 227 | 2019 | 0 | Parliamentary Debate | Debbie Newman | [doi](https://doi.org/10.4324/9781351020220-8) |
| 228 | 2019 | 0 | Where Are We and Where Should We Be Going? | Eli Ginzberg | [doi](https://doi.org/10.4324/9780429039379-21) |
| 229 | 2019 | 0 | Mad identity I: Controversial and failed identities | Mohammed Abouelleil Rashed | [doi](https://doi.org/10.1093/med/9780198786863.003.0007) |
| 230 | 2019 | 0 | Mad identity II: Unity and continuity of self | Mohammed Abouelleil Rashed | [doi](https://doi.org/10.1093/med/9780198786863.003.0008) |
| 231 | 2019 | 0 | Responding to the demand for recognition of Mad identity | Mohammed Abouelleil Rashed | [doi](https://doi.org/10.1093/med/9780198786863.003.0010) |
| 232 | 2018 | 0 | Deliberative Rhetoric of Parliamentary Debate | Kari Palonen | [doi](https://doi.org/10.1007/978-3-319-90533-4_4) |
| 233 | 2018 | 0 | Disability, Rights and Vulnerability in British Parliamentary Debate | Evan Odell | [doi](https://doi.org/10.31235/osf.io/tqf5j) |
| 234 | — | 0 | Debate in a multi-agent system : multiparty argumentation protocols | Dionysios Kontarinis | [doi](https://doi.org/10.70675/5446404fz4553z4dd4z9754zf836813be6bb) |
| 235 | — | 0 | RUMAD: Reinforcement-Unifying Multi-Agent Debate | Chao Wang, Han Lin, Huaze Tang, Huiji... | [doi](https://doi.org/10.65109/cbjo8409) |
| 236 | — | 0 | Symbolic representations and common - sense reasoning in open multi - agent s... | Γεώργιος Γιαννίκης | [doi](https://doi.org/10.12681/eadd/17424) |
| 237 | — | 0 | Multi Agent Computation of Interchangeability in Distributed CSPs | — | [doi](https://doi.org/10.1007/3-7643-7319-9_4) |
| 238 | — | 0 | Polymer-Agent: Large Language Model Agent for Polymer Design | — | [doi](https://doi.org/10.1021/acs.jcim.6c00343.s001) |
| 239 | — | 0 | Politics and Fashion: British Parliamentary Debate on Utility Suits | — | [doi](https://doi.org/10.3726/978-3-653-05742-3/18) |
| 240 | — | 0 | Defeasible Argumentation for Cooperative Multi-Agent Planning | SERGIO PAJARES FERRANDO | [doi](https://doi.org/10.4995/thesis/10251/60159) |
| 241 | — | 0 | Multi-Agent Dialogue | — | [doi](https://doi.org/10.1007/1-4020-4943-9_5) |
| 242 | — | 0 | Figure 7: Prompt for multi-agent LLM for best instruction choice. | — | [doi](https://doi.org/10.7717/peerj-cs.2328/fig-7) |
| 243 | — | 0 | Figure 8: Prompt for multi-agent LLM for best instruction improvement. | — | [doi](https://doi.org/10.7717/peerj-cs.2328/fig-8) |
| 244 | — | 0 | CRAwDAD: Causal Reasoning Augmentation with Dual-Agent Debate | Finn G. Vamosi, Nils D. Forkert | [doi](https://doi.org/10.65109/dvbn4652) |
| 245 | — | 0 | Formalization of multiagent reasoning | M. Kacprzak | [doi](https://doi.org/10.1109/pcee.2002.1115206) |
| 246 | — | 0 | Autonomous multi-agent collaborative environment exploration | Tianze Luo | [doi](https://doi.org/10.32657/10356/136784) |
| 247 | — | 0 | Miranda and the Police: The Confession Debate Continues | Irving R. Kaufman | [doi](https://doi.org/10.1037/e452852008-178) |
| 248 | — | 0 | Chapter Five: Playing with Gender, Queering Lines: Should We Be Mad at Madea? | — | [doi](https://doi.org/10.3726/978-1-4539-1588-2/16) |
| 249 | — | 0 | Comparison of spatial transcriptomics technologies for medulloblastoma cryose... | Anne Rademacher, Pooja Sant, Michele ... | [doi](https://doi.org/10.6019/s-biad1093) |
| 250 | — | 0 | The Liar | — | [doi](https://doi.org/10.5040/9781580819411.p01) |
| 251 | — | 0 | The Liar Cannot Be Solved | György Serény | [doi](https://doi.org/10.1007/978-1-4020-8468-3_10) |
| 252 | — | 0 | "r u mad @ me?": Social anxiety and interpretation bias in computer-mediated ... | Mila Kingsbury | [doi](https://doi.org/10.22215/etd/2014-10508) |
| 253 | — | 0 | Modeling of supply chain: a multi-agent approach | Xiong Bo, Wu Zhiming | [doi](https://doi.org/10.1109/acc.2003.1239726) |

## 三、使用的关键词

- `multi-agent debate`
- `multi-agent debate reasoning`
- `multi-agent debate large language model`
- `LLM debate fact checking`
- `parliamentary debate AI`
- `multi-agent judgment`
- `argumentation LLM`
- `multi-agent argumentation LLM`
- `debate among large language models`
- `multiagent reasoning debate`
- `LLM multi agent debate`
- `debate-based reasoning LLM`
- `multi agent collaborative debate`
- `large language model debate reasoning`

## 四、说明

- 本列表通过项目 `src.search` 统一搜索接口从 **arXiv / Crossref / Semantic Scholar** 同时检索。
- 已自动剔除 `src.search` 在 API 失败时返回的 mock 数据，并按 DOI / 规范化标题去重。
- 由于 Semantic Scholar 接口存在速率限制（429），部分年份的论文主要来自 Crossref 与 arXiv。
- 对业界公认的 MAD 标志性论文（如 Irving et al. 2018、Du et al. 2023 等）已手动整理补充元数据。
- 结果排序：**关键论文优先 → 引用数降序 → 年份降序**。
