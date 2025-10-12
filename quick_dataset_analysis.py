#!/usr/bin/env python3
"""
Quick dataset analysis and visualization script
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
import seaborn as sns

def analyze_dataset(repo_id):
    print(f"🔍 Analyzing dataset: {repo_id}")
    
    # Load the dataset
    print("📥 Loading dataset...")
    dataset = LeRobotDataset(repo_id, root="data")
    
    print(f"📊 Dataset Statistics:")
    print(f"  - Total episodes: {dataset.num_episodes}")
    print(f"  - Total frames: {len(dataset)}")
    print(f"  - FPS: {dataset.fps}")
    print(f"  - Episode length: {dataset.episode_length}")
    
    # Get first episode data
    episode_data = []
    for i in range(len(dataset)):
        if dataset[i]['episode_index'] == 0:  # First episode
            episode_data.append({
                'frame': i,
                'timestamp': dataset[i]['timestamp'],
                'action': dataset[i]['action'].numpy(),
                'observation': dataset[i]['observation.state'].numpy()
            })
    
    print(f"\n📈 Episode 0 Analysis:")
    print(f"  - Frames in episode: {len(episode_data)}")
    
    # Convert to arrays for plotting
    frames = [d['frame'] for d in episode_data]
    actions = np.array([d['action'] for d in episode_data])
    observations = np.array([d['observation'] for d in episode_data])
    
    # Create visualizations
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'Dataset Analysis: {repo_id}', fontsize=16)
    
    # Plot each joint's action trajectory
    for i in range(6):  # 6 joints
        ax = axes[0, i % 3] if i < 3 else axes[1, i % 3]
        ax.plot(frames, actions[:, i], label=f'Action Joint {i+1}', alpha=0.7)
        ax.plot(frames, observations[:, i], label=f'Obs Joint {i+1}', alpha=0.7, linestyle='--')
        ax.set_title(f'Joint {i+1} Trajectory')
        ax.set_xlabel('Frame')
        ax.set_ylabel('Angle (degrees)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'dataset_analysis_{repo_id.replace("/", "_")}.png', dpi=150, bbox_inches='tight')
    print(f"📊 Saved plot: dataset_analysis_{repo_id.replace('/', '_')}.png")
    
    # Show action vs observation differences
    print(f"\n🔧 Action vs Observation Analysis:")
    differences = np.abs(actions - observations)
    mean_diff = np.mean(differences, axis=0)
    max_diff = np.max(differences, axis=0)
    
    for i in range(6):
        print(f"  Joint {i+1}: Mean diff = {mean_diff[i]:.2f}°, Max diff = {max_diff[i]:.2f}°")
    
    # Find large corrections (likely torque-off periods)
    large_corrections = differences > 1.0  # More than 1 degree difference
    correction_frames = np.any(large_corrections, axis=1)
    num_corrected_frames = np.sum(correction_frames)
    
    print(f"\n🎯 Torque Control Analysis:")
    print(f"  - Frames with corrections (>1° diff): {num_corrected_frames}/{len(frames)} ({100*num_corrected_frames/len(frames):.1f}%)")
    
    # Show correction distribution
    if num_corrected_frames > 0:
        corrected_frame_indices = np.where(correction_frames)[0]
        print(f"  - First correction at frame: {corrected_frame_indices[0]}")
        print(f"  - Last correction at frame: {corrected_frame_indices[-1]}")
    
    return dataset, episode_data

if __name__ == "__main__":
    repo_id = "NLTuan/dual_camera_torque_demo_v2_torque_corrected"
    dataset, episode_data = analyze_dataset(repo_id)
    
    print(f"\n✅ Analysis complete! Check the generated plot for visual trajectories.")
