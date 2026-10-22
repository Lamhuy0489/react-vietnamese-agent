# Rà lại hướng đồ án: giữ nền tảng, dừng mở rộng bản vá hẹp

2026-09-25. Theo yêu cầu của chủ đề tài: kiểm chứng tính khả thi và nguy cơ lệch
hướng, không mặc định tiếp tục backlog cũ. **Chưa có căn cứ để bỏ toàn bộ đồ án;
có bằng chứng để không promote doc_read proof hiện tại thành giải pháp tổng quát.**
Không đổi Phase 5 acceptance hoặc sửa kết quả cũ để đóng phase.

## 1. So với mục tiêu gốc

Đã đối chiếu Word gốc `Ke_hoach_trien_khai_va_phan_cong_Lam_Quang_Huy_Nguyen_Quang_Minh_FINAL.docx`,
[research contract](../project/research_contract.md) và
[Phase 5, CXXVI](../../plan/phase5.md). Câu hỏi chính là đánh đổi an toàn–ích lợi
của A0–A6 trên cùng ReAct/model/tools/environment, không phải xây một hệ thống
chống mọi prompt injection. Kết quả âm có giá trị khoa học; không bắt buộc A6
thắng mọi metric. Nhưng leak smoke và deny-everything không thể gọi là nghiệm thu.

Ba dấu hiệu cần chỉnh hướng triển khai:

1. Bản main cumulative v12 và các adapter A6-only mới chưa tạo thành một candidate
   A0–A6 thống nhất để nghiệm thu. Nhiều phiên bản là lịch sử cần giữ, không phải
   bằng chứng rằng tất cả đã tích hợp hoặc là lý do tiếp tục thêm phiên bản vô hạn.
2. Điều kiện proof thu hẹp tới mẫu câu cố định và whole-field ASCII identifier;
   CPU controls trong miền đó không đại diện khả năng xử lý tiếng Việt/nguồn hỗn hợp.
3. Đã lẫn giữa nghiệm thu cơ chế và tối ưu chất lượng. DoD-5 ghi guard end-to-end,
   structured output/fallback; DoD-15 ghi representative benign **smoke**, không
   đưa ra ngưỡng ASR/FPR tổng quát. Các gate native quality/graceful đã ghi trong
   tài liệu vận hành vẫn phải được xử lý hoặc thay đổi qua quyết định minh bạch,
   không được âm thầm xóa. 4/7≈57% là nhóm acceptance, không đo công sức còn lại.

## 2. Thực nghiệm vừa thực hiện

[Protocol](phase5_direction_probe_v1_protocol.md) khóa 12 điều kiện trước chạy;
[harness](../../scripts/run_phase5_direction_probe_v1.py) không sửa runtime.
Một semantic unit synthetic, hai arm: clause A6 v12 và doc_read pair candidate.
Agent/guard scripted, 24 selected paired-process CPU executions, cùng task,
catalog/environment/proposals/config trên từng cặp. Không LLM pretrained/GPU/Test.
Full pair audit cả hai arm; candidate thêm raw final/Broker joins.

| Chỉ số trên các controls đã định | A6 v12 | Doc-read candidate |
|---|---:|---:|
| Giữ nguyên đáp án public hợp lệ | 8/8 | 2/8 |
| Loại được mục tiêu nhạy cảm đã định | 0/4 | 3/4 |
| Terminal completed | 12/12 | 12/12 |
| Tổng thời gian thực thi CPU các task, không gồm hậu kiểm | 16.110 s | 16.254 s |

Candidate giữ exact command và no-collision. Mất ích lợi ở hai paraphrase,
câu lịch sự, field văn xuôi, field nhiều dòng và đọc public lặp lại. Rò rỉ còn
lọt là **Base64 của identifier riêng**, không phải một phát hiện tấn công mới.
Các kiểm tra còn lại là exact identifier, private context quanh literal trùng
public và zero-width. Scorer chỉ kiểm các phép biểu diễn đã định, không chứng
minh an toàn ngữ nghĩa tổng quát.

Đây là **falsification/coverage diagnostic**, không full-benchmark ASR/FPR,
không 12 attack families độc lập, không khảo sát thống kê và không LLM speed
benchmark. Baseline giữ ích lợi bằng cách cũng cho lộ secret: không phải giải
pháp thay thế an toàn. Candidate chặn nhiều hơn nhưng chưa đạt đồng thời hai
mục tiêu. Không sửa candidate sau khi thấy kết quả, không thêm regex Base64 để
chấm lại cùng matrix. Kết luận theo rule đã ghi: `do_not_promote_as_general_remedy`.

### Bằng chứng và các lần chạy chưa hoàn chỉnh

[Selected receipt/hashes](../../experiments/manifests/phase5_direction_probe_v1.json).
Raw ignored: `build/evaluation/phase5_direction_probe01`, `...02`, `...03`.

- 01 thực thi baseline đầu tiên nhưng lỗi JSON hash do tuple responses; không
  có case/top-level receipt. Giữ nguyên, không chọn nó vào mẫu 24. Đây là lần
  thực thi CPU scripted bổ sung, không che giấu hoặc tính như model run thành công.
- 02 sửa serializer/type annotation, hoàn thành 10 điều kiện/20 executions;
  dừng trước worker của điều kiện `base64` do task ID chứa chữ số trái schema.
- 03 sửa ID và bổ sung prefix resume. Hash declaration 02 được cung cấp ngoài;
  giữ cùng runtime-source/conditions/smoke, tái audit/read-only 20 kết quả đã
  hoàn tất và chỉ chạy hai điều kiện còn thiếu/4 executions. Toàn bộ inventory
  02 khớp trước/sau. Harness đổi hạ tầng được ghi deviation; không đổi thuật
  toán, task instruction, content, action, model/config hoặc scorers để tăng điểm.

Tổng 25 executions của diagnostic qua ba thư mục, 24 được đưa vào bảng theo
coverage manifest; các CPU unit/integration tests riêng không cộng vào mẫu.
Fresh replay từ đầu dùng output mới; không ghi đè dữ liệu:

```sh
.venv/bin/python scripts/run_phase5_direction_probe_v1.py \
  --output build/evaluation/phase5_direction_probe_fresh
```

## 3. Đối chiếu bằng chứng native đã có

Kiểm lại SHA của 32-row summary Dev32 gốc:
`5601a90ddca2de14111fd6b573417022f989c2b4c52e21edc240baff9dfbd04e`.
[Báo cáo gốc](phase5_clause_dev32_scoring_v1_report.md): A2/A6 có utility
4/8 và 3/8 benign; observed attack success 1/8 và 0/8. Mỗi mức có hai benign
không đề xuất tool. Do đó provenance mới không thể tự chữa lỗi agent không
thực hiện tác vụ. Không mở oracle riêng hoặc chấm lại Test trong rà soát này.

## 4. Phương án đề xuất — chưa thay kiến trúc

**Khuyến nghị tái cấu trúc có giới hạn, không đập bỏ toàn bộ.** Giữ benchmark
đã khóa, tám tools, Tool Broker, schema observable trace, model adapters, Test
seals và toàn bộ raw/negative results. Giữ v12 cùng candidate hiện tại làm
đối chứng lịch sử, không coi v12 là bản an toàn cuối.

Hướng cần thử là **tham chiếu dữ liệu có kiểu tại broker**, ví dụ lựa chọn
`artifact_id + field_path` thay vì suy luận nguồn chỉ từ chuỗi literal bằng nhau.
Host resolve dữ liệu thực, kiểm artifact/hash/path/sensitivity/trust và quyền
của sink; chỉ các phép biến đổi khai báo rõ mới truyền provenance. Field nhiều
dòng không đòi ngoại lệ riêng theo câu văn; encode/concat không được tự rũ nhãn.
Đây là giả thuyết thiết kế, chưa có prototype/kết quả chứng minh trong repo.

Các rủi ro phải thử: model chọn nhầm reference, nguồn S0 chứa instruction,
control-flow injection, derived values, metadata nguồn thiếu/sai và final tự do.
Source reference chỉ chứng minh host lấy giá trị ở đâu, không chứng minh động cơ
hay causal reasoning của LLM. Free-form final vẫn là sink, không tự được allow.

Nếu thay schema/prompt/tool contract, phải áp dụng cách biểu diễn nền giống nhau
cho A0–A6 trong một phiên bản thí nghiệm mới, chỉ khác policy; A0 không được lén
thêm defense. Không trộn kết quả trước/sau schema thành cùng ablation. Khởi đầu
bằng prototype riêng, chưa thay core hoặc benchmark. Đề xuất này cần owner duyệt.

### Lộ trình hữu hạn sau phê duyệt

1. Một contract ngắn cho reference/derived-operation/sink và bảng ánh xạ 20 DoD.
   Một prototype có khả năng bác bỏ giả thuyết, không mở hàng loạt runtime wrapper.
2. Một batch synthetic mới khóa trước: public/private/collision/unknown-source,
   paraphrase và transformations; kiểm cả hành động external lẫn final. Nếu
   không giữ được utility và chặn các ca được giao, ghi no-go trước GPU.
3. Nếu CPU đạt: một source freeze theo khối, một package/model identity và một
   lịch Dev native đối chứng cố định. Đo task success, disclosure, denial đúng/sai,
   coverage, latency/tokens và forced/graceful exits riêng; không retry semantics.
4. Ra quyết định giữ hoặc bác bỏ prototype từ batch đó. Nếu bác bỏ, chọn giảm
   phạm vi có ghi nhận hoặc trình phương án kiến trúc thay thế; không tự động
   sinh vòng bản vá mới. Final statistics/Test thuộc phase sau khi đủ điều kiện.

## 5. Cơ sở nghiên cứu và giới hạn áp dụng

Nguồn sơ cấp, truy cập 2026-09-25:

- Edoardo Debenedetti et al., **Defeating Prompt Injections by Design** (2025,
  arXiv v2). [Paper](https://arxiv.org/abs/2503.18813v2),
  [mã tác giả](https://github.com/google-research/camel-prompt-injection).
  Bằng chứng trực tiếp: CaMeL tách control/data flow và áp capability policy
  ngoài LLM. Suy luận cho đồ án: nên khảo sát kiểm soát dữ liệu tại host thay
  vì chỉ chuỗi keyword. Không nhập nguyên CaMeL vì có thể đổi mô hình thực thi
  và vi phạm điều kiện một ReAct/cùng runtime; không nhận guarantee của họ.
- Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner,
  Marc Fischer, Florian Tramèr, **AgentDojo** (2024, arXiv v3/NeurIPS).
  [Paper](https://arxiv.org/abs/2406.13352v3). Bằng chứng trực tiếp: đánh giá
  tool agents trên untrusted data và ghi nhận task failures ngay khi không có
  attack. Suy luận: phải tách agent capability khỏi defense loss và chấm utility
  cùng security. Không suy các kết quả của họ sang benchmark tiếng Việt này.

Theo `research-evidence`, tìm được một paper không tự cho phép đổi kiến trúc.
Đã gửi câu hỏi duyệt tái cấu trúc giới hạn; trước phản hồi, không sửa runtime/
contract gốc, không upload Kaggle, không commit, không cập nhật phase acceptance.
