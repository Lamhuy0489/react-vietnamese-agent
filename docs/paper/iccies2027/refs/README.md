# Tài liệu tham khảo: bản PDF gốc và link

20 bài tải từ arXiv ngày 2026-11-10. Đã kiểm ba lớp: (1) tên bài và tác giả lấy từ metadata arXiv
(API `export.arxiv.org`) đúng với ID; (2) file tải về là PDF hợp lệ; (3) trang đầu của từng PDF đọc ra đúng tên bài.
Nơi đăng chỉ ghi khi arXiv hoặc trang đầu PDF nêu rõ; chỗ ghi "cần kiểm" là chưa có bằng chứng, không dùng trong bài
trước khi đối chiếu trang nhà xuất bản. Cột "Dùng cho" là gợi ý chỗ trích, chưa phải kết quả đọc kỹ từng bài.

PDF **không commit** (`.gitignore`): repo public, giấy phép từng bài khác nhau. Tải lại: `https://arxiv.org/pdf/<ID>`.

| Khóa | Bài (link) | Tác giả | Nơi đăng | File PDF | Dùng cho |
|---|---|---|---|---|---|
| ReAct | [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) | Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao | ICLR 2023 (ghi trên trang đầu PDF) | `yao2023_react.pdf` (2210.03629v3) | agent ReAct (Mục 1, 2.1) |
| Greshake | [Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173) | Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, Mario Fritz | arXiv không ghi; cần kiểm (nhớ là AISec 2023) | `greshake2023_indirect_prompt_injection.pdf` (2302.12173v2) | định nghĩa IPI (Mục 1) |
| Liu | [Formalizing and Benchmarking Prompt Injection Attacks and Defenses](https://arxiv.org/abs/2310.12815) | Yupei Liu, Yuqi Jia, Runpeng Geng, Jinyuan Jia, Neil Zhenqiang Gong | USENIX Security 2024 (arXiv ghi) | `liu2024_formalizing_prompt_injection.pdf` (2310.12815v5) | hình thức hóa tấn công và phòng thủ (Mục 1, 2) |
| BIPIA | [Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models](https://arxiv.org/abs/2312.14197) | Jingwei Yi, Yueqi Xie, Bin Zhu, Emre Kiciman, Guangzhong Sun, Xing Xie, Fangzhao Wu | KDD 2025 (arXiv ghi) | `yi2025_bipia.pdf` (2312.14197v4) | benchmark IPI (Mục 1) |
| InjecAgent | [InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents](https://arxiv.org/abs/2403.02691) | Qiusi Zhan, Zhixiang Liang, Zifan Ying, Daniel Kang | Findings of ACL 2024 (arXiv ghi) | `zhan2024_injecagent.pdf` (2403.02691v3) | benchmark agent (Mục 1) |
| AgentDojo | [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents](https://arxiv.org/abs/2406.13352) | Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, Florian Tramèr | arXiv không ghi; cần kiểm (nhớ là NeurIPS 2024 Datasets and Benchmarks) | `debenedetti2024_agentdojo.pdf` (2406.13352v3) | ngoại kiểm (Mục 4.6, 5.4) |
| ASB | [Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents](https://arxiv.org/abs/2410.02644) | Hanrong Zhang, Jingyuan Huang, Kai Mei, Yifei Yao, Zhenting Wang, Chenlu Zhan, Hongwei Wang, Yongfeng Zhang | ICLR 2025 (ghi trên trang đầu PDF) | `zhang2025_agent_security_bench.pdf` (2410.02644v4) | benchmark agent (Mục 1) |
| Spotlighting | [Defending Against Indirect Prompt Injection Attacks With Spotlighting](https://arxiv.org/abs/2403.14720) | Keegan Hines, Gary Lopez, Matthew Hall, Federico Zarfati, Yonatan Zunger, Emre Kiciman | arXiv không ghi; cần kiểm | `hines2024_spotlighting.pdf` (2403.14720v1) | baseline P1 (Mục 4.4) |
| StruQ | [StruQ: Defending Against Prompt Injection with Structured Queries](https://arxiv.org/abs/2402.06363) | Sizhe Chen, Julien Piet, Chawin Sitawarin, David Wagner | USENIX Security 2025 (arXiv ghi) | `chen2025_struq.pdf` (2402.06363v2) | phòng thủ bằng huấn luyện (Mục 1) |
| SecAlign | [SecAlign: Defending Against Prompt Injection with Preference Optimization](https://arxiv.org/abs/2410.05451) | Sizhe Chen, Arman Zharmagambetov, Saeed Mahloujifar, Kamalika Chaudhuri, David Wagner, Chuan Guo | ACM CCS 2025 (arXiv ghi) | `chen2025_secalign.pdf` (2410.05451v3) | phòng thủ bằng huấn luyện (Mục 1) |
| MELON | [MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents](https://arxiv.org/abs/2502.05174) | Kaijie Zhu, Xianjun Yang, Jindong Wang, Wenbo Guo, William Yang Wang | ICML 2025 (arXiv ghi) | `zhu2025_melon.pdf` (2502.05174v4) | baseline MEL (Mục 4.4) |
| Progent | [Progent: Securing AI Agents with Privilege Control](https://arxiv.org/abs/2504.11703) | Tianneng Shi, Jingxuan He, Zhun Wang, Hongwei Li, Linyu Wu, Wenbo Guo, Dawn Song | arXiv preprint (chưa thấy nơi đăng) | `shi2025_progent.pdf` (2504.11703v3) | baseline PRG (Mục 4.4) |
| LlamaFirewall | [LlamaFirewall: An open source guardrail system for building secure AI agents](https://arxiv.org/abs/2505.03574) | Sahana Chennabasappa, Cyrus Nikolaidis, Daniel Song, David Molnar, Stephanie Ding, Shengye Wan, Spencer Whitman, Lauren Deason, Nicholas Doucette, Abraham Montilla, Alekhya Gampa, Beto de Paola, Dominik Gabi, James Crnkovich, Jean-Christophe Testud, Kat He, Rashnil Chaturvedi, Wu Zhou, Joshua Saxe | arXiv preprint (chưa thấy nơi đăng) | `chennabasappa2025_llamafirewall.pdf` (2505.03574v1) | nguồn trích cho Prompt Guard 2, baseline G1 (Mục 4.4) |
| CaMeL | [Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813) | Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph Kern, Chongyang Shi, Andreas Terzis, Florian Tramèr | arXiv preprint (chưa thấy nơi đăng) | `debenedetti2025_camel.pdf` (2503.18813v2) | phòng thủ theo thiết kế (Mục 1, 3) |
| FIDES | [Securing AI Agents with Information-Flow Control](https://arxiv.org/abs/2505.23643) | Manuel Costa, Boris Köpf, Aashish Kolluri, Andrew Paverd, Mark Russinovich, Ahmed Salem, Shruti Tople, Lukas Wutschitz, Santiago Zanella-Béguelin | arXiv preprint (chưa thấy nơi đăng) | `costa2025_information_flow_control.pdf` (2505.23643v2) | luồng thông tin, nhãn tin cậy và nhạy cảm (Mục 2.2, 3) |
| DesignPatterns | [Design Patterns for Securing LLM Agents against Prompt Injections](https://arxiv.org/abs/2506.08837) | Luca Beurer-Kellner, Beat Buesser, Ana-Maria Creţu, Edoardo Debenedetti, Daniel Dobos, Daniel Fabian, Marc Fischer, David Froelicher, Kathrin Grosse, Daniel Naeff, Ezinwanne Ozoani, Andrew Paverd, Florian Tramèr, Václav Volhejn | arXiv preprint (chưa thấy nơi đăng) | `beurerkellner2025_design_patterns.pdf` (2506.08837v3) | mẫu thiết kế agent an toàn (Mục 3) |
| AdaptiveIPI | [Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents](https://arxiv.org/abs/2503.00061) | Qiusi Zhan, Richard Fang, Henil Shalin Panchal, Daniel Kang | Findings of NAACL 2025 (arXiv ghi) | `zhan2025_adaptive_attacks.pdf` (2503.00061v2) | tấn công thích nghi (Mục 5.5, 6) |
| AttackerSecond | [The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against Llm Jailbreaks and Prompt Injections](https://arxiv.org/abs/2510.09023) | Milad Nasr, Nicholas Carlini, Chawin Sitawarin, Sander V. Schulhoff, Jamie Hayes, Michael Ilie, Juliette Pluto, Shuang Song, Harsh Chaudhari, Ilia Shumailov, Abhradeep Thakurta, Kai Yuanqing Xiao, Andreas Terzis, Florian Tramèr | preprint, đang phản biện (ghi trên PDF) | `nasr2025_attacker_moves_second.pdf` (2510.09023v1) | tấn công thích nghi, hạn chế (Mục 6) |
| MultiJail | [Multilingual Jailbreak Challenges in Large Language Models](https://arxiv.org/abs/2310.06474) | Yue Deng, Wenxuan Zhang, Sinno Jialin Pan, Lidong Bing | ICLR 2024 (ghi trên trang đầu PDF) | `deng2024_multilingual_jailbreak.pdf` (2310.06474v3) | an toàn đa ngôn ngữ (Mục 1, 6) |
| vLLM | [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) | Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph E. Gonzalez, Hao Zhang, Ion Stoica | SOSP 2023 (arXiv ghi) | `kwon2023_vllm_pagedattention.pdf` (2309.06180v1) | hệ phục vụ mô hình (Mục 4.3) |

## Chưa có PDF

- **Prompt Guard 2** (Meta): không có bài báo riêng. Trích LlamaFirewall (bảng trên) và model card; khi viết cần chép URL
  model card và ngày truy cập.
- **Holm (1979)**, *A simple sequentially rejective multiple test procedure*, Scandinavian Journal of Statistics 6(2), 65–70.
  **McNemar (1947)**, *Note on the sampling error of the difference between correlated proportions or percentages*,
  Psychometrika 12(2), 153–157. Không có trên arXiv; thông tin thư mục ghi theo trí nhớ, **chưa đối chiếu** bản nhà xuất bản.
- Template Springer LNCS: tải từ trang Springer khi chuyển định dạng.

## Còn phải làm khi soát trích dẫn

- Các ô "cần kiểm" ở cột Nơi đăng; tên kỷ yếu đầy đủ, số trang, DOI của bài đã đăng hội nghị.
- Mỗi câu trích trong bài phải được người viết mở PDF đọc đúng đoạn liên quan; không trích theo tóm tắt.
