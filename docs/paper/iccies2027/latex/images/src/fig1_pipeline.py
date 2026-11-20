"""Figure 1: the defence pipeline (Tool Broker mediating every call).

Usage: python fig1_pipeline.py --lang vi|en --out ../fig1_pipeline.pdf
Solid blue boxes = deterministic host-side checks; dashed orange box = model-dependent layer.
"""
from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

INK = "#0b0b0b"
MUTED = "#52514e"
RULE_FILL = "#e3eefb"  # light step of categorical slot 1 (blue)
RULE_EDGE = "#2a78d6"
SOFT_FILL = "#fdeee6"  # light step of slot 2 (orange): model-dependent layer
SOFT_EDGE = "#eb6834"
NEUTRAL_FILL = "#f2f1ee"
DASH = (0, (3, 2))

TXT = {
    "vi": {
        "user": "Người dùng\nchỉ thị $u$\n(đáng tin)",
        "agent": "Tác tử LLM\n(ReAct)",
        "broker": "Tool Broker (phía host)",
        "l0": "Kiểm schema và giới hạn · gán nhãn tin cậy, nhạy cảm · trích giá trị mật $C$",
        "row1": "trước mỗi lời gọi sink",
        "dest": "R-Dest\nđích phải có trong $u$",
        "flow": "R-Flow\ngiá trị mật chỉ được ra\nnếu có trong $u$",
        "sig": "R-Signal\nchặn nếu quan sát bị gắn\ncờ nêu đúng đích",
        "row2": "ở câu trả lời · trên đường quan sát · khi từ chối",
        "ans": "R-Flow + R-Redact\nche từng giá trị mật\ntrong câu trả lời",
        "remind": "Sandwich\nnhắc lại $u$ sau\nmỗi quan sát",
        "deny": "Phản hồi từ chối\nkhông chạy công cụ,\ntác tử làm tiếp",
        "read": "Công cụ đọc\nđầu ra không đáng tin,\ncó thể chứa lệnh chèn",
        "sink": "Sink: e-mail, webhook\nbản giả, không ra mạng",
        "out": "câu trả lời đã che",
        "legend_det": "kiểm tất định",
        "legend_soft": "phụ thuộc mô hình",
    },
    "en": {
        "user": "User\ninstruction $u$\n(trusted)",
        "agent": "LLM agent\n(ReAct)",
        "broker": "Tool Broker (host side)",
        "l0": "Schema and limits · trust and sensitivity labels · confidential values $C$",
        "row1": "before every sink call",
        "dest": "R-Dest\ndestination must\nappear in $u$",
        "flow": "R-Flow\nconfidential value leaves\nonly if written in $u$",
        "sig": "R-Signal\ndeny if a flagged\nobservation names it",
        "row2": "at the answer · on observations · on denial",
        "ans": "R-Flow + R-Redact\nredact each confidential\nvalue in the answer",
        "remind": "Sandwich\nrepeat $u$ after\neach observation",
        "deny": "Denial feedback\ntool not executed,\nagent continues",
        "read": "Read tools\nuntrusted output,\nmay carry injections",
        "sink": "Sinks: e-mail, webhook\nmocks, no network",
        "out": "redacted answer",
        "legend_det": "deterministic check",
        "legend_soft": "model-dependent",
    },
}


def box(ax, x, y, w, h, text, fill, edge, ls="-", size=5.6, weight="normal", lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08", fc=fill, ec=edge,
                                lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, weight=weight,
            linespacing=1.15)


def arrow(ax, x0, y0, x1, y1, label="", lx=0.0, ly=0.13):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, lw=0.8, color=MUTED,
                                 shrinkA=0, shrinkB=0))
    if label:
        ax.text((x0 + x1) / 2 + lx, (y0 + y1) / 2 + ly, label, fontsize=6.4, color=INK, ha="center",
                va="center")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["vi", "en"], default="vi")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    t = TXT[args.lang]

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "mathtext.fontset": "stix"})
    fig = plt.figure(figsize=(4.8, 2.2))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0.2, 4.6)
    ax.axis("off")

    # left column: user and agent
    box(ax, 0.0, 3.05, 1.25, 0.95, t["user"], NEUTRAL_FILL, MUTED, size=6.0)
    box(ax, 0.0, 1.0, 1.25, 1.3, t["agent"], NEUTRAL_FILL, MUTED, size=6.6, weight="bold")
    arrow(ax, 0.62, 3.05, 0.62, 2.3)

    # broker frame
    bx, by, bw, bh = 1.85, 0.55, 5.75, 4.0
    ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.12", fc="white",
                                ec=INK, lw=1.0))
    ax.text(bx + bw / 2, by + bh - 0.2, t["broker"], ha="center", va="center", fontsize=7.0, weight="bold")
    box(ax, bx + 0.12, 3.72, bw - 0.24, 0.35, t["l0"], RULE_FILL, RULE_EDGE, size=5.3)

    cw = (bw - 0.24 - 0.2) / 3
    ax.text(bx + 0.15, 3.53, t["row1"], fontsize=5.4, color=MUTED, va="center", style="italic")
    for i, key in enumerate(["dest", "flow", "sig"]):
        box(ax, bx + 0.12 + i * (cw + 0.1), 2.6, cw, 0.8, t[key], RULE_FILL, RULE_EDGE)
    ax.text(bx + 0.15, 2.4, t["row2"], fontsize=5.4, color=MUTED, va="center", style="italic")
    box(ax, bx + 0.12, 1.45, cw, 0.8, t["ans"], RULE_FILL, RULE_EDGE)
    box(ax, bx + 0.12 + (cw + 0.1), 1.45, cw, 0.8, t["remind"], SOFT_FILL, SOFT_EDGE, ls=DASH)
    box(ax, bx + 0.12 + 2 * (cw + 0.1), 1.45, cw, 0.8, t["deny"], RULE_FILL, RULE_EDGE)

    # legend
    ax.add_patch(FancyBboxPatch((bx + 0.15, 0.78), 0.28, 0.2, boxstyle="round,pad=0,rounding_size=0.03",
                                fc=RULE_FILL, ec=RULE_EDGE, lw=0.8))
    ax.text(bx + 0.52, 0.88, t["legend_det"], fontsize=5.4, va="center", color=MUTED)
    ax.add_patch(FancyBboxPatch((bx + 2.15, 0.78), 0.28, 0.2, boxstyle="round,pad=0,rounding_size=0.03",
                                fc=SOFT_FILL, ec=SOFT_EDGE, lw=0.8, ls=DASH))
    ax.text(bx + 2.52, 0.88, t["legend_soft"], fontsize=5.4, va="center", color=MUTED)

    # agent <-> broker: action, observation, final answer
    arrow(ax, 1.25, 2.05, bx, 2.05, "$a_t$")
    arrow(ax, bx, 1.65, 1.25, 1.65, "$o_t$")
    arrow(ax, 1.25, 1.2, bx, 1.2, "$y$")

    # tools column
    tx, tw = 8.2, 1.8
    box(ax, tx, 2.6, tw, 0.95, t["read"], NEUTRAL_FILL, MUTED, size=5.6)
    box(ax, tx, 1.45, tw, 0.8, t["sink"], NEUTRAL_FILL, MUTED, size=5.6)
    arrow(ax, bx + bw, 3.25, tx, 3.25, "$a_t$")
    arrow(ax, tx, 2.85, bx + bw, 2.85, "$o_t$")
    arrow(ax, bx + bw, 1.85, tx, 1.85, "$a_t$")

    # redacted answer leaves the broker
    arrow(ax, bx + bw, 0.85, tx + 0.35, 0.85)
    ax.text(tx + 0.42, 0.85, t["out"], fontsize=5.6, color=MUTED, va="center", ha="left")

    fig.savefig(args.out, bbox_inches="tight", pad_inches=0.02, dpi=300)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
