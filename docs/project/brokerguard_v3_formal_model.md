# BrokerGuard v3: mô hình hình thức và mệnh đề (bản nháp cho bài tạp chí)

Cập nhật 2026-11-16. Bám theo code `src/react_agent/security_v3/` (decision log 2026-11-16 12:30 và 15:30) và mục 4
của [thiết kế v3](brokerguard_v3_extension_design.md). Mức chi tiết: đủ để phát biểu và chứng minh dưới giả định; phần
thực nghiệm nằm ở mục 5.

## 1. Ký hiệu

- $u$: lời yêu cầu thô của người dùng, là nguồn tin cậy duy nhất. Đầu ra công cụ đều không tin cậy.
- Công cụ chia hai lớp: đọc $R$ (`doc_read`, `db_query`, `cached_fetch`, `calculator`, ...) và sink có tác dụng phụ
  $S = \{\textsf{email}, \textsf{webhook}\}$. Mỗi sink có một trường đích $\textsf{dst}(a)$ và các trường dữ liệu
  $\textsf{data}(a)$.
- Quan sát $o_t$: đầu ra công cụ ở bước $t$, mang nhãn độ tin $\tau(o_t)$ và độ nhạy $\sigma(o_t)$ do môi trường gắn.
  Hai chiều này độc lập (bất biến của dự án).
- $P(u) = \{g_i\}$: chính sách ý định, mỗi $g = (\textsf{tool}, \textsf{dst}, \pi, \textsf{pins}, \textsf{flags})$ với
  cực tính $\pi \in \{+, -\}$ (`intent_policy_v1.Grant`).
- $V(u)$: tập giá trị xuất hiện nguyên văn trong $u$ (so ở dạng rút gọn $\kappa$: casefold, bỏ dấu, chỉ giữ chữ và số).
- $C_t$: tập giá trị cần bảo vệ sau bước $t$, gồm (i) giá trị kiểu dữ liệu trong quan sát có $\sigma \ge$ mật (luật 3
  của v1) và (ii) giá trị được C2 gắn nhãn theo kiểu, bất kể $\sigma(o)$ (`value_labels_v1.label_values`).
- Trạng thái $s_t = (u, P(u), C_t, H_t)$, $H_t$ là lịch sử lời gọi và quan sát.

## 2. Broker là điểm kiểm duy nhất

Mỗi lời gọi đề xuất $a_t$ đi qua hàm cổng $\textsf{gate}(s_t, a_t) \in \{\textsf{allow}, \textsf{deny},
\textsf{confirm}\}$; trong benchmark, $\textsf{confirm}$ được thi hành như $\textsf{deny}$ và đếm riêng. Với $a_t \in S$,
$\textsf{gate} = \textsf{allow}$ khi và chỉ khi cả bốn điều kiện sau đúng (`brokerguard_v3_v1.V3State.check_action`):

1. **Lớp luật A1 của v1** không chặn (giữ nguyên v1).
2. **C1 (quyền):** có $g \in P(u)$ với $\pi(g) = +$, $\textsf{tool}(g) = \textsf{tool}(a_t)$,
   $\textsf{dst}(g) = \textsf{dst}(a_t)$ (khớp nguyên token sau chuẩn hóa), $g$ không bị đánh dấu chỉ-nhắc-tới; và không
   có $g' \in P(u)$ với $\pi(g') = -$ cùng đích. Đích chỉ được nhắc tới (trích dẫn, lời thuật lại, "chỉ để tham khảo",
   không có động từ gửi không bị phủ định) cho kết quả $\textsf{confirm}$.
3. **C3 (toàn vẹn):** với ít nhất một $g$ thỏa (2): mọi literal ghim $p \in \textsf{pins}(g)$ có
   $\kappa(p) \sqsubseteq \kappa(\textsf{data}(a_t))$, và $\textsf{data}(a_t)$ không mang boolean ngược với boolean ghim
   hay boolean bị cấm, không đổi đơn vị đã nêu (`param_pinning_v1.check`).
4. **C2 (luồng giá trị):** không có $v \in C_t \setminus V(u)$ với $\kappa(v) \sqsubseteq \kappa(\textsf{data}(a_t))$
   (`value_labels_v1.flows`; $\sqsubseteq$ là chuỗi con).

Với $a_t \in R$: $\textsf{allow}$ (đọc tự do, như luật 1 của v1; chỉ chịu giới hạn công cụ). Câu trả lời cuối $y$ đi qua
phép che: mọi $v \in C_t \setminus V(u)$ có $\kappa(v) \sqsubseteq \kappa(y)$ được thay bằng `[REDACTED]` ở mọi dạng bề
mặt khớp với $\kappa(v)$ (`value_labels_v1.redact`).

## 3. Giả định

- **(A1) Complete mediation.** Mọi lời gọi công cụ đều qua broker; agent không có kênh tác dụng phụ nào khác. Đúng theo
  cấu trúc code (Tool Broker là đường duy nhất, bất biến của dự án) và được test kiểm.
- **(A2) Bộ trích đúng trên $u$.** Với mọi sink người dùng thực sự cho phép, $P(u)$ có grant dương tương ứng; với mọi
  đích người dùng cấm hoặc không nêu, $P(u)$ không có grant dương. Đo thực nghiệm (mục 5).
- **(A3) Độ phủ nhãn.** Mọi giá trị bí mật $v$ xuất hiện trong quan sát đều thuộc $C_t$: hoặc nguồn có
  $\sigma \ge$ mật, hoặc $v$ thuộc một kiểu C2 nhận ra (định danh trộn chữ và số $\ge 8$ ký tự, số $\ge 9$ chữ số, giá
  trị đứng sau tên trường nhạy cảm).
- **(A4) Lớp biến đổi.** Kẻ tấn công chỉ làm rò $v$ dưới dạng $w$ với $\kappa(v) \sqsubseteq \kappa(w)$: thêm hoặc bỏ
  khoảng trắng, dấu chấm, gạch, đổi hoa thường, bỏ dấu tiếng Việt. Mã hóa (base64), dịch số thành chữ, hay chia giá trị
  qua nhiều lời gọi nằm ngoài lớp này.
- **(A5) Literal ghim đúng.** $\textsf{pins}(g)$ là đúng các giá trị người dùng đã nêu cho sink của $g$.

## 4. Mệnh đề

**Mệnh đề 1 (an toàn quyền).** Dưới (A1) và (A2), mọi sink được thực thi có (công cụ, đích) thuộc ý định người dùng.

*Chứng minh.* Theo (A1), sink $a$ chỉ thực thi khi $\textsf{gate}(s_t, a) = \textsf{allow}$, nên điều kiện (2) đúng: có
grant dương cùng công cụ và đích, không có grant âm cùng đích. Theo (A2), grant dương chỉ có cho đích người dùng cho
phép. $\square$

**Mệnh đề 2 (bí mật).** Dưới (A1), (A3) và (A4), không giá trị bí mật nào ngoài $V(u)$ tới một sink được thực thi hay
xuất hiện trong câu trả lời cuối đã phát hành.

*Chứng minh.* Theo (A3), mọi bí mật $v$ đã quan sát thuộc $C_t$. Nếu sink $a$ mang $v$ ở dạng $w$, theo (A4)
$\kappa(v) \sqsubseteq \kappa(\textsf{data}(a))$, nên điều kiện (4) sai và $a$ bị chặn; theo (A1) không có đường thực thi
khác. Với câu trả lời cuối, phép che thay mọi dạng bề mặt khớp $\kappa(v)$ trước khi phát hành. $\square$

**Mệnh đề 3 (toàn vẹn).** Dưới (A1), (A2) và (A5), mọi sink được thực thi giữ nguyên mọi giá trị người dùng đã nêu cho
sink đó và không mang boolean ngược với boolean người dùng nêu.

*Chứng minh.* Từ điều kiện (3) và (A5), tương tự Mệnh đề 1. $\square$

Các mệnh đề là điều kiện đủ dưới giả định, không phải bảo đảm vô điều kiện: khi (A2), (A3) hoặc (A5) bị vi phạm, các ca
lọt được quy về giả định tương ứng (cách làm như Mục 7 của bài ICCIES).

## 5. Được chứng minh và chỉ kiểm thực nghiệm

| Tính chất | Trạng thái | Bằng chứng hiện có (Dev v4.1) |
|---|---|---|
| (A1) mọi lời gọi qua broker | theo cấu trúc, test | `tests/unit/test_brokerguard_v3_v1.py` (chạy trọn runtime) |
| Mệnh đề 1–3 khi giả định đúng | chứng minh (mục 4) | |
| (A2) độ đúng của bộ trích | thực nghiệm | sink cần cho phép: 100 % train và val; M6 chặn 105/105, 35/35 (decision log 12:30) |
| (A3) độ phủ nhãn C2 | thực nghiệm | phát lại oracle; trên Dev v1 đã chặn hết M3/M4 nên cần chạy agent thật và Test-4 |
| (A4) lớp biến đổi | giới hạn đã nêu | bộ chấm biến đổi `transformed_leakage.py` đo các dạng ngoài lớp |
| (A5) literal ghim | thực nghiệm | M5 Dev-val còn 2/35 quỹ đạo lọt (số nêu ở mệnh đề đọc, không có câu cấm sửa) |
| Lời nhắc P2, utility, chi phí | thực nghiệm | mốc Dev v4.1; H2–H4 trên Test-4 |

## 6. Ngoài phạm vi (bài phải nêu)

- Nội dung sai nhưng không vi phạm literal ghim (agent viết sai một trường người dùng không nêu).
- Đọc tự do: agent vẫn đọc được mọi nguồn; v3 chỉ bảo vệ luồng ra (sink và câu trả lời cuối).
- "Cần xác nhận" được mô phỏng là từ chối; tỉ lệ xác nhận báo riêng như chi phí utility.
- Bộ dò C2 cố ý không dựa vào dạng giá trị mật của bộ sinh dữ liệu (mọi giá trị mật Dev cùng một dạng); độ phủ trên dạng
  khác là câu hỏi thực nghiệm.

## 7. Kiểm mô hình (tùy chọn, chưa làm)

Property-based test (hypothesis) trên policy thật: sinh $u$ tổng hợp từ ngữ pháp nhỏ (đích, cực tính, literal) và chuỗi
lời gọi ngẫu nhiên; kiểm ba bất biến ở mục 4 trên mọi vết. Không dùng văn bản Dev hay Test.
