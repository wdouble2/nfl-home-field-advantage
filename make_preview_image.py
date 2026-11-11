"""Make the 1200x630 link-preview image for wdouble2.github.io (images/preview.png).

Run:  .venv/bin/python make_preview_image.py  [output path]
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else "../portfolio-site/images/preview.png"
a = pd.read_csv("data/season_adjusted_hfa.csv")   # written by the deep dive
BG, PANEL, LINE, TEXT, MUTED, DIM = "#0A0A0A", "#141414", "#262626", "#F5F5F5", "#A3A3A3", "#5C5C5C"
SANS, MONO = "Helvetica Neue", "Menlo"

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
bg = fig.add_axes([0, 0, 1, 1], zorder=0); bg.set_xlim(0, 1200); bg.set_ylim(0, 630); bg.axis("off")
xs, ys = np.meshgrid(np.arange(12, 1200, 24), np.arange(12, 630, 24))
fade = np.clip(0.16 - np.hypot((xs - 300) / 700, (ys - 420) / 420) * 0.13, 0, 0.16)
bg.scatter(xs, ys, s=1.6, c=TEXT, alpha=fade, linewidths=0)
bg.add_patch(FancyBboxPatch((702, 85), 444, 460, boxstyle="round,pad=0,rounding_size=18", facecolor=PANEL, edgecolor=LINE, linewidth=1.2))

fig.text(0.06, 0.865, "WILLIAM DOUBLE  ·  DATA PROFESSIONAL, SPORTS ANALYTICS", color=MUTED, fontsize=12.5, family=MONO)
for i, line in enumerate(["How much is NFL", "home field really", "worth?"]):
    fig.text(0.06, 0.745 - 0.1 * i, line, color=TEXT, fontsize=46, family=SANS, weight="bold")
fig.text(0.06, 0.445, "27 seasons  ·  6,878 games  ·  Python + SQL", color=MUTED, fontsize=16, family=SANS)
x = 0.06
for big, small in [("+2.3 pts", "home field, 1999–2025"), ("+0.1 pts", "in 2020, few fans"), ("p = 0.006", "the drop is real")]:
    fig.text(x, 0.255, big, color=TEXT, fontsize=27, family=SANS, weight="bold")
    fig.text(x, 0.205, small, color=MUTED, fontsize=12.5, family=SANS)
    x += 0.165
fig.text(0.06, 0.075, "wdouble2.github.io", color=TEXT, fontsize=15, family=MONO)
fig.text(0.268, 0.077, "·   live SQL, interactive charts, team explorer", color=MUTED, fontsize=13, family=SANS)

fig.text(0.61, 0.805, "HOME EDGE BY SEASON, PTS", color=MUTED, fontsize=10.5, family=MONO)
fig.text(0.61, 0.755, "Vanished in 2020", color=TEXT, fontsize=17, family=SANS, weight="bold")
ax = fig.add_axes([0.625, 0.235, 0.305, 0.48], zorder=2); ax.set_facecolor("none")
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0, labelsize=10)
ax.set_ylim(-2, 6); ax.set_yticks([0, 2, 4]); ax.set_yticklabels(["0", "+2", "+4"], family=MONO, color=DIM)
ax.set_xticks([2000, 2010]); ax.set_xticklabels(["2000", "2010"], family=MONO, color=DIM)
ax.grid(axis="y", color="#222222", lw=1); ax.set_axisbelow(True)
ax.axhline(0, color=DIM, lw=1, ls=(0, (3, 3)))
n = a[a.season != 2020]; c = a[a.season == 2020].iloc[0]
ax.vlines(n.season, n.lo, n.hi, color=TEXT, alpha=0.22, lw=2.4)
for lo, hi in [(1999, 2009), (2010, 2019), (2021, 2025)]:          # era averages (inverse-variance weighted)
    e = a[a.season.between(lo, hi)]; w = 1 / e.se ** 2
    ax.hlines(np.average(e.adj_hfa, weights=w), lo - 0.4, hi + 0.4, color=MUTED, lw=1.8)
ax.scatter(n.season, n.adj_hfa, s=22, color=TEXT, zorder=3, edgecolors=PANEL, linewidths=1)
ax.vlines([2020], [c.lo], [c.hi], color=TEXT, alpha=0.5, lw=2.4)
ax.scatter([2020], [c.adj_hfa], s=90, facecolor=PANEL, edgecolor=TEXT, linewidth=2.2, zorder=4)
ax.annotate("2020", (2020, c.lo), xytext=(0, -14), textcoords="offset points", ha="center", color=TEXT, fontsize=10.5, family=SANS, weight="bold")
ax.set_xlim(1998, 2026.5)
fig.text(0.625, 0.165, "●  home edge (95% CI)      —  era averages +2.6, +2.2, +2.0", color=MUTED, fontsize=10, family=SANS)
fig.savefig(OUT, dpi=100, facecolor=BG)
print("wrote", OUT)
