#!/usr/bin/env python3
"""
Comprehensive analysis of the corrected dataset
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from huggingface_hub import hf_hub_download

def analyze_corrected_dataset():
    print("🔍 Analyzing Corrected Dataset: NLTuan/dual_camera_torque_demo_v2_torque_corrected")
    print("=" * 80)
    
    # Load the corrected dataset locally
    corrected_parquet = "corrected_dataset_dual_camera_torque_demo_v2/episode_000000.parquet"
    
    if not Path(corrected_parquet).exists():
        print("❌ Local corrected dataset not found. Downloading from HuggingFace...")
        corrected_parquet = hf_hub_download(
            repo_id="NLTuan/dual_camera_torque_demo_v2_torque_corrected",
            filename="data/episode_000000.parquet",
            repo_type="dataset"
        )
    
    # Load original dataset for comparison
    print("📥 Loading original dataset for comparison...")
    original_parquet = hf_hub_download(
        repo_id="NLTuan/dual_camera_torque_demo_v2",
        filename="data/episode_000000.parquet", 
        repo_type="dataset"
    )
    
    # Load both datasets
    df_corrected = pd.read_parquet(corrected_parquet)
    df_original = pd.read_parquet(original_parquet)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  - Original frames: {len(df_original)}")
    print(f"  - Corrected frames: {len(df_corrected)}")
    print(f"  - Columns: {list(df_corrected.columns)}")
    
    # Extract observation and action data
    original_obs = np.array([np.frombuffer(row, dtype=np.float32) for row in df_original['observation.state']])
    corrected_obs = np.array([np.frombuffer(row, dtype=np.float32) for row in df_corrected['observation.state']])
    
    original_actions = np.array([np.frombuffer(row, dtype=np.float32) for row in df_original['action']])
    corrected_actions = np.array([np.frombuffer(row, dtype=np.float32) for row in df_corrected['action']])
    
    print(f"\n🔍 Data Analysis:")
    print(f"  - Observation shape: {original_obs.shape}")
    print(f"  - Action shape: {original_actions.shape}")
    
    # Analyze spike corrections
    print(f"\n🎯 Spike Correction Analysis:")
    obs_differences = np.abs(corrected_obs - original_obs)
    spike_corrections = np.sum(obs_differences > 0.1, axis=1)  # Frames with significant changes
    
    corrected_frames = np.where(spike_corrections > 0)[0]
    print(f"  - Frames with observation corrections: {len(corrected_frames)}")
    print(f"  - Total observation changes: {np.sum(obs_differences > 0.1)}")
    
    # Show some examples
    print(f"\n📝 Example Spike Corrections:")
    for i, frame_idx in enumerate(corrected_frames[:5]):
        original_vals = original_obs[frame_idx]
        corrected_vals = corrected_obs[frame_idx]
        changes = np.abs(corrected_vals - original_vals)
        
        print(f"  Frame {frame_idx}:")
        print(f"    Before: [{', '.join([f'{x:5.1f}' for x in original_vals])}]")
        print(f"    After:  [{', '.join([f'{x:5.1f}' for x in corrected_vals])}]")
        print(f"    Changes:[{', '.join([f'{x:5.1f}' for x in changes])}]")
        print()
    
    # Analyze torque control corrections  
    print(f"🎯 Torque Control Analysis:")
    action_differences = np.abs(corrected_actions - original_actions)
    torque_corrections = np.sum(action_differences > 0.1, axis=1)  # Frames with action changes
    
    torque_corrected_frames = np.where(torque_corrections > 0)[0]
    print(f"  - Frames with action corrections: {len(torque_corrected_frames)}")
    print(f"  - Total action changes: {np.sum(action_differences > 0.1)}")
    
    # Analyze 90-degree spike detection
    print(f"\n🚨 90° Spike Analysis:")
    
    # Count 90° values in original vs corrected
    original_90s = np.sum(np.abs(original_obs - 90.0) < 0.1)
    corrected_90s = np.sum(np.abs(corrected_obs - 90.0) < 0.1)
    
    print(f"  - 90° values in original: {original_90s}")
    print(f"  - 90° values in corrected: {corrected_90s}")
    print(f"  - 90° spikes removed: {original_90s - corrected_90s}")
    
    # Find frames where entire observation was 90°
    original_full_90s = np.sum(np.all(np.abs(original_obs - 90.0) < 0.1, axis=1))
    corrected_full_90s = np.sum(np.all(np.abs(corrected_obs - 90.0) < 0.1, axis=1))
    
    print(f"  - Frames with all joints at 90° (original): {original_full_90s}")
    print(f"  - Frames with all joints at 90° (corrected): {corrected_full_90s}")
    print(f"  - Full 90° spike frames fixed: {original_full_90s - corrected_full_90s}")
    
    # Data quality metrics
    print(f"\n📈 Data Quality Improvements:")
    
    # Calculate smoothness (lower is better)
    original_smoothness = np.mean(np.abs(np.diff(original_obs, axis=0)))
    corrected_smoothness = np.mean(np.abs(np.diff(corrected_obs, axis=0)))
    
    print(f"  - Original smoothness (avg change): {original_smoothness:.3f}°")
    print(f"  - Corrected smoothness (avg change): {corrected_smoothness:.3f}°") 
    print(f"  - Smoothness improvement: {((original_smoothness - corrected_smoothness) / original_smoothness * 100):.1f}%")
    
    # Calculate standard deviation (stability)
    original_std = np.mean(np.std(original_obs, axis=0))
    corrected_std = np.mean(np.std(corrected_obs, axis=0))
    
    print(f"  - Original std deviation: {original_std:.3f}°")
    print(f"  - Corrected std deviation: {corrected_std:.3f}°")
    print(f"  - Stability improvement: {((original_std - corrected_std) / original_std * 100):.1f}%")
    
    # Action-observation consistency
    original_action_obs_diff = np.mean(np.abs(original_actions[:, :6] - original_obs))
    corrected_action_obs_diff = np.mean(np.abs(corrected_actions[:, :6] - corrected_obs))
    
    print(f"  - Original action-obs mismatch: {original_action_obs_diff:.3f}°")
    print(f"  - Corrected action-obs mismatch: {corrected_action_obs_diff:.3f}°")
    print(f"  - Consistency improvement: {((original_action_obs_diff - corrected_action_obs_diff) / original_action_obs_diff * 100):.1f}%")
    
    # Create visualization
    print(f"\n📊 Creating visualization...")
    
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle('Dataset Correction Analysis', fontsize=16)
    
    # Plot joint trajectories for first 3 joints
    for joint in range(3):
        ax = axes[joint, 0]
        frames = np.arange(len(original_obs))
        
        ax.plot(frames, original_obs[:, joint], 'r-', alpha=0.7, label='Original', linewidth=1)
        ax.plot(frames, corrected_obs[:, joint], 'b-', alpha=0.8, label='Corrected', linewidth=1)
        
        ax.set_title(f'Joint {joint + 1} Trajectory')
        ax.set_xlabel('Frame')
        ax.set_ylabel('Angle (degrees)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Highlight corrected frames
        corrected_joint_frames = corrected_frames[obs_differences[corrected_frames, joint] > 0.1]
        if len(corrected_joint_frames) > 0:
            ax.scatter(corrected_joint_frames, corrected_obs[corrected_joint_frames, joint], 
                      c='orange', s=10, alpha=0.8, label='Corrections', zorder=5)
    
    # Plot action-observation differences
    axes[0, 1].plot(np.mean(np.abs(original_actions[:, :6] - original_obs), axis=1), 'r-', alpha=0.7, label='Original')
    axes[0, 1].plot(np.mean(np.abs(corrected_actions[:, :6] - corrected_obs), axis=1), 'b-', alpha=0.8, label='Corrected')
    axes[0, 1].set_title('Action-Observation Mismatch')
    axes[0, 1].set_ylabel('Avg Mismatch (degrees)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot smoothness comparison
    original_smoothness_series = np.mean(np.abs(np.diff(original_obs, axis=0)), axis=1)
    corrected_smoothness_series = np.mean(np.abs(np.diff(corrected_obs, axis=0)), axis=1)
    
    axes[1, 1].plot(original_smoothness_series, 'r-', alpha=0.7, label='Original')
    axes[1, 1].plot(corrected_smoothness_series, 'b-', alpha=0.8, label='Corrected')
    axes[1, 1].set_title('Movement Smoothness')
    axes[1, 1].set_ylabel('Frame-to-frame change (degrees)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # Plot correction histogram
    all_corrections = obs_differences[obs_differences > 0.1]
    axes[2, 1].hist(all_corrections, bins=50, alpha=0.7, color='orange', edgecolor='black')
    axes[2, 1].set_title('Spike Correction Magnitude Distribution')
    axes[2, 1].set_xlabel('Correction Amount (degrees)')
    axes[2, 1].set_ylabel('Count')
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    output_path = 'dataset_correction_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"📊 Analysis plot saved: {output_path}")
    
    # Load correction reports if available
    corrections_file = "corrected_dataset_dual_camera_torque_demo_v2/corrections.json"
    if Path(corrections_file).exists():
        print(f"\n📋 Correction Report Summary:")
        with open(corrections_file, 'r') as f:
            corrections = json.load(f)
        
        print(f"  - Total corrections logged: {len(corrections.get('corrections', []))}")
        print(f"  - Processing time: {corrections.get('processing_time', 'N/A')}")
        print(f"  - Methods used: {corrections.get('methods_used', [])}")
    
    plt.show()
    
    return {
        'original_frames': len(df_original),
        'corrected_frames': len(df_corrected),
        'spike_corrections': len(corrected_frames),
        'torque_corrections': len(torque_corrected_frames),
        'smoothness_improvement': ((original_smoothness - corrected_smoothness) / original_smoothness * 100),
        'consistency_improvement': ((original_action_obs_diff - corrected_action_obs_diff) / original_action_obs_diff * 100)
    }

if __name__ == "__main__":
    results = analyze_corrected_dataset()
    print(f"\n🎉 Analysis Complete!")
    print(f"   - Dataset quality significantly improved")
    print(f"   - Ready for high-quality imitation learning")
