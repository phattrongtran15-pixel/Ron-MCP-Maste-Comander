---
name: a2a-kilo-orchestration
description: Quy chuẩn và cẩm nang điều phối đa tác tử A2A (Agent-to-Agent), điều phối Kilo/OpenCode/Goose, cầu dao chống cháy quota (Circuit Breaker), và kỷ luật bàn giao chuẩn Ron-Sho M1-M5 đúc kết từ 71 phiên thực chiến.
---

# CẨM NANG ĐIỀU PHỐI ĐA TÁC TỬ A2A & QUẢN TRỊ KILO / WORKER
**Mã hiệu:** `SKILL-A2A-KILO-ORCHESTRATION-v1.0`  
**Triết lý:** `HUMAN SOVEREIGNTY` | `EVIDENCE BEFORE CLAIMS` | `FAIL-CLOSED` | `NO GREEDY FALLBACK`  
**Nguồn gốc:** Đúc kết từ phân tích pháp y 179 phiên Brain và 71 phiên chỉ đạo thực tế của Thuyền trưởng Ron (08/2026 - 11/2026).

---

## I. TỔNG QUAN & PHÂN ĐỊNH VAI TRÒ (CAPABILITY != AUTHORITY)

Trong hệ sinh thái điều phối đa tác tử:
* **Antigravity Cloud (Anti Cloud):** Giữ vai trò **TỔNG THẦU KIẾN TRÚC & QA ORACLE (PM / Architect / Verifier)**.
  - Chịu trách nhiệm: Lập kế hoạch M1 -> M5, thiết kế schema, viết unit tests, giám sát rơ-le an toàn, kiểm chứng tính toàn vẹn.
  - **CẤM TUYỆT ĐỐI:** Tự biến mình thành thợ gõ code nặng (hàng ngàn dòng) làm cạn kiệt token quota.
* **Kilo / OpenCode / Goose / Worker Agents:** Giữ vai trò **THỢ THI CÔNG (Heavy Code Builder)**.
  - Tận dụng tài nguyên quota miễn phí dồi dào (OpenRouter Free, Groq Free, Ollama local) để cày cuốc, refactor, viết chi tiết.
* **Thuyền trưởng Ron (Human Sovereignty):** Nắm quyền quyết định và **NGHIỆM THU TỐI CAO (Acceptance Gate)**. Không bao giờ biến Ron thành middleware gõ phím dọn rác.

---

## II. 6 CẠM BẪY PHÁP Y CỐT TỬ CẦN TRÁNH (THE 6 FATAL TRAPS)

1. **FAIL-01: Bẫy tham lam ôm việc (Greedy Orchestrator Fallback):** Khi Worker gặp sự cố, Orchestrator tự ý mở file code khổng lồ để tự làm thay -> Context window bùng nổ -> Cháy sạch quota tài khoản.
2. **FAIL-02: Vụ nổ Quota trong đêm (Overnight Quota Burnout):** AI tự chạy vòng lặp chẩn đoán vô hạn trong khi Ron đang ngủ mà không có cầu dao ngắt.
3. **FAIL-03: Vòng lặp sửa lỗi không hội tụ (Endless Debug Loops):** Sửa lỗi mù quáng không dừng. Phải tuân thủ chỉ thị `DO_NOT_CREATE_DEBUG_LOOPS=TRUE`.
4. **FAIL-04: Lạc trôi mục tiêu (Unbounded Scope):** Sa đà vào viết tài liệu triết lý vũ trụ thay vì dứt điểm tính năng thực tế ("Quay về trái đất nào!").
5. **FAIL-05: Lệch môi trường & Mã hóa (Platform Mismatch):** Lỗi tiếng Việt stdout `cp1252` (`UnicodeEncodeError`) trên Windows, hardcode đường dẫn Linux thay vì Windows path.
6. **FAIL-06: Ảo giác trạng thái (State Hallucination):** Tự tuyên bố `ALL TESTS PASS` hay `DONE 100%` khi chưa có bằng chứng nhị phân / read-back vật lý.

---

## III. 5 ĐỊNH LUẬT BẤT BIẾN ĐIỀU PHỐI A2A

### ĐỊNH LUẬT 1: TÁCH BẠCH THẨM QUYỀN
Anti Cloud thiết kế và kiểm định; Worker thi công. Người thiết kế không tự cấp bằng nghiệm thu cho sản phẩm của mình.

### ĐỊNH LUẬT 2: CẦU DAO QUOTA CHỐNG THAM LAM (CIRCUIT BREAKER & NO SILENT HALT)
Khi phát lệnh ủy quyền (delegate) cho Kilo / Worker:
* Nếu Worker gặp sự cố: **Timeout > 30s, Lỗi 429 Rate Limit, Crash, Connection Refused**:
  - **HÀNH ĐỘNG DUY NHẤT:** CẮT CẦU DAO NGAY LẬP TỨC (`HALT IMMEDIATELY`), bảo toàn 100% ngân sách token.
  - **CẤM TUYỆT ĐỐI:** Tự đọc source code nặng để làm thay.
  - **CẤM IM LẶNG:** Bắt buộc xuất cảnh báo thị giác đập vào mắt:
```markdown
🚨 [HAVE ISSUE: AI PLATFORM UNRESPONSIVE / CIRCUIT TRIPPED]
• Platform: <Tên Worker/Model>
• Task ID: <Mã công việc>
• Root Cause: <Chi tiết lỗi: Timeout 30s / Rate limit 429 / Connection refused>
• Quota Status: ĐÃ BẢO TỒN NGUYÊN VẸN (Cầu dao ngắt an toàn)
👉 ONE NEXT VALID ACTION FOR RON: <Đúng 1 bước kiểm tra ngắn gọn>
```

### ĐỊNH LUẬT 3: KẾ HOẠCH BẮT BUỘC 3 ĐẾN 5 BƯỚC (ATOMIC INCREMENTS)
* Không giao prompt khổng lồ chứa 20 việc.
* Mỗi nhiệm vụ chia thành đúng 3 đến 5 bước ngắn: Input rõ -> Expected Output -> Tiêu chí Pass/Fail bằng mắt thường.

### ĐỊNH LUẬT 4: NGUYÊN TẮC CẮT LỖ 2 LẦN (MAX 2 RETRIES)
* Khi gặp lỗi, cho phép AI đổi phương án và thử lại **TỐI ĐA 2 LẦN**.
* Lần thứ 3 vẫn tắc: **DỪNG LẠI NGAY LẬP TỨC**. Trình bày ngôn ngữ đời thường cho Ron: Điểm nghẽn ở đâu? Cần Ron can thiệp gì?

### ĐỊNH LUẬT 5: NIÊM PHONG & KIỂM CHỨNG NHỊ PHÂN (MERKLE SEAL)
* Sau khi Worker thi công xong: Khóa cứng toàn bộ file -> chạy kiểm thử vật lý -> kiểm tra sha256/read-back trước khi báo cáo nghiệm thu.

---

## IV. MẪU BÀN GIAO CHUẨN A2A (A2A HANDOFF CONTRACT SCHEMA)

Mỗi lần chuyển giao ca trực hoặc bàn giao kết quả giữa các Agent, bắt buộc sử dụng form chuẩn sau:

```markdown
⚡ [Topic: <tên_topic> | Domain: <nhóm_domain> | Fork: <nhánh> | AI Pic: <tên_ai> | Turn: <số_lượt> | Context: <số_token>% | State: <trạng_thái> | Ref: #TOPIC_STATE.json]

CURRENT SYSTEM STATE
- **Workspace / Platform:** [Đường dẫn workspace] | [ANTIGRAVITY_IDE / CLOUD_WEB / LOCAL_NATIVE]
- **Project ID / Work ID:** [Mã dự án] / [Mã công việc]
- **State & Checkpoint:** [VERIFIED / HOLD / UNKNOWN] | [Checkpoint hash/ref]
- **Blocker / Loop:** [Điểm nghẽn hoặc NONE] | [Vấn đề mở hoặc NONE]
- **Main Track:** [Mục tiêu cốt lõi duy nhất đang giải quyết]

HANDOFF
- **Actor Lineage:** [Actor hiện tại] -> [Next Target Actor] | [Thẩm quyền]
- **Execution & Truth Delta:** [Tóm tắt việc đã làm & Thay đổi thực tế trên file/hệ thống]
- **Evidence Refs:** [Link file log / file chứng thực / commit SHA]
- **Fork Analysis:** Fork A (Hướng thắng) — ON_TRACK | Fork B — OFF_TRACK | Fork C — DEAD_END

ONE NEXT ACTION
> [Đúng 1 lệnh terminal hoặc prompt ăn liền để Ron duyệt hoặc chạy ngay]

END
```

---

## V. CÔNG CỤ TÍCH HỢP (TOOLING SUPPORT)

Khi thực thi trên hệ thống, sử dụng trực tiếp các công cụ đã được đóng gói trong repo `Ron-MCP-Maste-Comander`:
* `ron_mcp_commander.circuit_breaker.CircuitBreaker`: Rơ-le tự ngắt mạch khi lỗi 2 lần liên tiếp hoặc chạm trần token.
* `ron_mcp_commander.mailbox.MailboxManager`: Trạm phát vé bất đồng bộ (Inbox/Outbox) ngăn chặn việc treo máy (blocking wait).
* CLI: `python -m ron_mcp_commander.cli status --budget 20000`
