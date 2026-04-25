import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

LOG_FILE  = os.path.join(os.path.dirname(__file__), "rewards_log.csv")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(LOG_FILE)
df["global_step"] = range(len(df))
df["rolling_avg"] = df["reward"].rolling(window=10, min_periods=1).mean()

# -- Plot 1: Reward curve -------------------------------
fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(df["global_step"], df["reward"],
        alpha=0.25, color="#4A90D9", linewidth=1, label="raw reward")
ax.plot(df["global_step"], df["rolling_avg"],
        color="#1a5fa8", linewidth=2.5, label="10-step rolling avg")
ax.axhline(0.5, linestyle="--", color="#999999", linewidth=1, label="baseline (0.5)")

ax.set_xlabel("Training Step", fontsize=13)
ax.set_ylabel("Reward (0 - 1)", fontsize=13)
ax.set_title("CodeArena - Agent Reward Over Training", fontsize=15, fontweight="bold")
ax.set_ylim(0, 1.05)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "reward_curve.png"), dpi=150)
plt.close()
print("Saved: results/reward_curve.png")

# -- Plot 2: Reward by task -----------------------------
task_avg = df.groupby("task_id")["reward"].mean().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#2ecc71" if v > 0.7 else "#f39c12" if v > 0.4 else "#e74c3c"
          for v in task_avg.values]
bars = ax.bar(task_avg.index, task_avg.values, color=colors, edgecolor="white", width=0.5)

for bar, val in zip(bars, task_avg.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f"{val:.2f}", ha="center", fontsize=11, fontweight="bold")

ax.set_xlabel("Task Category", fontsize=13)
ax.set_ylabel("Average Reward", fontsize=13)
ax.set_title("CodeArena - Average Reward by Task Category", fontsize=15, fontweight="bold")
ax.set_ylim(0, 1.15)
ax.grid(axis="y", alpha=0.3)

legend_patches = [
    mpatches.Patch(color="#2ecc71", label="> 0.70 (strong)"),
    mpatches.Patch(color="#f39c12", label="0.40-0.70 (learning)"),
    mpatches.Patch(color="#e74c3c", label="< 0.40 (struggling)")
]
ax.legend(handles=legend_patches, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "reward_by_task.png"), dpi=150)
plt.close()
print("Saved: results/reward_by_task.png")
print("\nAll plots saved to results/")
