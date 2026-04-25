import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    os.makedirs('results', exist_ok=True)
    
    if not os.path.exists('rewards_log.csv'):
        print("No rewards_log.csv found. Run inference first.")
        return
        
    try:
        df = pd.read_csv('rewards_log.csv')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
        
    if df.empty:
        print("rewards_log.csv is empty.")
        return

    # Plot 1: Reward Curve over Training Steps (using index as training step)
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['reward'], alpha=0.3, label='Episode Reward')
    
    # 10-step rolling average
    rolling_avg = df['reward'].rolling(window=10, min_periods=1).mean()
    plt.plot(df.index, rolling_avg, color='red', linewidth=2, label='10-step Rolling Average')
    
    plt.xlabel('Training Step')
    plt.ylabel('Episode Reward (0-1)')
    plt.title('Reward Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('results/reward_curve.png')
    plt.close()
    
    # Plot 2: Average Reward per Task ID
    plt.figure(figsize=(10, 6))
    avg_per_task = df.groupby('task_id')['reward'].mean().sort_values()
    avg_per_task.plot(kind='barh', color='skyblue')
    plt.xlabel('Average Episode Reward (0-1)')
    plt.ylabel('Task ID')
    plt.title('Average Reward by Task ID')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/reward_by_task.png')
    plt.close()
    
    print("Plots saved to results/ directory.")

if __name__ == "__main__":
    main()
