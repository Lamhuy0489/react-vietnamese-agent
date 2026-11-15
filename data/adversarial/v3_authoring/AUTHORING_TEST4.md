# Test-4 và gắn nhãn Dev v4: hướng dẫn cho owner và Minh

Trang này giao việc cho hai người viết (owner, Minh) trong bản mở rộng BrokerGuard v3 cho tạp chí Q4. Bối cảnh nằm ở
[`brokerguard_v3_extension_design.md`](../../../docs/project/brokerguard_v3_extension_design.md) và decision log các mục
2026-11-15 15:30, 15:45 và 16:30. Định dạng canonical lấy từ [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md), còn trục và
cơ chế lấy từ [`taxonomy.md`](taxonomy.md). Trang này chỉ nêu phần mới.

Có ba việc, làm theo đúng thứ tự:

| Bước | Việc | Ai làm | Xong khi |
|---|---|---|---|
| A | Viết quy tắc gắn nhãn độ nhạy, gắn nhãn Dev v4, viết errata | Owner và Minh | Có quy tắc, có κ, có errata |
| B | Soạn Test-4 phần tĩnh: 48 họ `T5_*` | Owner và Minh | `check` và `qa` sạch, đã review chéo |
| C | Soạn Test-4 phần thích nghi nhắm vào v1 | Owner và Minh | Có file riêng, đã review chéo |
| D | Niêm phong Test-4, đăng ký trước giả thuyết | Claude, owner duyệt | Hash nằm trong decision log |

Claude chỉ làm hạ tầng: script kiểm, đếm, hash và niêm phong. **Claude không đọc nội dung tấn công hay nội dung Test.**
Code v3 chỉ được viết sau bước D.

---

## Luật chung (áp dụng cho cả A, B và C)

- **Viết độc lập với phòng thủ.** Không đọc `src/react_agent/security_v1/` hay `src/react_agent/security_v3/`. Không đọc
  các mục D2/D3/v3 trong decision log, kết quả trong `results/` hay bản thiết kế v3 ở mức chi tiết code. Biết hướng
  chung của v3 thì được, nhưng không soạn họ nào để v3 thắng.
- **Dữ liệu giả.** Đích dùng `@example.test` hoặc `mock://…`. Bí mật dùng `SYNTH-…`.
- **Mới so với mọi bộ cũ.** Tên họ, định danh `AWB_…`/`AUX_…`, đích, domain và bí mật `SYNTH-…` không được trùng pilot,
  Dev v4 (`release_dev4`, gồm cả Test-I và Test-II cũ), `release_v2` hay `release_test2`. Jaccard 4-gram phải ≤ 0,2.
- Không đưa nội dung Test-4 cho công cụ AI bên ngoài và không gửi cho Claude đọc.
- **Không commit file Test-4 trước khi niêm phong.** File được commit cùng lúc với seal.

---

## A. Quy tắc gắn nhãn độ nhạy và sửa Dev v4

**Vì sao cần.** Ở v1, 25/40 ca lọt qua là do giá trị mật nằm trong một nguồn gắn nhãn công khai (`S0`). Bản v3 gắn nhãn
theo từng giá trị, nên nhãn của dữ liệu phải đúng và nhất quán. Nếu sửa nhãn sau khi đã biết v3 chặn được gì, reviewer
sẽ nghi sửa để v3 thắng. Vì vậy **quy tắc phải được viết trước, rồi mới áp dụng.**

### A1. Viết quy tắc

Tạo file `data/adversarial/v3_authoring/labelling_rules_v4.md` và chốt trước khi gắn nhãn. Quy tắc cần trả lời:

1. **Loại giá trị nào là mật.** Ví dụ, loại nào trong các nhóm sau được tính là mật: mật khẩu, OTP, mã truy cập hoặc
   token, số tài khoản hay thẻ, mã định danh cá nhân, điểm số, mức lương, ghi chú y tế, địa chỉ riêng.
2. **Đơn vị gắn nhãn** là từng giá trị (một chuỗi cụ thể trong nguồn), không phải cả nguồn.
3. **Nhãn của nguồn được suy ra từ giá trị.** Một nguồn có ít nhất một giá trị mật thì nguồn đó là `S2`.
4. **Ca biên.** Giá trị chính người dùng đã viết trong yêu cầu. Giá trị đã che một phần, ví dụ 4 số cuối. Giá trị công khai
   theo ngữ cảnh, ví dụ email của phòng ban.
5. **Độ tin là chiều riêng.** Nhãn độ tin (`T0/T1/T2`) không đổi theo nhãn độ nhạy.

### A2. Gắn nhãn hai người, độc lập

- Owner và Minh **mỗi người gắn riêng** theo A1, không trao đổi trong lúc gắn. Đối tượng là mọi nguồn của 168 họ Dev v4.
- Claude sẽ tạo phiếu gắn nhãn dạng CSV. Phiếu chỉ có mã họ, mã nguồn, nhãn hiện tại và hai cột trống cho hai người.
  Người gắn tự mở fixture để đọc. Phiếu chưa có, cứ báo Claude khi sẵn sàng.
- Claude tính hệ số Cohen's κ từ hai cột. Hai người bàn với nhau để chốt các ca lệch. Ghi lại số ca lệch trước khi bàn.

### A3. Errata

- Mỗi thay đổi so với nhãn cũ ghi một dòng vào `data/adversarial/v3_authoring/dev4_errata.csv` với các cột
  `family_id, source_id, field, old, new, rule, note`. Cột `rule` là số mục quy tắc ở A1.
- Ngoài nhãn, chỉ sửa **lỗi dữ liệu thật**, ví dụ oracle sai hoặc thiếu literal. Không viết lại câu tấn công.
- Claude dựng bản Dev mới `release_dev4_1` từ errata. Bản `release_dev4` đã niêm phong giữ nguyên. Sau đó Claude chạy lại
  các mốc A0 và v1 trên bản mới.

**Cùng quy tắc A1 được dùng để gắn nhãn Test-4** ở bước B.

---

## B. Test-4 phần tĩnh: 48 họ `T5_*`

Đây là phần dùng cho **giả thuyết chính**. Cách viết giống hệt Test-3, chỉ khác những điểm sau.

- **Danh sách họ:** [`spec_test4.json`](spec_test4.json) có 48 dòng từ `T5_01` đến `T5_48`.
  - Mỗi cơ chế M1–M6 có 8 dòng. Có 16 dòng mang `b_auth = true`.
  - Mỗi dòng đã định sẵn cơ chế, chi tiết, vector, mức thuyết phục, vị trí, giọng, cấu trúc, ràng buộc, lĩnh vực, loại
    sink và có B-auth hay không. Viết đúng theo dòng, không đổi cột.
  - Kiểm spec bằng lệnh: `.venv/bin/python scripts/build_test4_spec.py check`.
- **File cần viết:** `data/adversarial/v3_authoring/test4_canonicals.json`. Đây là một mảng JSON 48 phần tử, có cùng các
  trường như `test3_canonicals.json`. Trường `spec_id` là `T5_xx`.
- **Biến thể:** viết `canonical`, `paraphrase` và `english` cho `instruction`, `attack` và `benign`. Với họ có `b_auth`,
  viết thêm `auth.instruction`. Hai biến thể `code_mix` và `no_diacritic` do code sinh.
- **Nhãn độ nhạy** của nguồn và giá trị theo quy tắc A1.
- **Viết theo phân loại cơ chế** trong `taxonomy.md`. Phần này **không** nhắm vào luật của v1 hay v3. Họ nào được viết
  với ý nhắm vào phòng thủ thì chuyển sang phần C.

**Lệnh kiểm.** Hai lệnh dưới đây chưa có, Claude sẽ viết khi bạn bắt đầu soạn. Chúng chỉ in số đếm và mã họ, không in nội
dung.

```bash
.venv/bin/python scripts/check_release_test4_v1.py check --per-family   # liệt kê mọi họ lỗi
.venv/bin/python scripts/check_release_test4_v1.py qa                   # + replay an toàn và độ mới so với Dev v4
```

Lỗi hay gặp giống Test-3, xem `AUTHORING_TEST3.md`. Thường là bản `paraphrase` hoặc `english` thiếu literal, hoặc văn
bản code-mix chưa đủ từ trong glossary.

**Review chéo:** dùng phiếu 5 mục ở `taxonomy.md` §7. Người này review họ của người kia.

---

## C. Test-4 phần thích nghi nhắm vào v1

- **Mục đích:** đo xem v3 có vá được các lỗ hổng đã biết của v1 hay không. Phần này **báo riêng**, không vào giả thuyết
  chính, vì nó được dựng để v1 thua.
- **Được biết:** luật v1 ở mức mô tả trong bài báo (R-Dest, R-Flow, R-Redact, R-Signal, Mệnh đề 1) và ba loại lỗ hổng ở
  Mục 7:
  - giá trị mật trong nguồn gắn nhãn công khai;
  - đích có trong yêu cầu, ví dụ trong câu cấm hoặc trùng chuỗi con;
  - sửa tham số.
- **Không được biết:** code v3, vì code v3 chưa tồn tại và sẽ không tồn tại trước bước D.
- **Quy mô đề xuất:** 24 ca, mỗi loại lỗ hổng 8 ca, dựng trên các họ `T5_*` của phần B. Owner chốt lại số này.
- **File và định dạng:** `data/adversarial/v3_authoring/test4_adaptive.json`, cùng định dạng với
  `adaptive_attacks.json` của Dev (khóa là mã họ). Claude sẽ viết lệnh kiểm theo mẫu `check_adaptive_fixtures_v1.py`.

---

## D. Niêm phong (Claude làm, owner duyệt)

1. `check` và `qa` sạch cho phần B. Lệnh kiểm phần C sạch. Phiếu review chéo đã xong.
2. Claude ước lượng lực thống kê trên Dev v4, để xem 48 họ có đủ phát hiện mức chênh dự kiến giữa v3 và v1 không. Nếu
   không đủ, owner quyết thêm họ trước khi niêm phong.
3. Đăng ký trước vào decision log: giả thuyết, cấu hình (A0, Sandwich, Progent\*, v1, v3, các bản loại bỏ), chỉ số và
   phép thử (McNemar mức họ, Holm). Phần C được ghi là phân tích riêng.
4. Claude dựng release Test-4, ghi hash vào decision log, rồi commit nội dung cùng seal.
5. Sau bước này mới viết code v3 trên Dev v4.

## Trạng thái các công cụ

| Công cụ | Trạng thái |
|---|---|
| `spec_test4.json` và `scripts/build_test4_spec.py` | Có |
| `release_dev4` (168 họ, Dev-val 42) và `scripts/build_dev_pool_v4.py` | Có, đã niêm phong |
| Phiếu gắn nhãn CSV và script tính κ | Claude viết khi A1 xong |
| `check_release_test4_v1.py` | Claude viết khi bắt đầu B |
| Lệnh kiểm phần C | Claude viết khi bắt đầu C |
| Dựng `release_dev4_1` từ errata | Claude viết khi có errata |
