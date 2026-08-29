# Reflection Questions

- **Họ và tên:** Chu Nguyễn Tuấn Anh
- **MSSV:** 2A202601755
- **Lab:** 27 — Agent Human-in-the-Loop (HITL)

## Câu 1 — `interrupt_before` hay `interrupt_after`?

Nếu email retention vừa được generate và con người cần **rewrite output đó trước khi workflow sang routing node**, lựa chọn trực tiếp nhất là `interrupt_after` trên node generate email. Ta cần cho node generation chạy xong để có nội dung email trong state, sau đó dừng ngay sau node đó để reviewer chỉnh sửa; routing chỉ được chạy khi graph resume. Một breakpoint `interrupt_before` trên chính routing node cũng đặt điểm dừng ở cùng ranh giới, nhưng theo cách đặt câu hỏi “sau khi email vừa được generate”, `interrupt_after` generation node diễn đạt intent rõ nhất.

## Câu 2 — Giảm Alert Fatigue khi 500 `send_email`/ngày đều ở 0.82

Không nên bắt human duyệt từng item chỉ vì score nằm sát 0.85. Tôi sẽ dùng ba lớp bảo vệ:

1. **Calibrate threshold theo action/risk:** dùng dữ liệu validation lịch sử để xác định threshold riêng cho `send_email`. Nếu evidence cho thấy 0.82 đã đủ an toàn cho hành động reversible/low-risk, có thể hạ threshold của riêng action này; hard rule cho `increase_credit_limit` vẫn không đổi.
2. **Gray-zone queue + batch review:** chỉ đẩy một dải bất định hẹp vào queue, gom các email tương tự thành batch với preview, filter/sort và “approve selected”, thay vì 500 modal riêng lẻ.
3. **Sampling + active learning:** auto-execute phần low-risk đã calibrated nhưng lấy mẫu ngẫu nhiên để QA. Các case human sửa/reject được đưa lại vào tập calibration để threshold và model cải thiện theo thời gian.

Như vậy human attention được dành cho các case thật sự bất định hoặc có hậu quả cao, thay vì biến reviewer thành một nút bấm cơ học.

## Câu 3 — Vì sao không nên tin self-reported confidence của LLM và cách calibrate?

Confidence do LLM tự báo không mặc định là xác suất đúng đã được calibration. Model có thể rất “tự tin” vì pattern ngôn ngữ quen thuộc trong khi input gốc (ví dụ thu nhập khách hàng) bị sai, thiếu hoặc hallucinate. Vì vậy score 0.95 có thể không tương ứng với 95% accuracy và có thể drift theo prompt/model version.

Trước routing, tôi sẽ calibration bằng dữ liệu có nhãn trên tập validation độc lập: đo reliability curve, Brier score/ECE; fit một mapping như Platt scaling hoặc isotonic regression từ raw score/features sang xác suất đã calibrated. Đồng thời validate các field tài chính từ nguồn dữ liệu có thẩm quyền và có thể thêm một verifier/rule-based check. Sau deployment tiếp tục theo dõi calibration drift và recalibrate định kỳ. Dù score đã calibrated, hard policy cho `increase_credit_limit` vẫn phải bắt buộc human review.
