# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: A3 - C401
- [REPO_URL]: https://github.com/7kitan/Lab13-C401-A3
- [MEMBERS]:
  - Member A: Nguyễn Xuân Hoàng | Chịu trách nhiệm: logging + PII
  - Member B: Nguyễn Tuấn Kiệt | Chịu trách nhiệm: tracing + tags
  - Member C: Nguyễn Văn Bách | Chịu trách nhiệm: SLO + alerts
  - Member D: Trần Trọng Giang | Chịu trách nhiệm: load test + incident injection
  - Member E: Nguyễn Đức Duy | Chịu trách nhiệm: dashboard + evidence
  - Member F: Nguyễn Duy Hưng | Chịu trách nhiệm: blueprint + demo lead
---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 40
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- EVIDENCE_CORRELATION_ID_SCREENSHOT: ScreenShot\CORRELATION_ID_SCREENSHOT.png
- EVIDENCE_PII_REDACTION_SCREENSHOT: ScreenShot\PII_REDACTION_SCREENSHOT.png
- EVIDENCE_TRACE_WATERFALL_SCREENSHOT: ScreenShot\TRACE_WATERFALL_SCREENSHOT.png
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- DASHBOARD_6_PANELS_SCREENSHOT: ScreenShot\Dashboard-Monitor.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |

### 3.3 Alerts & Runbook
- ALERT_RULES_SCREENSHOT: ScreenShort\ALERT_RULES_SCREENSHOT.png
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Độ trễ (latency) của các requests tới tính năng `qa` hoặc liên quan đến truy xuất tài liệu đột ngột tăng mạnh vượt mốc 2500ms. Cảnh báo Latency P95 vi phạm ngưỡng cảnh báo trên hệ thống Dashboard.
- [ROOT_CAUSE_PROVED_BY]: Dựa vào cây Trace Waterfall trên Langfuse, phát hiện bộ phận `mock_llm_generate` hoạt động bình thường (~150ms), nhưng Span con `retrieve_docs` (thuộc Vector DB) tốn chính xác 2500ms. Log file cũng ghi nhận `latency_ms = 2650` đối với service `api`.
- [FIX_ACTION]: Tắt cờ `rag_slow` trong `incidents.py` và tối ưu hoá lại pipeline RAG trong `retrieve()` (gỡ code `time.sleep()`).
- [PREVENTIVE_MEASURE]: Thiết lập Alert Rules phụ trách tự động Paging cho On-Call Engineer ngay khi P95 của riêng Span `retrieve_docs` vọt qua ngưỡng 1000ms. Cân nhắc thêm cơ chế Caching (Redis) cho RAG.

---

## 5. Individual Contributions & Evidence

### Nguyễn Xuân Hoàng - Thiết lập Logging & Bảo vệ PII
- [TASKS_COMPLETED]: Xây dựng luồng logs bằng `structlog`, tích hợp `JsonlFileProcessor`. Triển khai thành công Regex lọc dữ liệu nhạy cảm (Passport, SDT Việt Nam) trong `pii.py`. Pass 100% PII test.
- [EVIDENCE_LINK]: 

### Nguyễn Tuấn Kiệt - Tích hợp Langfuse Tracing
- [TASKS_COMPLETED]: Cấu hình decorator `@observe()` của Langfuse, quản lý phân cấp Span Hierarchy (Parent Trace `chat-response` chứa các Span con `generation` và `retrieval`). Thiết lập PII Masking trên tracing inputs/outputs qua thuật tuán `summarize_text()`.
- [EVIDENCE_LINK]: 

### Nguyễn Văn Bách - Alerting & Tracking SLOs
- [TASKS_COMPLETED]: Đánh giá mức độ khả dụng của dịch vụ dựa trên Latency P95 và Error Rates, lên cấu hình `alert_rules.yaml`. Viết tài liệu Runbook `alerts.md` xử lý khi hệ thống vi phạm SLO.
- [EVIDENCE_LINK]: 

### Trần Trọng Giang - Giả lập Load Test & Incident
- [TASKS_COMPLETED]: Điều phối kịch bản kiểm thử tĩnh `load_test.py`, bơm traffic tạo ra 40+ Unique requests với đầy đủ `correlation_id` chéo. Khởi động tính năng `STATE["rag_slow"]` để đánh giá năng lực quan sát log của team.
- [EVIDENCE_LINK]: 

### Nguyễn Đức Duy - Data Visualization (Dashboard)
- [TASKS_COMPLETED]: Code giao diện Giám sát (Observability Dashboard) bằng công nghệ Streamlit. Vẽ biểu đồ hiển thị 6 metrics quan trọng: Token Usage, Lỗi API, Cost, và Distribution của Request Latency.
- [EVIDENCE_LINK]: 

### Nguyễn Duy Hưng - Blueprint & Tích hợp liên tục
- [TASKS_COMPLETED]: Tham gia khắc phục Root Cause vụ việc `rag_slow`, chạy `validate_logs.py` để verify điểm tuyệt đối 100/100, và trình diễn (demo) quá trình vận hành hệ thống.
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
