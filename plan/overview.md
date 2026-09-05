## I. Problem Formulation & Objectives

Tôi đã đọc toàn bộ bản Word 9 trang theo góc nhìn của một kế hoạch nghiên cứu hoàn chỉnh: câu hỏi nghiên cứu, phạm vi, kiến trúc hệ thống, A0–A6, benchmark, Dev/Test, robustness, kế hoạch 24 tuần và phân công hai thành viên. 

Tôi cũng đã ghi nhớ ràng buộc triển khai của bạn: nhóm 2 người, local không có GPU phù hợp, inference chủ yếu trên Kaggle/Kaggle CLI; về mặt lập kế hoạch, GPU quota được xem là đủ nên **không cần thu nhỏ thực nghiệm chỉ vì tài nguyên tính toán**. Việc sử dụng tài nguyên Kaggle vẫn nên nằm trong quyền truy cập và điều khoản áp dụng của nền tảng.

Kết luận tổng thể:

> **Bản Word hiện tại đã đủ tốt để dùng làm bản kế hoạch chính thức của đồ án. Không có vấn đề kiến trúc nào buộc phải đổi đề tài hoặc thiết kế lại toàn bộ.**

Tôi sẽ giữ nguyên hướng 24 tuần và 8 nhóm phase hiện tại. Tuy nhiên, trước khi coi specification là “frozen”, có **4 điểm phương pháp bắt buộc phải làm rõ** và một số điểm nên bổ sung. Chúng không làm thay đổi đề tài, nhưng nếu không khóa sớm thì về sau dễ gây data leakage hoặc làm kết quả A0–A6 khó diễn giải.

---

# II. Đánh giá toàn cục: cấu trúc nghiên cứu hiện tại hợp lý

Bản Word đã tốt hơn đáng kể so với bản kế hoạch dài trước đó ở chỗ scope được diễn đạt rõ và có tính bảo vệ khi trình bày với giảng viên.

Ba RQ hiện tại tạo thành một cấu trúc rất sạch:

$$
RQ1 \rightarrow Capability
$$

$$
RQ2 \rightarrow Security
$$

$$
RQ3 \rightarrow Vietnamese\ Robustness
$$

Đây là ba trục độc lập vừa đủ, không bị lan sang fine-tuning, multi-agent hay system security cấp OS. 

Bối cảnh **trợ lý hành chính–học vụ đại học giả lập** cũng là lựa chọn hợp lý. Nó cho phép nhóm kiểm soát:

$$
\text{Ground Truth}
+
\text{Sensitive Data}
+
\text{Tool Behavior}
+
\text{Attack Placement}
$$

mà không phải xử lý dữ liệu cá nhân thật. Điều này đặc biệt quan trọng với RQ2.

Tám mock tools cũng đủ để tạo ra ba loại hành vi cần nghiên cứu:

$$
\text{Information Retrieval}
\rightarrow
\text{Computation}
\rightarrow
\text{External Sink}
$$

Trong đó `send_email_mock` và `post_webhook_mock` tạo ra security sink rõ ràng. Đây là điểm mạnh của thiết kế vì định nghĩa attack success có thể dựa trên hành vi quan sát được thay vì phán đoán chủ quan. 

---

# III. Dataset design hiện tại nhìn chung tốt

Bản Word hiện tại có ba khối dữ liệu khác nhau và nên tiếp tục giữ tách biệt như vậy.

$$
D_{\text{clean}} = 250
$$

với:

$$
150_{Dev}+100_{Test}
$$

Adversarial benchmark bắt đầu từ:

$$
70\ canonical\ attack\ scenarios
$$

và mỗi scenario có 5 biến thể:

$$
70\times5=350
$$

cùng:

$$
350\ benign\ controls
$$

Ngoài ra robustness clean benchmark gồm:

$$
50\ canonical + 250\ variants =300
$$

Cấu trúc này tốt hơn việc tạo hàng trăm attack hoàn toàn độc lập, vì bạn có một **canonical semantic unit** rồi kiểm tra nhiều surface perturbations của cùng một semantics. 

Với 2 người và GPU inference không còn là constraint chính, tôi **không đề nghị giảm các con số này nữa**.

Khối lượng tạo dữ liệu vẫn lớn, nhưng có thể quản lý được:

$$
250/2 = 125
$$

clean tasks/người,

và:

$$
70/2 = 35
$$

canonical attack scenarios/người.

Phân công trong Word đã phản ánh chính xác điều này. 

---

# IV. Bốn điểm bắt buộc phải khóa trước khi triển khai

Đây là những điểm tôi coi là quan trọng nhất sau khi đọc toàn bộ tài liệu.

| Mức          | Vấn đề                           | Trạng thái hiện tại                                                    | Cách nên khóa                                                                     |
| ------------ | -------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Bắt buộc** | Dev/Test của attack variants     | Word nói 350 variants chia 200/150 nhưng chưa nói rõ cách chia         | **Split theo 70 canonical scenario trước**, sau đó mới tạo variants               |
| **Bắt buộc** | Robustness subset 50 clean tasks | Chưa nói rõ 50 task lấy từ Dev/Test hay tập riêng                      | Định nghĩa rõ đây là frozen held-out subset hoặc separate held-out robustness set |
| **Bắt buộc** | Quan hệ A0–A6                    | Mô tả từng mức rõ về ý tưởng nhưng chưa đủ rõ về component inheritance | Tạo component matrix chính xác cho A0…A6                                          |
| **Bắt buộc** | Số LLM backbones                 | Word nói “các mô hình có sẵn” nhưng chưa định lượng                    | Chốt mục tiêu **3 backbone** nếu đó vẫn là thiết kế nghiên cứu cuối               |
| Nên có       | Statistical analysis             | Chưa xuất hiện rõ                                                      | Bổ sung CI + paired statistical testing                                           |
| Nên có       | Human validation                 | Có nói “một phần kết quả”                                              | Sau này khóa sampling protocol + agreement                                        |
| Nên có       | Run reproducibility              | Có versioning nhưng chưa định nghĩa chi tiết                           | Lưu model revision, config/data hash, Git commit, seed                            |

Điểm thứ nhất đặc biệt quan trọng.

Hiện tại:

$$
70\times5=350
$$

và:

$$
200_{Dev}+150_{Test}=350.
$$

Cách chia tự nhiên nhất phải là:

$$
40\ canonical\ scenarios \rightarrow 200\ Dev\ variants
$$

$$
30\ canonical\ scenarios \rightarrow 150\ Test\ variants.
$$

Tức là toàn bộ năm variants của cùng canonical scenario phải thuộc **cùng một split**.

Formal requirement:

$$
G_{\text{Dev}}\cap G_{\text{Test}}=\varnothing
$$

với \(G\) là tập canonical attack families.

Nếu một biến thể bỏ dấu nằm ở Dev nhưng paraphrase của cùng attack nằm ở Test, thì semantic attack template đã leak từ Dev sang Test. Khi đó held-out test không còn thật sự held-out.

Đây là chỉnh sửa quan trọng nhất tôi muốn bạn ghi vào specification sau này.

---

# V. Robustness set cũng cần làm rõ một điểm

Word hiện nói:

> trước khi khóa tập kiểm thử, chọn 50 tác vụ bình thường rồi tạo 5 variants.

Ý tưởng đúng. 

Nhưng cần định nghĩa chính xác quan hệ giữa:

$$
D_{\text{robust}}
$$

và:

$$
D_{\text{clean}}^{test}.
$$

Có hai thiết kế hợp lệ.

Thiết kế đơn giản nhất cho đồ án của bạn là:

$$
D_{\text{robust}}^{canonical}
\subset
D_{\text{clean}}^{test}
$$

với:

$$
|D_{\text{robust}}^{canonical}|=50.
$$

Tức là chọn 50 trong 100 clean held-out tasks, trước khi freeze, sau đó tạo 250 variants.

Khi đó:

$$
50\times5=250
$$

variants và comparison luôn paired.

Điều duy nhất phải tránh là chọn 50 task từ Dev sau khi đã dùng Dev để tune normalizer/prompt/policy.

---

# VI. A0–A6: ý tưởng đúng, nhưng cần một component matrix

Đây là điểm kiến trúc duy nhất tôi thấy cần khóa rõ hơn.

Trong Word:

* A1 = rule/regex.
* A2 = model guard.
* A3 = sensitivity.
* A4 = untrusted-data/control influence.
* A5 = sensitivity + trust ở session level.
* A6 = provenance-aware + pre/post/final gates. 

Các mức này có logic nghiên cứu tốt.

Nhưng hiện chưa hoàn toàn rõ:

$$
A_3 = A_2 + sensitivity?
$$

hay:

$$
A_3 = A_0 + sensitivity?
$$

Tương tự A4/A5.

Đây là khác biệt rất lớn về mặt experimental interpretation.

Nếu A0–A6 là **cumulative defense levels**, phải có:

$$
A_i \supseteq A_{i-1}.
$$

Nếu chúng là **alternative architectures/ablations**, thì không được mô tả như các mức tăng dần đơn giản.

Tôi nghiêng về cumulative levels cho đồ án này vì nó dễ giải thích:

$$
A0
\rightarrow A1
\rightarrow A2
\rightarrow \cdots
\rightarrow A6.
$$

Nhưng đến lúc Phase 0 chúng ta sẽ khóa thành một ma trận thành phần, không để mỗi thành viên hiểu A3/A4/A5 khác nhau.

A6 hiện được xác định là contribution kỹ thuật trọng tâm, và tôi thấy cách đặt trọng tâm đó hợp lý. 

---

# VII. Một thiếu sót tương đối rõ trong Word: số model

Bản kế hoạch cũ của bạn có Experiment 1 với ba LLM backbones, nhưng bản Word hiện tại không còn ghi cụ thể số lượng.

Trang đầu nói:

> “Các mô hình có sẵn được sử dụng làm nền tảng…”

nhưng chưa nêu:

$$
|M| = ?
$$



Vì bạn đã xác nhận compute không phải constraint chính, tôi khuyên giữ:

$$
\boxed{|M|=3}
$$

cho capability experiment.

Sau đó security experiment dùng một model cố định:

$$
M^*.
$$

Điều đó tạo thiết kế rất sạch:

$$
E_1:\quad M_1,M_2,M_3 \times A0
$$

$$
E_2:\quad M^* \times A0,\ldots,A6
$$

$$
E_3:\quad M^* \times canonical/variants
$$

Như vậy:

* RQ1 kiểm tra backbone/tool-agent capability.
* RQ2 cô lập effect của security architecture.
* RQ3 cô lập effect của Vietnamese perturbation.

Tôi sẽ không đưa chi tiết model nào vào lúc này; chỉ nói về design toàn cục.

---

# VIII. Phân công hai người: tôi đánh giá là ổn

Bản Word chia khối lượng tốt hơn phương án “mỗi người làm một nửa pipeline”.

Hai người cùng làm dữ liệu:

$$
125/125
$$

clean,

và:

$$
35/35
$$

attack canonical.

Sau đó specialization:

$$
Huy
\rightarrow
ReAct + control\ flow + policy + A1\text{--}A4 + RQ2
$$

$$
Minh
\rightarrow
data + provenance + A5\text{--}A6 + robustness + RQ1/RQ3.
$$

A6 lại được quy định là integration chung. 

Đây là điểm quan trọng vì A6 phụ thuộc cả control-flow và data-flow. Nếu giao hoàn toàn cho một người thì người còn lại có thể không nắm được contribution chính.

Tôi sẽ **giữ nguyên cách phân công hiện tại**.

---

# IX. Timeline 24 tuần có hợp lý không?

Có.

Tôi không thấy cần đổi thứ tự macro:

$$
\text{Specification}
\rightarrow
A0
\rightarrow
Clean\ Data
\rightarrow
Adversarial\ Data
\rightarrow
Security\ Structures
\rightarrow
A1\text{--}A6
\rightarrow
Evaluation
\rightarrow
Experiments
\rightarrow
Writing.
$$



Điểm rất đúng là A0 được xây ở tuần 2 trước khi nhóm tạo 600–900 mẫu dữ liệu. Nếu agent/tool schema ban đầu có vấn đề, bạn phát hiện trước khi benchmark bị đóng cứng theo một interface sai.

24 tuần cũng có buffer 2 tuần cuối. Với LLM experiments, buffer này nên giữ nguyên, không phân bổ trước cho feature mới.

---

# X. Tôi sẽ tổ chức toàn bộ dự án thành các Phase như sau

Chưa đi vào checklist chi tiết, nhưng từ bây giờ tôi sẽ dùng cùng một taxonomy cố định khi làm với bạn:

$$
\boxed{\text{Phase 0}}
$$

Research specification & experiment contract
**Tuần 1**

$$
\boxed{\text{Phase 1}}
$$

Baseline A0 + simulated environment
**Tuần 2**

$$
\boxed{\text{Phase 2}}
$$

Clean benchmark
**Tuần 3–5**

$$
\boxed{\text{Phase 3}}
$$

Adversarial + benign benchmark
**Tuần 6–8**

$$
\boxed{\text{Phase 4}}
$$

Normalization + data/provenance foundations
**Tuần 9–10**

$$
\boxed{\text{Phase 5}}
$$

Security architectures A1–A6
**Tuần 11–14**

$$
\boxed{\text{Phase 6}}
$$

Evaluation framework
**Tuần 15–16**

$$
\boxed{\text{Phase 7}}
$$

Final experiments & statistical analysis
**Tuần 17–20**

$$
\boxed{\text{Phase 8}}
$$

Reproducibility + thesis/report
**Tuần 21–22**

và:

$$
\boxed{\text{Buffer}}
$$

**Tuần 23–24**.

Cấu trúc này khớp trực tiếp với Word hiện tại. 

---

# XI. Khi đi vào từng Phase, checklist sẽ theo một format cố định

Tôi đã ghi nhớ yêu cầu này cho các lần trao đổi sau.

Mỗi Phase tôi sẽ không chỉ nói “làm cái gì”, mà checklist sẽ kiểm soát toàn bộ lifecycle:

$$
\text{Inputs}
\rightarrow
\text{Tasks}
\rightarrow
\text{Files}
\rightarrow
\text{Tests}
\rightarrow
\text{Artifacts}
\rightarrow
\text{Git/Kaggle}
\rightarrow
\text{Acceptance Criteria}.
$$

Tức là một Phase chỉ được coi là hoàn thành khi:

$$
\forall c_i\in C_{phase},\quad c_i=PASS.
$$

Như vậy bạn sẽ biết chính xác khi nào được chuyển sang phase tiếp theo thay vì làm theo cảm giác.

---

# XII. Kết luận cuối cùng về bản Word

**Có thể chốt bản này làm master project plan.** Tôi không thấy cần viết lại đề tài hoặc thay đổi phạm vi lớn. 

Trước khi bắt đầu code, tôi chỉ muốn khóa thêm bốn vấn đề:

$$
\boxed{
\begin{aligned}
1.&\ \text{Attack split theo canonical family}\\
2.&\ \text{Vị trí chính xác của 50 robustness tasks}\\
3.&\ \text{Component definition chính xác của A0--A6}\\
4.&\ \text{Chốt 3 LLM backbones cho Experiment 1}
\end{aligned}}
$$

Ngoài bốn điểm đó, các phần **RQ, scope, mock tools, attack definition, data scale, 24-week schedule, phân công hai người và A6 làm contribution trọng tâm** đều nhất quán và có thể triển khai.

Từ đây tôi sẽ xem **file Word này là specification gốc của đồ án**. Khi bạn hỏi Phase 0, Phase 1, v.v., tôi sẽ bám theo nó, không tự ý thu nhỏ dataset hay đổi kiến trúc vì vấn đề GPU. 
