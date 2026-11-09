# QUY CHẾ BẢO VỆ QUOTA VÀ CẦU DAO CHỐNG CHÁY CHO A2A / MULTI-AGENT
**Mã tài liệu:** `POL-A2A-CIRCUIT-BREAKER-v1.0`  
**Áp dụng:** Toàn bộ hệ sinh thái RON-SHO, Antigravity Local, Kilo, và các Orchestrator điều phối đa Agent.  
**Nguyên tắc tối thượng:** `FAIL-CLOSED` | `EVIDENCE BEFORE CLAIMS` | `NO GREEDY FALLBACK`

---

## 1. Bối cảnh & Vấn đề Cốt lõi

Trong mô hình Agent-to-Agent (A2A), khi Agent Điều Phối (Orchestrator) giao việc cho một Subagent hoặc Worker bên ngoài (Ollama local, worker node, API bên thứ ba):
* **Lỗi kinh điển (Greedy Fallback Trap):** Khi bên nhận việc không phản hồi, bị timeout hoặc trả về lỗi, Orchestrator tự ý suy diễn và nhảy vào tự làm thay (đọc toàn bộ file mã nguồn, nhồi ngữ cảnh khổng lồ vào prompt của chính nó).
* **Hậu quả:** Bùng nổ kích thước context window (Context Explosion), rơi vào vòng lặp mù quáng (blind retry loops), đốt sạch quota tài khoản trong vài phút và làm tê liệt hệ thống.

---

## 2. Các Điều Luật Bắt Buộc (Invariants)

### ĐIỀU 1: LUẬT CẤM TỰ TIỆN LÀM THAY (NO GREEDY FALLBACK)
1. Khi đã ủy quyền (delegated) một tác vụ cho Worker/Subagent chuyên trách, Orchestrator **TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP** tự ý đọc toàn bộ source code của task đó để làm thay khi Worker gặp sự cố.
2. Nếu Worker thất bại hoặc timeout: **HÀNH ĐỘNG DUY NHẤT LÀ DẬM CHÂN TẠI CHỖ (HALT)**, lập tức ghi nhận sự cố vào biên bản và dừng lượt chạy.

### ĐIỀU 2: NGUYÊN TẮC FAIL-CLOSED (LỖI THÌ ĐỨNG IM)
1. `TIMEOUT != RETRY_INDEFINITELY`.
2. `UNKNOWN_WORKER_STATE != PROCEED`.
3. Khi mất tín hiệu từ Worker quá ngưỡng thời gian quy định (`TIMEOUT_SECONDS`), hệ thống mặc định coi là **RỦI RO CAO** và tự động ngắt kết nối an toàn.

### ĐIỀU 3: TRẦN VÒNG LẶP & TRẦN TOKEN CỨNG (HARD CEILINGS)
1. **Trần thử lại (Max Retries):** Tối đa 2 lần thử lại cho một tác vụ ủy quyền. Nếu lần thứ 2 vẫn không có phản hồi hợp lệ, Cầu dao ngắt mạch (Circuit Breaker) phải bung ra ngay lập tức (`STATE = OPEN / TRIPPED`).
2. **Trần ngân sách Token (Token Budget Cap):** Mỗi phiên làm việc phải có một định mức trần (ví dụ: tối đa 20,000 tokens). Khi số token tích lũy đạt 90% trần, hệ thống cảnh báo; đạt 100% trần, hệ thống buộc phải ngắt tiến trình (`HALT_TOKEN_LIMIT`).

### ĐIỀU 4: BẤT ĐỒNG BỘ HÓA BẰNG HỘP THƯ (ASYNCHRONOUS MAILBOX)
1. Orchestrator không được duy trì trạng thái chờ chặn (Blocking Wait) quá 15 giây.
2. Mọi tác vụ nặng phải chuyển sang mô hình phát vé (Ticket):
   * Ghi yêu cầu vào `inbox/task_{id}.json`.
   * Worker đọc vé, xử lý và ghi kết quả vào `outbox/result_{id}.json`.
   * Orchestrator chỉ đọc `outbox` theo chu kỳ, không bị áp lực "phải tự làm ngay".

### ĐIỀU 5: CẤM IM LẶNG (SILENT HALT FORBIDDEN) — BẮT BUỘC NÊU RÕ "HAVE ISSUE"
1. **Tuyệt đối cấm im lặng:** Đứng im để bảo vệ quota KHÔNG đồng nghĩa với việc "im thin thít" làm người vận hành hoang mang.
2. Khi Worker không phản hồi hoặc Cầu dao bung (`OPEN`):
   * Orchestrator **BẮT BUỘC PHẢI HIGHLIGHT RÕ RÀNG**:
     * `[HAVE ISSUE / SỰ CỐ PHÁT SINH]`: Chỉ rõ Worker nào đang chết, task nào bị nghẽn, thời gian timeout là bao lâu.
     * `[ROOT CAUSE / NGUYÊN NHÂN]`: Bị rớt mạng, Ollama chưa bật, hay lỗi port.
     * `[ONE NEXT VALID ACTION]`: Chỉ định duy nhất 1 hành động kế tiếp cho anh Ron / Người vận hành (ví dụ: Bật lại Ollama, kiểm tra log local, hoặc reset cầu dao).

---

## 3. Hệ Thống Mã Trạng Thái Cầu Dao (Circuit States)

* `CLOSED` (Bình thường): Dòng điện thông suốt, các Agent giao tiếp ổn định.
* `HALF_OPEN` (Thử nghiệm hồi phục): Sau sự cố, cho phép thử đúng 1 yêu cầu nhỏ để kiểm tra xem Worker đã sống lại chưa.
* `OPEN / TRIPPED` (Cắt cầu dao khẩn cấp): Ngắt toàn bộ lệnh gọi, chặn đứng nguy cơ đốt quota, đồng thời phát cảnh báo `HAVE ISSUE` tới người vận hành.
