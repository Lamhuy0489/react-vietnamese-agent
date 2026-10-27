# API và cách tiếp tục sau Phase 5

Cập nhật: 2026-10-02. Phase 5 đã accepted. Native84 và guard80 đều terminal;
không chạy lại hoặc resume để lấy kết quả tốt hơn.

## Phiên ngày mai

Bắt đầu từ [Phase 6 start](phase6_start.md) và [handoff](handoff.md): chốt metric,
đọc saved traces và viết golden tests có thể làm bằng CPU local, chưa cần API.
[Thông số và run roots](phase5_parameters.md) là mốc tái lập đã lưu.

## Khi cần bật API trở lại

1. Chỉ làm sau khi có scope Dev inference mới. Giữ hai notebook/worker theo
   [sổ tài nguyên](kaggle_resources.md), không mặc định launcher bốn model cũ.
2. API key/endpoint giữ trong ignored connection files; không in hoặc đưa vào
   knowledge. Tắt notebook không làm mất local manifests/raw nhưng worker boot,
   cache và tunnel có thể không còn. READY cũ không chứng minh còn online.
3. Xác minh role, model revision, source/prompt/config, session và boot thực tế.
   Source/model/boot mới phải có declaration mới, không giả resume identity cũ.
4. Trước inference kiểm journal còn unresolved; không xóa ledger, đổi root hoặc
   gửi lại semantic failure để vượt block. Giữ model/API failures trong báo cáo.
5. Mỗi run khai báo task IDs, generation, hashes, evaluator version và checkpoint;
   không cho private evaluator labels vào runtime. Test vẫn khóa.

## Lịch sử và khôi phục

Các lệnh release01–04a và mốc16/84 trước closure chỉ là lịch sử, đã chuyển sang
[runbook lịch sử](history_20261002_before_phase6_api_experiment_runbook.md).
Không tự chạy các lệnh đó khi mở chat mới. Gói bằng chứng local và raw roots
được giữ nguyên; [quy tắc lưu trữ](storage_and_obsidian.md) phân biệt hash, bản
sao local và backup ngoài máy. Dọn cache không cho phép xóa raw hoặc receipt.
