"""
Advanced Analysis of LLM Finetuning Performance
Analyzes reward curves, complexity metrics, and fixer method effectiveness
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import Counter

os.makedirs('results', exist_ok=True)

# Load data
rewards_df = pd.read_csv('rewards_log.csv')
complexity_df = pd.read_csv('complexity_rewards.csv')

print("\n" + "="*70)
print("FINETUNING ANALYSIS REPORT")
print("="*70)

# ─── SUMMARY STATISTICS ──────────────────────────────────────────────────────
print("\n📊 TRAINING OVERVIEW")
print(f"Total Episodes: {len(rewards_df)}")
print(f"Unique Tasks: {rewards_df['task_id'].nunique()}")
print(f"Date Range: {rewards_df['timestamp'].iloc[0]} to {rewards_df['timestamp'].iloc[-1]}")
print(f"Avg Reward: {rewards_df['reward'].mean():.4f}")
print(f"Max Reward: {rewards_df['reward'].max():.4f}")
print(f"Min Reward: {rewards_df['reward'].min():.4f}")
print(f"Reward Std: {rewards_df['reward'].std():.4f}")

# ─── TASK BREAKDOWN ──────────────────────────────────────────────────────────
print("\n📋 PERFORMANCE BY TASK")
task_stats = rewards_df.groupby('task_id')['reward'].agg([
    ('Count', 'count'),
    ('Mean', 'mean'),
    ('Max', 'max'),
    ('Min', 'min'),
    ('Std', 'std')
]).round(4)
print(task_stats)

# ─── COMPLEXITY ANALYSIS ────────────────────────────────────────────────────────
print("\n⚡ COMPLEXITY VS REWARD ANALYSIS")
complexity_stats = complexity_df.groupby('complexity')['reward'].agg([
    ('Count', 'count'),
    ('Mean Reward', 'mean'),
    ('Max Reward', 'max'),
    ('Min Reward', 'min')
]).round(4)
print(complexity_stats)

# ─── METHOD PERFORMANCE ──────────────────────────────────────────────────────
print("\n🔧 FIXER METHOD EFFECTIVENESS")
method_stats = complexity_df.groupby('method')['reward'].agg([
    ('Count', 'count'),
    ('Mean Reward', 'mean'),
    ('Max Reward', 'max'),
    ('Min Reward', 'min')
]).round(4)
print(method_stats)

# ─── COMPLEXITY BREAKDOWN ──────────────────────────────────────────────────────
print("\n🔄 COMPLEXITY DISTRIBUTION")
complexity_counts = complexity_df['complexity'].value_counts().sort_values(ascending=False)
print(complexity_counts)

# ─── GRAPH 1: Complexity vs Reward Scatter ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
colors = {'ollama': 'blue', 'builtin': 'red', 'tgi': 'green'}
for method in complexity_df['method'].unique():
    df_method = complexity_df[complexity_df['method'] == method]
    ax.scatter(range(len(df_method)), df_method['reward'], 
              label=f"{method.capitalize()} (n={len(df_method)})",
              alpha=0.6, s=60, color=colors.get(method, 'gray'))

ax.set_xlabel('Sample Index', fontsize=11)
ax.set_ylabel('Reward Score (0-1)', fontsize=11)
ax.set_title('LLM Fixer Method Performance Comparison', fontsize=13, fontweight='bold')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/method_performance.png', dpi=150)
plt.close()
print("\n✓ Saved: method_performance.png")

# ─── GRAPH 2: Complexity Distribution (Pie + Bar) ──────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Pie chart
colors_pie = plt.cm.Set3(np.linspace(0, 1, len(complexity_counts)))
ax1.pie(complexity_counts.values, labels=complexity_counts.index, autopct='%1.1f%%',
        colors=colors_pie, startangle=90)
ax1.set_title('Complexity Distribution in Dataset', fontsize=12, fontweight='bold')

# Bar chart
complexity_counts.plot(kind='bar', ax=ax2, color='skyblue', edgecolor='navy', alpha=0.7)
ax2.set_xlabel('Time Complexity Class', fontsize=11)
ax2.set_ylabel('Number of Samples', fontsize=11)
ax2.set_title('Complexity Class Frequency', fontsize=12, fontweight='bold')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('results/complexity_distribution.png', dpi=150)
plt.close()
print("✓ Saved: complexity_distribution.png")

# ─── GRAPH 3: Method Performance Box Plot ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
method_data = [complexity_df[complexity_df['method'] == m]['reward'].values 
               for m in complexity_df['method'].unique()]
bp = ax.boxplot(method_data, labels=complexity_df['method'].unique(), patch_artist=True)

for patch, color in zip(bp['boxes'], ['lightblue', 'lightcoral', 'lightgreen'][:len(bp['boxes'])]):
    patch.set_facecolor(color)

ax.set_xlabel('Fixer Method', fontsize=11)
ax.set_ylabel('Reward Score (0-1)', fontsize=11)
ax.set_title('Reward Distribution by Fixer Method', fontsize=13, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('results/method_boxplot.png', dpi=150)
plt.close()
print("✓ Saved: method_boxplot.png")

# ─── GRAPH 4: Task Performance Heatmap ──────────────────────────────────────────
task_reward_matrix = rewards_df.pivot_table(
    values='reward', 
    index='task_id', 
    aggfunc=['mean', 'max', 'std']
)
task_reward_matrix = task_reward_matrix.droplevel(0, axis=1)

fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(task_reward_matrix.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(task_reward_matrix.columns)))
ax.set_yticks(range(len(task_reward_matrix.index)))
ax.set_xticklabels(task_reward_matrix.columns, rotation=45)
ax.set_yticklabels(task_reward_matrix.index)
ax.set_title('Task Difficulty Performance Matrix (Mean, Max, Std)', fontsize=13, fontweight='bold')

# Add text annotations
for i in range(len(task_reward_matrix.index)):
    for j in range(len(task_reward_matrix.columns)):
        text = ax.text(j, i, f'{task_reward_matrix.values[i, j]:.2f}',
                      ha="center", va="center", color="black", fontsize=9)

plt.colorbar(im, ax=ax, label='Reward Score')
plt.tight_layout()
plt.savefig('results/task_performance_matrix.png', dpi=150)
plt.close()
print("✓ Saved: task_performance_matrix.png")

# ─── GRAPH 5: Cumulative Reward Over Time ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
sorted_rewards = complexity_df.sort_values('timestamp')
cumulative_reward = sorted_rewards['reward'].cumsum()

ax.plot(range(len(cumulative_reward)), cumulative_reward, marker='o', 
        markersize=4, linewidth=2, color='darkblue', alpha=0.7, label='Cumulative Reward')
ax.fill_between(range(len(cumulative_reward)), cumulative_reward, alpha=0.2, color='blue')

ax.set_xlabel('Sample Index (Chronological)', fontsize=11)
ax.set_ylabel('Cumulative Reward', fontsize=11)
ax.set_title('Cumulative Reward Trajectory', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig('results/cumulative_reward.png', dpi=150)
plt.close()
print("✓ Saved: cumulative_reward.png")

# ─── FINAL SUMMARY ──────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("✅ ALL GRAPHS GENERATED IN results/ DIRECTORY:")
print("  • reward_curve.png (rolling avg of rewards)")
print("  • reward_by_task.png (task-wise comparison)")
print("  • method_performance.png (fixer methods)")
print("  • complexity_distribution.png (algorithm classes)")
print("  • method_boxplot.png (reward distribution)")
print("  • task_performance_matrix.png (heatmap)")
print("  • cumulative_reward.png (training trajectory)")
print("="*70 + "\n")
