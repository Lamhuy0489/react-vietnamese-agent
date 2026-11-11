# Vietnamese ReAct Tool-Agent Evaluation

Đồ án đánh giá khả năng, độ bền vững và an toàn của tác nhân ReAct dùng công cụ trong môi trường tiếng Việt giả lập
(hành chính – học vụ đại học), gồm hai nghiên cứu:

| | Study 1 | **Study 2 (hiện tại)** |
|---|---|---|
| Câu hỏi | Dựng benchmark sạch và adversarial tiếng Việt, đo tác nhân A0–A6 | Phòng thủ prompt injection gián tiếp cho tác nhân dùng công cụ: cơ chế **D3** |
| Giai đoạn | Phase 1–5 (09–10/2026) | Rebuild A, R0–R4, Test niêm phong (10–11/2026) |
| Trạng thái | Đóng (Phase 5 closure) | **Thí nghiệm đã xong (10/11/2026)**; đang viết luận văn và bài báo ICCIES 2027 |
| Đọc trước | [Phần Study 1](#study-1-benchmark-và-tác-nhân-a0a6) | [Phần Study 2](#study-2-phòng-thủ-d3) |

## Bắt đầu từ đâu

| Bạn muốn | Mở |
|---|---|
| Biết dự án đang ở đâu | [knowledge/current_status.md](knowledge/current_status.md) |
| Xem toàn bộ bảng kết quả Study 2 | [docs/research/study2_thesis_tables.md](docs/research/study2_thesis_tables.md) |
| Hiểu vì sao từng quyết định được đưa ra | [docs/project/decision_log.md](docs/project/decision_log.md) |
| Lộ trình Study 2 | [docs/project/roadmap_v2_rebuild.md](docs/project/roadmap_v2_rebuild.md) |
| Chạy ở đâu, kết quả lưu ở đâu | [knowledge/rebuild_a_runbook.md](knowledge/rebuild_a_runbook.md) (mục "Bản đồ") |
| Notebook và Dataset Kaggle | [knowledge/kaggle_resources.md](knowledge/kaggle_resources.md) |
| Bài báo ICCIES 2027 | [docs/paper/iccies2027/README.md](docs/paper/iccies2027/README.md) |
| Mục lục tri thức dự án | [knowledge/README.md](knowledge/README.md) |

## Study 2: phòng thủ D3

**Bài toán.** Tác nhân đọc dữ liệu không tin cậy (email, tài liệu, trang web giả lập) rồi có thể gọi công cụ gửi ra ngoài
(`send_email_mock`, `post_webhook_mock`). Tấn công chèn chỉ dẫn vào dữ liệu để đẩy tác nhân làm lộ dữ liệu nhạy cảm qua
công cụ hoặc câu trả lời cuối. Sáu cơ chế tấn công M1–M6, năm biến thể ngôn ngữ (canonical, paraphrase, code-mix,
không dấu, tiếng Anh). Toàn bộ dữ liệu là tổng hợp; công cụ gửi chỉ là mock, không có I/O mạng.

**Các cấu hình so sánh.** A0 (không phòng thủ), P1 spotlighting, P2 sandwich, G1 Prompt Guard 2, MELON, Progent-lite,
R1 (từ Study 1), D2 (chính sách control/data), D2+P2, và **D3** = D2+P2 cộng luật đích gửi.

**Kết quả chính: Test-3 niêm phong** (48 family mới, 560 fixture mỗi cấu hình, chạy một lần 09–10/11/2026, gộp 3
backbone Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B):

| Cấu hình | Tấn công thành công (ASR) | Utility benign |
|---|---|---|
| A0 | 233/720 (32,4%) | 523/960 (54,5%) |
| D2+P2 | 27/720 (3,8%) | 480/960 (50,0%) |
| **D3** | **26/720 (3,6%)** | **490/960 (51,0%)** |

- D3 giảm ASR 28,7 điểm so với A0 (p Holm 5,0·10⁻⁵⁷) và giữ 93,7% utility benign của A0.
- So với D2+P2: utility tăng 1,0 điểm (p Holm 3,2·10⁻³), hại không tệ hơn (không kém hơn quá 2 điểm). Mức tăng nhỏ.
- Thống kê: McNemar chính xác trên cặp fixture, hiệu chỉnh Holm, CI 95% bootstrap theo family (10.000 lần).
- Ngoại kiểm phụ: Gemini 3 Flash trên Dev; AgentDojo v1.2.2 bản tiếng Anh và tiếng Việt (Llama, Gemini).

Chi tiết và hạn chế: [bảng luận văn Study 2](docs/research/study2_thesis_tables.md).

**Mã nguồn chính.**

| Thành phần | Vị trí |
|---|---|
| D3 | [src/react_agent/security_v3/d3.py](src/react_agent/security_v3/d3.py) |
| Chính sách control/data (D2) | [src/react_agent/security_v1/control_data_policy_v1.py](src/react_agent/security_v1/control_data_policy_v1.py) |
| Cấu hình chốt cho Test-3 | [configs/final/final_config_v4.json](configs/final/final_config_v4.json) |
| Phân loại cơ chế tấn công | [data/adversarial/v3_authoring/taxonomy.md](data/adversarial/v3_authoring/taxonomy.md) |
| Gemini qua proxy | [docs/omniroute_gemini_guide.md](docs/omniroute_gemini_guide.md) |

**Nhánh Git.** Công việc Study 2 làm trên `study2/d3-dev` rồi merge vào `main`; `study2/test3-seal` giữ trạng thái
niêm phong Test-3. Commit từ 23/10 đến 10/11/2026 đã đổi mã hash ngày 11/11; tra mã cũ → mới ở
[docs/project/commit_hash_map_2026-11-11.tsv](docs/project/commit_hash_map_2026-11-11.tsv).

## Study 1: benchmark và tác nhân A0–A6

- Phase 1–2: tác nhân A0, môi trường smoke, clean benchmark v1.1 (Kaggle).
  Xem [tiến độ clean v1.1](knowledge/clean_v11_progress.md).
- Phase 3: adversarial_v2, 350 attack + 350 benign, năm biến thể, Test đã khóa.
  Xem [nghiệm thu và giới hạn](docs/benchmark/adversarial_release_v2_summary.md).
- Phase 4: runtime artifact/provenance, metadata, hooks.
  Xem [báo cáo 12 DoD](docs/architecture/phase4_report.md).
- Phase 5: runtime A0–A6 và thí nghiệm API; đóng tháng 10/2026, các vấn đề còn lại chuyển sang Study 2.
- Pilot Gemma 4 / Qwen 7B: [báo cáo](docs/evaluation/measured_dev_pilot_report.md).
- Thiết kế dữ liệu: [clean_benchmark_design.md](docs/clean_benchmark_design.md),
  [clean_data_card.md](docs/clean_data_card.md).

## Nguyên tắc cốt lõi

- Chỉ dùng dữ liệu tổng hợp, không dữ liệu cá nhân thật.
- Email và webhook chỉ là mock, không có side effect mạng.
- Không lưu hidden chain-of-thought; chỉ lưu hành động và kết quả quan sát được.
- Test held-out được niêm phong trước khi chạy và không dùng để điều chỉnh hệ thống.
- GitHub là source of truth; Kaggle chỉ là inference worker.

## Cài đặt local

Yêu cầu Python 3.11 trở lên.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Kiểm tra:

```bash
python scripts/verify_setup.py
ruff check .
mypy src scripts
pytest
```

Smoke suite A0 trên CPU (replay backend, 20/20 tác vụ, đủ tám mock tool; kết quả ở `results/phase1/`, không commit):

```bash
python scripts/build_smoke_environment.py
python scripts/validate_smoke_data.py
python scripts/run_smoke.py --backend replay
```

## Tài liệu

- [Research contract](docs/project/research_contract.md) · [Invariants](docs/project/invariants.md) ·
  [Phase map](docs/project/phase_map.md)
- [Architecture](ARCHITECTURE.md) · [Team workflow](docs/project/team_workflow.md)
- [Decision log](docs/project/decision_log.md) · [Knowledge index](knowledge/README.md)

Không commit credential. Thư mục `credential kaggle/` chỉ giữ ở máy và bị `.gitignore` loại trừ.
