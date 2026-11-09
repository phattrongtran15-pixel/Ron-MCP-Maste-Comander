# Ron MCP Master Commander

**Hệ Thống Điều Phối Đa Agent & Cầu Dao Chống Cháy Quota cho Căn Cứ Mặt Đất**

`Ron-MCP-Maste-Comander` là giải pháp kỹ thuật triệt tiêu vấn đề **"Greedy Fallback"** (Agent điều phối mất kết nối thì tự tiện lao đầu vào làm, gây bùng nổ context và đốt sạch token quota).

---

## 1. Năng Lực Cốt Lõi (Maturity Level: L3 - App Machine)

* **Level 1 (Chính sách - Policy):** [`docs/CIRCUIT_BREAKER_RULES.md`](docs/CIRCUIT_BREAKER_RULES.md) — Quy chế bất biến cấm Agent điều phối tự làm thay việc của Worker khi xảy ra sự cố (Luật `FAIL-CLOSED`).
* **Level 2 (Kiểm định - Verification & CI):** 
  * Schema vé tác vụ bất đồng bộ: [`schemas/task_ticket.schema.json`](schemas/task_ticket.schema.json).
  * 8/8 Unit tests kiểm chứng vật lý (`tests/test_circuit_breaker.py`, `tests/test_mailbox.py`).
  * GitHub Actions CI tự động (`.github/workflows/test.yml`).
* **Level 3 (Máy thực thi - App Engine):** 
  * `CircuitBreaker`: Cầu dao ngắt tự động khi quá số lần lỗi (Max Failures) hoặc chạm trần ngân sách Token (Token Budget Ceiling).
  * `MailboxManager`: Trạm giao nhận thư bất đồng bộ (Inbox/Outbox/Archive) giúp tách rời Orchestrator khỏi Worker, chấm dứt việc treo máy (blocking wait).
  * CLI tool `ron-guard`: Giúp máy local kiểm tra trạng thái và phát vé tác vụ nhanh chóng.

---

## 2. Ba Cấp Độ Phòng Thủ Chống "Cháy Quota"

```
[Orchestrator] ---> [Giao việc cho Worker]
                           |
            +--------------+--------------+
            | (Mất kết nối / Timeout / Lỗi) |
            v                             v
   [CƠ CHẾ CŨ (NGUY HIỂM)]       [RON MCP COMMANDER (AN TOÀN)]
   Tự lao đầu vào làm thay       CẦU DAO NGẮT MẠCH (CIRCUIT BREAKER)
   Đọc file khổng lồ              Trạng thái: OPEN (Fail-Closed)
   Bùng nổ Context                DẬM CHÂN TẠI CHỖ (HALT)
   ==> ĐỐT SẠCH QUOTA!            ==> BẢO TOÀN 100% QUOTA!
```

1. **Anti-Greedy Interceptor:** Phát hiện và chặn đứng ngay lập tức nếu Orchestrator cố tình thực hiện một task đã được giao cho Worker.
2. **Consecutive Failure Ceiling:** Sau tối đa 2 lần gọi Worker không thành công, cầu dao tự động bung (`OPEN`), từ chối mọi yêu cầu tiếp theo để bảo vệ tài khoản.
3. **Hard Token Budget Ceiling:** Đặt trần ngân sách token cứng (ví dụ: 20,000 tokens). Khi chạm trần, hệ thống lập tức ngắt tiến trình (`QuotaBudgetExceededError`).

---

## 3. Cài Đặt & Chạy Thử trên Căn Cứ Mặt Đất

### Yêu cầu
* Python 3.9 trở lên.
* Không có thư viện phụ thuộc ngoài (Pure Python Standard Library).

### Chạy Unit Test kiểm chứng
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

### Sử dụng CLI `ron-guard`
```bash
# Kiểm tra trạng thái cầu dao và ngân sách token
PYTHONPATH=src python3 -m ron_mcp_commander.cli status --budget 20000

# Phát một vé tác vụ bất đồng bộ vào Inbox cho Worker local (Ollama)
PYTHONPATH=src python3 -m ron_mcp_commander.cli dispatch \
  --action "parse_subtitles" \
  --worker "local-ollama" \
  --payload '{"file": "episode_01.srt"}'

# Kiểm tra kết quả xử lý của vé từ Outbox
PYTHONPATH=src python3 -m ron_mcp_commander.cli check --ticket-id "<TICKET_ID>"
```

---

## 4. Tích Hợp Vào Cấu Hình Antigravity Local / Kilo

Để bảo vệ Antigravity local không bao giờ tự ý cày code làm cháy quota, hãy nạp đoạn chỉ thị sau vào System Prompt hoặc file cấu hình Agent:

```markdown
### SYSTEM DIRECTIVE: ANTI-GREEDY DELEGATION CONTRACT
1. You are an Orchestrator. When a subagent, worker, or tool call times out or fails:
   - YOU ARE STRICTLY FORBIDDEN FROM EXECUTING THE TASK YOURSELF.
   - DO NOT read source code or heavy files to compensate for worker failure.
   - Immediately HALT, output status 'HALTED_DELEGATION_FAILED', and wait for Ron's manual inspection.
```

---

## 5. Bản Quyền & Giấy Phép
Phát triển độc lập thuộc hệ sinh thái RON-SHO. Tuân thủ nghiêm ngặt nguyên tắc **Evidence Before Claims** và **Human Sovereignty**.