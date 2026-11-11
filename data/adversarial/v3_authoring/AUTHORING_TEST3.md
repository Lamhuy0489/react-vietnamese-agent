# Test-3: hướng dẫn cho người viết (owner, Minh)

Test-3 là bộ Test mới, niêm phong, để khẳng định D3 so với D2+P2 (decision log 2026-11-09 "Test-3").
Cách viết giống hệt Test v3: định dạng ở [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md), trục và cơ chế ở
[`taxonomy.md`](taxonomy.md). Trang này chỉ nêu phần khác.

## Viết gì, lưu ở đâu

- Danh sách family: [`spec_test3.json`](spec_test3.json), 48 dòng `T4_01` … `T4_48`, 8 dòng mỗi cơ chế
  M1–M6, 16 dòng có `b_auth = true`. Mỗi dòng đã định sẵn cơ chế, chi tiết, vector, mức thuyết phục, vị trí,
  giọng, cấu trúc, ràng buộc, lĩnh vực, loại sink và có B-auth hay không. Viết đúng theo dòng, không đổi cột.
- File viết: `data/adversarial/v3_authoring/test3_canonicals.json`, một mảng JSON 48 phần tử, mỗi phần tử
  là một canonical cùng trường như `test_canonicals.json` của Test v3; `spec_id` là `T4_xx`.
- Đủ biến thể: `canonical`, `paraphrase`, `english` cho `instruction`, `attack`, `benign` (và
  `auth.instruction` khi `b_auth`). `code_mix` và `no_diacritic` do code sinh.

## Luật

- Viết độc lập với phòng thủ: không đọc `src/react_agent/security_v1/`, `src/react_agent/security_v3/`
  (nhất là `d3.py`), các mục D2/D3 trong `docs/project/decision_log.md`, hay kết quả trong `results/`.
- Mới so với mọi bộ cũ: tên family, định danh `AWB_…`/`AUX_…`, đích, domain và bí mật `SYNTH-…` không trùng
  pilot, Dev, Test v3 (`release_v3`), `release_v2`, `release_test2`. Jaccard 4-gram ≤ 0,2 với các bộ đó.
- Dữ liệu giả: đích `@example.test` hoặc `mock://…`, bí mật `SYNTH-…`.
- Không đưa nội dung Test-3 cho công cụ AI bên ngoài nếu không chủ ý; không gửi cho Claude đọc.
- Chưa commit `test3_canonicals.json` trước khi niêm phong; commit cùng lúc seal.

## Lệnh kiểm

Dùng được ngay (không sửa `release.py` khi D3 Dev còn chạy; mã `T4_xx` được đổi tạm trong bộ nhớ):

```bash
.venv/bin/python scripts/check_release_test3_v1.py check --per-family   # liệt kê mọi family lỗi
.venv/bin/python scripts/check_release_test3_v1.py check   # schema, phủ spec, sink, bí mật, tamper, biến thể
.venv/bin/python scripts/check_release_test3_v1.py qa      # + replay an toàn/âm + độ mới (so cả pilot, Dev, Test v3)
```

Lỗi hay gặp:
- `paraphrase dropped protected literals`: bản `paraphrase`/`english` thiếu một literal của bản canonical (định danh,
  email, `mock://…`, số, ngày, `SYNTH-…`) đúng từng ký tự. Lưu ý: URL `mock://…` đứng ngay trước dấu chấm cuối câu thì
  dấu chấm bị tính vào literal; viết thêm chữ sau URL hoặc giữ đúng dấu chấm đó ở mọi biến thể.
- `code-mix requires substantive edits`: văn bản có dưới 2 từ trong glossary code-mix (ngoài tiêu đề). Thêm vài từ thông
  dụng (xem `code_mix_glossary_v3.json`) hoặc bổ sung glossary.

Script chỉ in số đếm và mã family, không in nội dung. Sạch `check` + `qa`, review chéo bằng phiếu 5 mục
(`taxonomy.md` §7), rồi báo Claude niêm phong; Claude ghi hash vào decision log và chạy Test-3 đúng một lần.
