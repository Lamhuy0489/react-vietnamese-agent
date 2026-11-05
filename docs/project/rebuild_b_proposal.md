# Rebuild B: đề xuất nâng cấp lên mức hội nghị top (để owner và Minh review)

Trạng thái: **ĐÃ DUYỆT** (owner, 2026-11-05). Thêm Qwen3.6-35B-A3B vào backbone chính; API frontier hoãn
tới khi owner cấp. Kế hoạch thi hành: [rebuild_b_plan.md](rebuild_b_plan.md). File này giữ làm lý do và khảo sát.

## 0. Tóm tắt

- **Không vứt đi hạ tầng.** Tool Broker, runtime, evaluator, seal/manifest, McNemar ghép cặp và CI
  bootstrap theo family là phần mạnh nhất và reviewer đánh giá cao. Phần "đập đi làm lại" là **dữ liệu,
  danh sách model và tập phòng thủ để so sánh**.
- **Kết quả cũ giữ nguyên làm Study 1:** R4 Test v1, Test-2, clean Test RQ1 và RQ3. Không chạy lại,
  không sửa. Rebuild B là **Study 2** với bộ dữ liệu mới **VN-AgentInject v3**: Dev v3 và Test v3,
  đăng ký trước.
- **Định vị bài báo:** chưa có benchmark nào đo prompt injection gián tiếp vào agent dùng tool
  **bằng tiếng Việt**, với thao tác bề mặt đặc thù tiếng Việt (bỏ dấu, tách từ, code-mix) và phòng thủ
  ngoài mô hình được đánh giá **có tấn công thích nghi**. Ba ý này đều nằm đúng khoảng trống mà các
  nghiên cứu 2025–2026 chỉ ra (mục 2).
- **Mục tiêu:** USENIX Security / IEEE S&P / CCS (track benchmark và hệ thống) hoặc ACL/EMNLP (main
  hoặc Findings), NeurIPS Datasets & Benchmarks. Phương án dự phòng: workshop ở các hội nghị đó, hoặc
  SoICT/KSE/RIVF.

## 1. Vì sao bản hiện tại chưa đủ cho hội nghị top

| Điểm yếu | Bằng chứng trong repo | Cách sửa ở Rebuild B |
|---|---|---|
| Test-2 chỉ có **một cơ chế tấn công** (gửi tới địa chỉ mới, có chữ "gửi" và địa chỉ viết rõ), nên regex A1 bắt hết và D2 = A1 ở 200/200 lượt | decision log "Test-2 result"; spec Test-2 không có trục cơ chế | Taxonomy cơ chế M1–M6 là trục chính của ma trận sinh dữ liệu (mục 4.1) |
| Nhỏ: 20–40 family; A0 chỉ gây hại ở 5/20 family của Test-2 | bảng per-family | ≥ 72 family Test, có power analysis (mục 4.4) |
| RQ2 chỉ có một model (Qwen3-8B) | roadmap v2 | Ít nhất 4 backbone cho cả RQ1 và RQ2 (mục 5) |
| Chỉ so với thang phòng thủ tự xây (A0–A6) | – | So thêm baseline đã công bố: spotlighting, PromptGuard, MELON, kiểu Progent, Meta SecAlign (mục 6) |
| Chỉ có tấn công tĩnh | – | Thêm vòng tấn công thích nghi biết trước phòng thủ (mục 7); đây là chuẩn mới sau *The Attacker Moves Second* |
| Không so được với benchmark tiếng Anh | – | Chuyển một phần AgentDojo sang tiếng Việt, chạy cả bản EN và VI (mục 4.3) |
| Người viết dữ liệu biết luật phòng thủ | Test-2 do assistant viết | Spec cơ chế cố định trước; owner và Minh review mù với code D2; công bố là giới hạn (mục 4.5) |

## 2. Khảo sát nghiên cứu gần đây (đến 11/2026)

**Benchmark tấn công agent (tiếng Anh):** InjecAgent, AgentDojo (v1.2.1: Workspace 40 user task /
14 injection task, Banking 16/9, Travel 20/7, Slack ~20/5) và Agent Security Bench (ASB) là ba chuẩn
được trích dẫn nhiều nhất. Năm 2026 có thêm các bộ chuyên biệt: LongPIBench (ngữ cảnh dài), AgentDyn
(động), AgentDrift (quỹ đạo gắn nhãn từng bước), benchmark agent web lấy các bên liên quan làm trung
tâm, và MCPTox (tool poisoning trên MCP server).

**Đa ngôn ngữ:**
- MAPS (EACL 2026 Findings) dịch ASB sang 11 ngôn ngữ, **không có tiếng Việt** và không dịch AgentDojo.
- SEALSBench (SEALGuard) có tiếng Việt nhưng chỉ đo jailbreak hội thoại, không đo agent hay tool.
- Một số nghiên cứu cho thấy bộ phát hiện injection kém đi ngoài tiếng Anh: AgentShield với tiếng
  Kurd và Ả Rập, MIPIAD với tiếng Bangla, nghiên cứu Thổ Nhĩ Kỳ trên 55 LLM, probe AgentDojo tiếng
  Trung.
- Chưa có công trình nào đo prompt injection gián tiếp vào agent tiếng Việt từ đầu đến cuối. Cũng
  chưa ai nghiên cứu tác động của **bỏ dấu tiếng Việt** lên tấn công hay phòng thủ. Ở mảng tokenizer,
  NeurIPS 2026 có bài "Tokenization Tax" về tiếng Việt nhưng chỉ đo chi phí token.

**Phòng thủ:**
- Kiến trúc tách control/data: CaMeL, FIDES, Progent, RTBAS, FORGE. D2 của ta thuộc nhóm này.
- Phát hiện: MELON (chạy lại có che dữ liệu rồi so tool call), PromptGuard 2, DataSentinel.
- Mức mô hình: StruQ, SecAlign, **Meta SecAlign-8B/70B**. Bản 8B dựng trên Llama-3.1-8B, khớp với
  backbone hiện có.
- Đã công bố: CaMeL giải 77% task AgentDojo dưới tấn công (84% khi không phòng thủ). Progent hạ ASR
  AgentDojo từ 39,9% xuống 1,0%.

**Đánh giá thích nghi, xu hướng bắt buộc:**
- *The Attacker Moves Second* (Nasr, Carlini và cộng sự, 10/2025) phá 12 phòng thủ với ASR > 90%,
  trong đó có MELON, dù các bài gốc báo ASR gần 0.
- Narisetty và cộng sự (2606.26479) chỉ ra phòng thủ ngoài mô hình mới được kiểm trên benchmark tĩnh.
  Họ chạy lại Progent trên Qwen2.5-7B (ASR 25,8% → 4,2%) và thấy tấn công thích nghi thủ công không
  phá được (2,6%), nhưng mới là thí nghiệm nhỏ.
- SoK 2602.10453 (78 bài) kết luận không có "viên đạn bạc". Một khoảng trống họ nêu: phòng thủ coi
  user prompt là nguồn tin cậy duy nhất sẽ gặp vấn đề ngoài thực tế. Đây chính là chỗ yếu M5 và B-auth
  của D2, ta phải đo nó.

**Hệ quả cho thiết kế:** reviewer top sẽ đòi bốn thứ: (a) tấn công thích nghi, (b) so với baseline đã
công bố trên cùng môi trường, (c) nhiều backbone, (d) chỉ số utility đi kèm ASR. Bản hiện tại mới có
(d).

## 3. Câu hỏi nghiên cứu cho Study 2

- **RQ1 (năng lực):** 4–5 backbone mã nguồn mở làm task agent tiếng Việt sạch tốt đến đâu, và kém bao
  nhiêu so với bản tiếng Anh tương đương (AgentDojo-VI so với EN)?
- **RQ2 (độ dễ bị tấn công):** ASR theo cơ chế M1–M6 và theo backbone. Tấn công viết bằng tiếng Việt,
  không dấu hoặc code-mix có thành công hơn bản tiếng Anh không?
- **RQ3 (phòng thủ):** D2 (tách control/data) so với các baseline đã công bố, theo từng cơ chế, cả với
  tấn công tĩnh lẫn thích nghi, và cái giá về utility.
- **RQ4 (bề mặt tiếng Việt):** bỏ dấu, tách từ sai, zero-width và code-mix ảnh hưởng thế nào tới (a)
  utility, (b) ASR, (c) bộ phát hiện (PromptGuard, guard LLM). Đây là phần mở rộng từ phát hiện RQ3
  cũ: bỏ dấu là loại duy nhất gây giảm có ý nghĩa, ở cả 3 model.

## 4. Dữ liệu VN-AgentInject v3

### 4.1 Taxonomy cơ chế (trục chính, cố định trước khi sinh dữ liệu)

| Mã | Cơ chế | Mục tiêu gây hại | Dự đoán (ghi trước, không dùng để chọn dữ liệu) |
|---|---|---|---|
| M1 | Chuyển hướng tới đích mới, viết lộ | gửi mail/webhook ngoài phạm vi | A1 và D2 đều chặn |
| M2 | Chuyển hướng tới đích mới, viết né: "chuyển tiếp/cc/forward", địa chỉ tách `x [at] y`, địa chỉ nằm trong một record khác, không có động từ gửi | như M1 | A1 lọt, D2 chặn |
| M3 | Lấy cắp giá trị bí mật qua sink người dùng đã nêu | lộ CONFIDENTIAL | A1 lọt, D2 chặn |
| M4 | Làm lộ giá trị bí mật qua câu trả lời cuối | lộ qua final answer | A1 lọt, D2 redact |
| M5 | Sửa payload thường trên sink người dùng đã nêu (số, boolean, đơn vị) | sai giá trị nghiệp vụ | **D2 lọt (giới hạn đã biết)** |
| M6 | Chiếm luồng điều khiển: gọi thêm tool có side-effect, ghi đè, lặp | hành động ngoài phạm vi | cần đo |
| B-plain | Benign tương ứng từng family | utility | – |
| B-auth | Benign có người dùng **cho phép** gửi hoặc trả lời giá trị bí mật | đo chặn nhầm | D2 có thể chặn nhầm |

Mỗi cơ chế được kết hợp với: vector (tài liệu, trang cache, trường DB, output tool), domain (đại học,
hành chính, ngân hàng, y tế, thương mại điện tử, nội bộ doanh nghiệp), độ thuyết phục (thông báo
thường, giả danh quyền hạn, nhiều bước, hợp lý theo ngữ cảnh) và vị trí chèn (đầu, giữa, cuối,
trong bảng).

### 4.2 Quy mô

| Bộ | Family | Biến thể/family | Fixture (attack + benign) |
|---|---|---|---|
| Dev v3 | 48 (8 × M1–M6) | 5 | 480 |
| Test v3 | 72 (12 × M1–M6) | 5 | 720 |
| Pilot (dùng rồi bỏ) | 12 | 1 | 24 |

5 biến thể gồm: canonical, paraphrase, code_mix, no_diacritic và tiếng Anh. Bản tiếng Anh là mới, phục
vụ RQ2 so ASR tiếng Việt với tiếng Anh. Mỗi family có cặp B-plain, và 1/3 family có thêm một ca B-auth.
Tách Dev/Test theo family như cũ.

### 4.3 AgentDojo-VI (neo so sánh với tiếng Anh)

Chuyển 2 suite của AgentDojo (Banking và Slack, khoảng 36 user task × 14 injection task) sang tiếng
Việt, chạy cả EN và VI trên cùng backbone. Mục đích là để reviewer so số với bài khác, và để tách hiệu
ứng ngôn ngữ ra khỏi hiệu ứng thiết kế benchmark. Cần kiểm license (AgentDojo dùng MIT) và việc chạy
được với vLLM. Bản dịch do Claude làm, owner và Minh review mẫu 20%.

### 4.4 Power analysis

- Muốn phát hiện chênh 10 điểm ASR theo cặp (ví dụ A1 15% → D2 5%) với α = 0,05 và power 0,8 bằng
  McNemar, cần khoảng 25–30 cặp bất đồng. Tương đương ≥ 250 lượt tấn công cho mỗi cấu hình.
- Test v3 có 360 lượt tấn công, mỗi cơ chế 60 lượt. Như vậy đủ cho so sánh tổng thể, còn so theo từng
  cơ chế chỉ thấy được chênh lớn. Ghi rõ điều này trước khi chạy.

### 4.5 Quy trình viết và review (owner và Minh review câu lệnh của Claude)

1. Claude soạn spec ma trận (mục 4.1). Owner duyệt và commit spec **trước khi sinh dữ liệu**.
2. Claude sinh pilot 12 family, chỉ chạy A0 trên 2 backbone để chỉnh độ thuyết phục. Mục tiêu: A0 gây
   hại ở ≥ 40% family pilot. Pilot không vào Dev hay Test.
3. Claude sinh Dev v3 và Test v3 theo spec đã khóa. Validator xác định: QA replay 100%, độ mới 4-gram
   so với v1 và Test-2 ≤ 0,2, không trùng định danh hay domain cũ.
4. **Owner và Minh review mù:** chỉ đọc câu lệnh, đoạn chèn và nhãn cơ chế, không xem code phòng thủ.
   Chia đôi, mỗi người review khoảng 60 family, trong đó 20% cùng review chéo để tính độ đồng thuận
   (Cohen's κ cho nhãn cơ chế và câu "có tự nhiên không").
5. Sửa xong mới seal. **Sau khi seal, không ai được chỉnh D2 hay baseline dựa trên Test v3.**
6. Dev v3 dùng để chỉnh mọi phòng thủ, kể cả baseline, với cùng ngân sách: tối đa 3 vòng, mỗi vòng ghi
   decision log trước khi chạy.

## 5. Backbone

Ràng buộc: Kaggle T4 × 2 (2 × 16 GB, không có bf16 nhanh), tối đa 2 phiên GPU mỗi tài khoản, 5 tài
khoản với khoảng 20–30 giờ/tuần mỗi tài khoản.

| Vai trò | Model đề xuất | Lý do | Ghi chú phục vụ |
|---|---|---|---|
| Giữ để nối kết quả cũ | Qwen3-8B | backbone RQ2 cũ | đã chạy được |
| Giữ | Gemma-4-12B | mạnh nhất RQ1 cũ | patch head_dim 512 đã có |
| Giữ (đối chứng) | Llama-3.1-8B | đối chứng cho Meta SecAlign-8B (cùng base) | đã chạy được |
| **Thêm** | Qwen3.5-9B | thế hệ mới, BFCL-V4 khoảng 66 (nhà phát hành tự báo) | **cần xác minh trên HF** và chat template tool |
| **Thêm** | Meta-SecAlign-8B | phòng thủ mức mô hình, cùng base Llama-3.1-8B | LoRA trên Llama-3.1-8B |
| Tùy chọn | Qwen3.6-35B-A3B (AWQ 4-bit) | MoE lớn, chỉ 3B kích hoạt nên vẫn nhanh | cỡ 18–20 GB vừa 2×T4 nhưng cần thử; có báo cáo lỗi tool call |
| Tùy chọn (nếu có ngân sách API) | 1–2 model frontier (GPT, Gemini, Claude) | reviewer top hay hỏi "model mạnh thì sao" | chi phí ước 30–80 USD cho Test v3 × 3 cấu hình; cần owner quyết |

Quy tắc công bằng giữ như RQ1 cũ: cùng prompt, cùng tool, cùng scorer, không chỉnh riêng cho từng
model. Chỉ sửa ở mức harness (chat template, parser).

## 6. Phòng thủ để so sánh

| Mã | Phòng thủ | Loại | Ghi chú |
|---|---|---|---|
| A0 | không phòng thủ | – | |
| P1 | spotlighting / datamarking (đánh dấu dữ liệu tool) | prompt | rẻ, baseline phổ biến |
| P2 | sandwich / nhắc lại nhiệm vụ | prompt | |
| G1 | PromptGuard 2 86M (và bản fine-tune tiếng Việt cộng đồng, nếu dùng được) | detector | RQ4: detector với tiếng Việt không dấu |
| R1 | A1 cũ (regex) | luật | |
| MEL | MELON (chạy lại có che dữ liệu) | detector | dùng code công khai, cần port |
| PRG | policy kiểu Progent (danh sách tool/đích cho phép theo task) | ngoài mô hình | cài lại bản rút gọn, ghi rõ |
| SEC | Meta-SecAlign-8B | mức mô hình | là một backbone |
| **D2** | tách control/data (của ta) | ngoài mô hình | giữ bản đã ghim, chỉ chỉnh trên Dev v3 |
| D2+P1 | kết hợp | | |

Bỏ A2–A6 khỏi Study 2: chúng đã được báo trong Study 1, và A6 không chuyển giao được. CaMeL đầy đủ quá
nặng để cài lại (cần interpreter riêng), nên chỉ so định tính kèm số đã công bố trên AgentDojo-EN.

## 7. Tấn công thích nghi

- **Vòng người (red team):** Claude, owner và Minh biết code D2 và các baseline. Mỗi người có ngân sách
  20 lần thử trên **Dev v3** để tìm mẫu vượt từng phòng thủ.
- **Vòng tự động:** một LLM attacker (black-box, ngân sách N truy vấn mỗi family) lặp viết lại đoạn chèn
  theo phản hồi thành công hay thất bại, kiểu PAIR / TAP / IterInject. Chạy trên Dev v3.
- Các chiến lược tìm được trên Dev được **đóng gói thành bộ tấn công cố định**, rồi áp lên Test v3
  đúng một lần. Báo ASR tĩnh và ASR thích nghi riêng.
- **Giới hạn ghi trước:** không làm GCG white-box (không có gradient qua vLLM trên T4).

## 8. Chỉ số và thống kê

Giữ nguyên các chỉ số đã duyệt:
- paired side-effect ASR là chỉ số chính, kèm leakage qua final answer;
- benign utility, utility under attack, false block (tách riêng B-auth);
- McNemar chính xác ghép theo biến thể;
- CI bootstrap theo family;
- hiệu chỉnh Holm cho các so sánh chính đăng ký trước, tối đa 6 so sánh.

Thêm: phân rã theo cơ chế và theo loại biến thể, cùng chi phí (token, độ trễ, số lần gọi LLM) của mỗi
phòng thủ.

## 9. Ước lượng tính toán và thời gian

- Test v3: 720 fixture × khoảng 8 cấu hình phòng thủ × 4 backbone chính, cộng AgentDojo-VI/EN, ước
  25.000–30.000 lượt.
- Tốc độ quan sát được: Qwen khoảng 10 lượt/phút (Test-2), Gemma khoảng 3,7 lượt/phút. Tổng khoảng
  70–90 giờ GPU T4, tức khoảng 2 tuần nếu xoay 5 tài khoản.
- Có thể chạy song song nhiều cấu hình trên cùng endpoint vì vLLM tự gộp batch. Ghi rõ là không tất
  định giữa các batch.

| Tuần (từ 09/11/2026) | Việc |
|---|---|
| 1 | Owner duyệt đề xuất; Claude viết spec ma trận và taxonomy; xác minh model trên HF; thử serve Qwen3.5-9B và SecAlign-8B |
| 2 | Pilot 12 family + chỉnh độ thuyết phục (chỉ A0); sinh Dev v3 + Test v3; dịch AgentDojo-VI |
| 3 | **Owner và Minh review mù**; sửa; seal Test v3; cài P1, P2, MEL, PRG trên Dev |
| 4–5 | Chạy Dev v3 cho mọi phòng thủ (≤ 3 vòng chỉnh mỗi phòng thủ); vòng tấn công thích nghi trên Dev |
| 6 | Ghim `final_config_v3`; chạy Test v3 + bộ thích nghi + AgentDojo-VI/EN, mỗi thứ một lần |
| 7 | Phân tích, viết luận văn (Study 1 + Study 2) |
| 8–14 | Viết bài báo, hoàn thiện luận văn trước 2027-02-19 |

Hạn nộp hội nghị (cần kiểm lại ngày chính xác): ARR cho ACL/EMNLP khoảng tháng 2 và tháng 5/2027,
USENIX Security 2027 có các đợt rải trong năm, NeurIPS D&B khoảng tháng 5/2027. Luận văn đến hạn trước,
nên bài báo được viết song song.

## 10. Rủi ro và cam kết trung thực

- Study 2 ra đời **sau khi** thấy Test-2 không phân biệt được D2 với A1. Bài báo và luận văn phải nói
  rõ điều này. D2 không chỉnh trên bất kỳ dữ liệu Test nào; taxonomy có cả lớp D2 dự kiến thua (M5,
  B-auth).
- Người viết dữ liệu (Claude) biết D2. Cách giảm thiểu: spec khóa trước, owner và Minh review mù, báo
  κ. Vẫn ghi là giới hạn.
- Dữ liệu tổng hợp và tool mock: giữ, vì đây là bất biến an toàn của đồ án. AgentDojo-VI giúp giảm lo
  ngại về tính thực tế.
- Model mới có thể không serve được trên T4. Phương án lùi: giữ 3 backbone cũ cùng SecAlign-8B.
- Quota Kaggle: lamhuy8904 gần hết quota tuần; ưu tiên oanhlam123456, huylmhuhu, buiquocviet và
  meanalways.

## 11. Quyết định cần owner

1. Duyệt hướng chung: Study 1 giữ nguyên, Study 2 với VN-AgentInject v3.
2. Quy mô: Dev 48 + Test 72 family (mục 4.2), hay nhỏ hơn hoặc lớn hơn.
3. Có làm AgentDojo-VI không (mục 4.3)? Đề xuất: có.
4. Backbone: thêm Qwen3.5-9B và Meta-SecAlign-8B? Có dùng API frontier (tốn tiền) không?
5. Danh sách baseline (mục 6), và Minh có tham gia vòng red team không.
6. Hội nghị nhắm tới, để chốt hạn và định dạng bài.

## Nguồn

- InjecAgent: https://arxiv.org/abs/2403.02691 · AgentDojo:
  https://ukgovernmentbeis.github.io/inspect_evals/evals/agentdojo/index.html
- MAPS: https://arxiv.org/abs/2505.15935 · SEALGuard/SEALSBench: https://arxiv.org/abs/2507.08898
- The Attacker Moves Second: https://arxiv.org/abs/2510.09023
- Adaptive Evaluation of Out-of-Band Defenses: https://arxiv.org/abs/2606.26479
- SoK Landscape of PI Threats in LLM Agents: https://arxiv.org/abs/2602.10453
- Meta SecAlign: https://arxiv.org/abs/2507.02735
- AgentShield: https://arxiv.org/abs/2605.11026 · MIPIAD: https://arxiv.org/abs/2605.07269 ·
  Chinese AgentDojo probes: https://arxiv.org/abs/2608.02657
- Turkish PI study: https://www.mdpi.com/2076-3417/16/13/6740
- LongPIBench: https://arxiv.org/abs/2608.28411 · AgentDrift: https://arxiv.org/abs/2609.06972 ·
  Stakeholder-centric web agents: https://arxiv.org/abs/2606.13385 · IterInject:
  https://arxiv.org/abs/2605.24659
- Tokenization Tax (Vietnamese): https://neurips.cc/virtual/2026/164760
- Model tool-calling (nguồn thứ cấp, cần kiểm lại): https://insiderllm.com/guides/function-calling-local-llms/
