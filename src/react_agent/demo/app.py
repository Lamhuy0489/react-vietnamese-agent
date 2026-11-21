"""Gradio 5 chat UI for BrokerGuard demo sessions."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast

import gradio as gr
from gradio import ChatMessage

from react_agent.demo.config import ROOT, DemoConfig, Mode
from react_agent.demo.corpus import DemoDocument
from react_agent.demo.outbox import Outbox
from react_agent.demo.session import DemoSession
from react_agent.demo.trace_view import Step, explain

STATUS_VI: dict[str, str] = {
    "pending": "Chờ xác nhận",
    "sent": "Đã gửi",
    "rejected": "Đã hủy",
    "blocked_allowlist": "Bị chặn (ngoài danh sách)",
    "over_limit": "Hết hạn mức",
    "failed": "Lỗi",
}

OUTBOX_COLUMNS = ["Mã", "Người nhận", "Tiêu đề", "Trạng thái", "Ghi chú"]
DOCUMENT_COLUMNS = ["Mã tài liệu", "Tiêu đề", "Độ nhạy cảm", "Độ tin cậy"]


def format_banner(config: DemoConfig) -> str:
    """Render a visible status banner for email mode, model repo, and task independence."""
    email_status = (
        "🔴 **LIVE (Gmail thật)**" if config.email_live else "🟡 **Chỉ chạy thử (Giả lập)**"
    )
    model_name = config.model_repo or "Chưa cấu hình"
    return (
        f"**Trạng thái e-mail:** {email_status} &nbsp;|&nbsp; "
        f"**Mô hình:** `{model_name}`\n\n"
        f"ℹ️ *Lưu ý: Mỗi tin nhắn là một tác vụ độc lập (không ghi nhớ ngữ cảnh câu trước).*"
    )


def format_blocked_message(blocked_steps: list[Step]) -> str:
    """Format explanation for actions intercepted by BrokerGuard."""
    n = len(blocked_steps)
    lines = [f"🛡️ BrokerGuard đã chặn {n} hành động:"]
    for s in blocked_steps:
        reason_text = explain(s.reasons)
        lines.append(f"- **Bước {s.index} ({s.tool})**: {reason_text}")
    return "\n".join(lines)


def format_final_answer(mode: Mode, final_answer: str | None) -> str:
    """Format the final assistant message prefixed with the mode label."""
    label = "BrokerGuard v3" if mode == "V3" else "A0"
    text = final_answer or "(Không có câu trả lời cuối)"
    return f"[{label}] {text}"


def format_outbox_table(outbox: Outbox) -> list[list[str]]:
    """Convert outbox records into localized table rows."""
    rows: list[list[str]] = []
    for item in outbox.items:
        status_label = STATUS_VI.get(item.status, item.status)
        rows.append([
            item.item_id,
            item.to,
            item.subject,
            status_label,
            item.note,
        ])
    return rows


def format_item_preview(outbox: Outbox, item_id: str | None) -> str:
    """Render markdown preview of the selected outbox message."""
    if not item_id:
        return "*Chưa chọn thư nào để xem trước.*"
    for item in outbox.items:
        if item.item_id == item_id:
            status_label = STATUS_VI.get(item.status, item.status)
            note_line = f"\n- **Ghi chú:** {item.note}" if item.note else ""
            return (
                f"### Xem trước thư: `{item.item_id}`\n\n"
                f"- **Người nhận (To):** `{item.to}`\n"
                f"- **Tiêu đề (Subject):** {item.subject}\n"
                f"- **Trạng thái:** {status_label}{note_line}\n\n"
                "**Nội dung (Body):**\n\n"
                + "\n".join("    " + line for line in item.body.splitlines())
            )
    return "*Không tìm thấy thông tin thư đã chọn.*"


def format_documents_table(documents: list[DemoDocument]) -> list[list[str]]:
    """Format the demo document catalog for table display."""
    return [
        [doc.doc_id, doc.title, doc.sensitivity, doc.trust]
        for doc in documents
    ]


def get_pending_choices(outbox: Outbox) -> list[str]:
    """Retrieve list of item IDs pending confirmation."""
    return [item.item_id for item in outbox.pending()]


def load_scenarios_markdown() -> str:
    """Read the demo scenarios file if present."""
    path = ROOT / "data/demo/scenarios.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "*Không tìm thấy tệp kịch bản mẫu (`data/demo/scenarios.md`).*"


def build_app(session: DemoSession) -> gr.Blocks:
    """Build the Gradio 5 blocks application for BrokerGuard."""
    with gr.Blocks(title="BrokerGuard Chat") as demo:
        gr.Markdown(
            "# 🛡️ BrokerGuard Chat\n"
            "Giao diện thử nghiệm phòng thủ prompt injection gián tiếp và rò rỉ dữ liệu "
            "cho AI Agent."
        )
        gr.Markdown(format_banner(session.config))

        with gr.Row():
            with gr.Column(scale=7):
                mode_radio = gr.Radio(
                    choices=[
                        ("BrokerGuard v3 (có bảo vệ)", "V3"),
                        ("A0 (không bảo vệ)", "A0"),
                    ],
                    value=session.config.default_mode,
                    label="Chế độ bảo vệ",
                )
                chatbot = gr.Chatbot(
                    label="Hội thoại",
                    type="messages",
                    height=520,
                )
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="Nhập yêu cầu tác vụ cho Agent...",
                        label="Tin nhắn người dùng",
                        lines=2,
                        scale=5,
                    )
                    send_btn = gr.Button("Gửi", variant="primary", scale=1)
                clear_btn = gr.Button("Xóa hội thoại", variant="secondary")

            with gr.Column(scale=5):
                gr.Markdown("### 📬 Hộp thư chờ")
                outbox_df = gr.Dataframe(
                    headers=OUTBOX_COLUMNS,
                    datatype=["str", "str", "str", "str", "str"],
                    value=format_outbox_table(session.outbox),
                    interactive=False,
                    wrap=True,
                )
                initial_pending = get_pending_choices(session.outbox)
                initial_selected = initial_pending[0] if initial_pending else None
                pending_dropdown = gr.Dropdown(
                    choices=initial_pending,
                    value=initial_selected,
                    label="Chọn thư chờ xử lý",
                )
                preview_md = gr.Markdown(
                    format_item_preview(session.outbox, initial_selected)
                )
                with gr.Row():
                    confirm_btn = gr.Button("✉️ Gửi thật", variant="primary")
                    reject_btn = gr.Button("Hủy", variant="stop")
                action_status = gr.Markdown("")

        with gr.Accordion("Kho tài liệu demo", open=False):
            gr.Dataframe(
                headers=DOCUMENT_COLUMNS,
                datatype=["str", "str", "str", "str"],
                value=format_documents_table(session.documents),
                interactive=False,
                wrap=True,
            )

        with gr.Accordion("Câu lệnh mẫu", open=False):
            gr.Markdown(load_scenarios_markdown())

        def handle_submit(
            message: str,
            mode: str,
            history: list[ChatMessage] | list[dict[str, Any]] | None,
            current_pending: str | None,
        ) -> Generator[tuple[Any, ...], None, None]:
            cleaned = message.strip()
            if not cleaned:
                yield (
                    history or [],
                    gr.update(value=""),
                    gr.update(interactive=True),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
                return

            target_mode: Mode = "A0" if mode == "A0" else "V3"
            current_history = list(history or [])
            current_history.append(ChatMessage(role="user", content=cleaned))
            current_history.append(ChatMessage(role="assistant", content="⏳ Đang chạy..."))

            yield (
                current_history,
                gr.update(value="", interactive=False),
                gr.update(interactive=False),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

            try:
                result = session.run(cleaned, mode=target_mode)
            except Exception as exc:  # noqa: BLE001 - shown in the chat, UI must stay usable
                current_history[-1] = ChatMessage(
                    role="assistant", content=f"⚠️ Lỗi: {type(exc).__name__}: {exc}")
                yield (current_history, gr.update(value="", interactive=True),
                       gr.update(interactive=True), gr.update(), gr.update(), gr.update(),
                       gr.update())
                return

            final_history = list(current_history[:-1])
            for step in result.view.steps:
                final_history.append(
                    ChatMessage(
                        role="assistant",
                        content=step.body(),
                        metadata={"title": step.title(), "status": "done"},
                    )
                )

            if result.view.blocked:
                final_history.append(
                    ChatMessage(
                        role="assistant",
                        content=format_blocked_message(result.view.blocked),
                    )
                )

            final_history.append(
                ChatMessage(
                    role="assistant",
                    content=format_final_answer(result.mode, result.view.final_answer),
                )
            )

            if result.error:
                final_history.append(
                    ChatMessage(
                        role="assistant",
                        content=f"⚠️ Lỗi: {result.error}",
                    )
                )

            table_data = format_outbox_table(session.outbox)
            pending_ids = get_pending_choices(session.outbox)
            next_pending = (
                current_pending
                if (current_pending and current_pending in pending_ids)
                else (pending_ids[0] if pending_ids else None)
            )
            preview = format_item_preview(session.outbox, next_pending)

            yield (
                final_history,
                gr.update(value="", interactive=True),
                gr.update(interactive=True),
                table_data,
                gr.update(choices=pending_ids, value=next_pending),
                preview,
                gr.update(),
            )

        def handle_select_pending(item_id: str | None) -> str:
            return format_item_preview(session.outbox, item_id)

        def handle_confirm(
            item_id: str | None,
        ) -> tuple[list[list[str]], Any, str, str]:
            if not item_id:
                return (
                    format_outbox_table(session.outbox),
                    gr.update(),
                    format_item_preview(session.outbox, None),
                    "⚠️ Vui lòng chọn một thư trong danh sách chờ để gửi.",
                )
            try:
                item = session.outbox.confirm(item_id)
                status_label = STATUS_VI.get(item.status, item.status)
                note_text = f" ({item.note})" if item.note else ""
                msg = f"Đã thực hiện gửi thư `{item.item_id}`: **{status_label}**{note_text}"
            except KeyError:
                msg = f"⚠️ Không tìm thấy thư với mã `{item_id}`."

            table_data = format_outbox_table(session.outbox)
            pending_ids = get_pending_choices(session.outbox)
            next_id = pending_ids[0] if pending_ids else None
            return (
                table_data,
                gr.update(choices=pending_ids, value=next_id),
                format_item_preview(session.outbox, next_id),
                msg,
            )

        def handle_reject(
            item_id: str | None,
        ) -> tuple[list[list[str]], Any, str, str]:
            if not item_id:
                return (
                    format_outbox_table(session.outbox),
                    gr.update(),
                    format_item_preview(session.outbox, None),
                    "⚠️ Vui lòng chọn một thư trong danh sách chờ để hủy.",
                )
            try:
                item = session.outbox.reject(item_id)
                status_label = STATUS_VI.get(item.status, item.status)
                note_text = f" ({item.note})" if item.note else ""
                msg = f"Đã hủy thư `{item.item_id}`: **{status_label}**{note_text}"
            except KeyError:
                msg = f"⚠️ Không tìm thấy thư với mã `{item_id}`."

            table_data = format_outbox_table(session.outbox)
            pending_ids = get_pending_choices(session.outbox)
            next_id = pending_ids[0] if pending_ids else None
            return (
                table_data,
                gr.update(choices=pending_ids, value=next_id),
                format_item_preview(session.outbox, next_id),
                msg,
            )

        def handle_clear_chat() -> list[ChatMessage]:
            return []

        pending_dropdown.change(
            fn=handle_select_pending,
            inputs=[pending_dropdown],
            outputs=[preview_md],
        )

        confirm_btn.click(
            fn=handle_confirm,
            inputs=[pending_dropdown],
            outputs=[outbox_df, pending_dropdown, preview_md, action_status],
        )

        reject_btn.click(
            fn=handle_reject,
            inputs=[pending_dropdown],
            outputs=[outbox_df, pending_dropdown, preview_md, action_status],
        )

        clear_btn.click(
            fn=handle_clear_chat,
            outputs=[chatbot],
        )

        submit_inputs = [user_input, mode_radio, chatbot, pending_dropdown]
        submit_outputs = [chatbot, user_input, send_btn, outbox_df, pending_dropdown, preview_md,
                          action_status]
        user_input.submit(fn=handle_submit, inputs=submit_inputs, outputs=submit_outputs)
        send_btn.click(fn=handle_submit, inputs=submit_inputs, outputs=submit_outputs)

    return cast(gr.Blocks, demo)
