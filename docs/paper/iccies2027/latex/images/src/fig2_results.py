"""Figure 2: (a) security/utility trade-off on Dev; (b) harmful fixtures by mechanism on Test-I.

Usage: python fig2_results.py --lang vi|en --out ../fig2_results.pdf
Numbers: docs/paper/iccies2027/facts.md and docs/research/study2_thesis_tables.md (Tables 5 and 7 of the outline).
Pooled values are sums over the three backbones (Gemma-4-12B, Llama-3.1-8B, Qwen3.5-9B).
"""
from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"
AQUA, BLUE, ORANGE = "#1baf7a", "#2a78d6", "#eb6834"  # validated: all-pairs PASS (light)

# Dev, per backbone: (harmful families /48, benign_plain /240, benign_auth /80) for Gemma, Llama, Qwen
DEV = {
    "NoDef": [(38, 159, 54), (34, 81, 30), (40, 140, 36)],
    "Spotlight": [(24, 146, 54), (24, 74, 36), (43, 137, 38)],
    "Sandwich": [(7, 150, 54), (13, 84, 40), (11, 144, 32)],
    "PromptGuard": [(39, 160, 54), (34, 81, 30), (40, 139, 36)],
    "MELON-det": [(38, 160, 54), (34, 79, 30), (40, 142, 36)],
    "Progent-pol": [(21, 160, 54), (18, 80, 32), (22, 138, 36)],
    "PhraseRules": [(36, 160, 49), (25, 80, 27), (33, 138, 33)],
    "Rules": [(17, 158, 44), (13, 80, 27), (15, 136, 28)],
    "Rules+Sandwich": [(2, 147, 45), (5, 82, 36), (3, 141, 24)],
    "BrokerGuard": [(2, 148, 49), (5, 85, 40), (3, 141, 27)],
}
# Test v3 pooled harmful attack fixtures by mechanism (/180 each): ER, CR, SL, AL, PT, US
MECH = ["ER", "CR", "SL", "AL", "PT", "US"]
TEST1 = {
    "NoDef": [58, 65, 89, 60, 68, 15],
    "Sandwich": [1, 1, 27, 18, 10, 4],
    "Rules": [0, 0, 29, 17, 25, 1],
    "Rules+Sandwich": [0, 0, 6, 3, 4, 0],
}

TXT = {
    "vi": {"xa": "Tiện ích lành tính trên Dev (%, /960)", "ya": "Họ gây hại trên Dev (/144)",
           "yb": "Ca tấn công gây hại (/180)", "ta": "(a) Đánh đổi an ninh – tiện ích (Dev)",
           "tb": "(b) Theo cơ chế tấn công (Test-I)", "cluster": "NoDef, PromptGuard,\nMELON-det"},
    "en": {"xa": "Benign utility on Dev (%, /960)", "ya": "Harmful families on Dev (/144)",
           "yb": "Harmful attack fixtures (/180)", "ta": "(a) Security–utility trade-off (Dev)",
           "tb": "(b) By attack mechanism (Test-I)", "cluster": "NoDef, PromptGuard,\nMELON-det"},
}

# label offsets (points) to avoid collisions; cluster members get one shared label
OFFS = {"Spotlight": (-5, -2), "Sandwich": (4, 2), "Progent-pol": (4, -2), "PhraseRules": (4, 5),
        "Rules": (4, 0), "Rules+Sandwich": (-4, 6), "BrokerGuard": (4, 5)}
HA = {"Spotlight": "right", "Rules+Sandwich": "right"}


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
        ax.spines[s].set_linewidth(0.6)
    ax.tick_params(colors=MUTED, labelsize=6.2, width=0.6, length=2.5)
    ax.yaxis.grid(True, color=GRID, lw=0.5)
    ax.set_axisbelow(True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["vi", "en"], default="vi")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    t = TXT[args.lang]
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                         "mathtext.fontset": "stix", "hatch.linewidth": 0.5})

    fig, (a, b) = plt.subplots(1, 2, figsize=(4.8, 2.05), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.38})

    # (a) trade-off scatter
    style(a)
    for name, cells in DEV.items():
        harm = sum(c[0] for c in cells)
        util = 100 * sum(c[1] + c[2] for c in cells) / 960
        ours = name == "BrokerGuard"
        a.scatter(util, harm, s=22 if ours else 12, color=BLUE if ours else INK, zorder=3,
                  edgecolors="white", linewidths=0.6)
        if name in OFFS:
            a.annotate(name, (util, harm), xytext=OFFS[name], textcoords="offset points", fontsize=5.6,
                       color=INK, ha=HA.get(name, "left"), va="center", weight="bold" if ours else "normal")
    a.annotate(t["cluster"], (52.08, 112.5), xytext=(-6, 0), textcoords="offset points", fontsize=5.6,
               ha="right", va="center", color=INK)
    a.set_xlim(48.6, 53.0)
    a.set_ylim(0, 125)
    a.set_xlabel(t["xa"], fontsize=6.4, color=INK)
    a.set_ylabel(t["ya"], fontsize=6.4, color=INK)
    a.set_title(t["ta"], fontsize=6.8, color=INK, loc="left", pad=4)

    # (b) grouped bars by mechanism
    style(b)
    series = [("NoDef", "white", INK, None), ("Sandwich", AQUA, AQUA, "////"),
              ("Rules", BLUE, BLUE, None), ("Rules+Sandwich", ORANGE, ORANGE, None)]
    n, w = len(series), 0.19
    for i, (name, fc, ec, hatch) in enumerate(series):
        xs = [k + (i - (n - 1) / 2) * (w + 0.02) for k in range(len(MECH))]
        b.bar(xs, TEST1[name], width=w, color=fc, edgecolor=ec if name == "NoDef" else "white",
              linewidth=0.6 if name == "NoDef" else 0.3, hatch=hatch, label=name, zorder=3)
    b.set_xticks(range(len(MECH)))
    b.set_xticklabels(MECH, fontsize=6.2)
    b.set_ylim(0, 100)
    b.set_ylabel(t["yb"], fontsize=6.4, color=INK)
    b.set_title(t["tb"], fontsize=6.8, color=INK, loc="left", pad=4)
    b.legend(fontsize=5.6, frameon=False, loc="upper right", handlelength=1.2, borderaxespad=0.1,
             labelspacing=0.25)

    fig.savefig(args.out, bbox_inches="tight", pad_inches=0.02, dpi=300)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
