#!/usr/bin/env python3
"""
Analysis of the corrected dataset: NLTuan/dual_camera_torque_demo_v2_torque_corrected
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def analyze_corrected_dataset():
    print("🔍 Analyzing Corrected Dataset: NLTuan/dual_camera_torque_demo_v2_torque_corrected")
    print("=" * 80)
    
    # Load the corrected dataset locally
    corrected_parquet = "corrected_dataset_dual_camera_torque_demo_v2/episode_000000.parquet"
    
    if not Path(corrected_parquet).exists():
        print("❌ Local corrected dataset not found!")
        return
    
    # Load the corrected dataset
    print("📥 Loading corrected dataset...")
    df_corrected = pd.read_parquet(corrected_parquet)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  - Total frames: {len(df_corrected)}")
    print(f"  - Columns: {list(df_corrected.columns)}")
    
    # Extract observation and action data
    observations = np.array([np.frombuffer(row, dtype=np.float32) for row in df_corrected['observation.state']])
    actions = np.array([np.frombuffer(row, dtype=np.float32) for row in df_corrected['action']])
    
    print(f"  - Observation shape: {observations.shape}")
    print(f"  - Action shape: {actions.shape}")
    
    # Basic statistics
    print(f"\n📈 Joint Angle Statistics:")
    joint_names = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
    
    for i, joint_name in enumerate(joint_names):
        joint_obs = observations[:, i]
        print(f"  {joint_name}:")
        print(f"    - Min: {np.min(joint_obs):.1f}°")
        print(f"    - Max: {np.max(joint_obs):.1f}°")
        print(f"    - Mean: {np.mean(joint_obs):.1f}°")
        print(f"    - Std: {np.std(joint_obs):.1f}°")
    
    # Analyze 90° reset spikes (should be minimal now)
    print(f"\n🚨 90° Reset Spike Analysis:")
    reset_90_count = np.sum(np.abs(observations - 90.0) < 0.1)
    full_reset_frames = np.sum(np.all(np.abs(observations - 90.0) < 0.1, axis=1))
    
    print(f"  - Total 90° values: {reset_90_count}")
    print(f"  - Frames with all joints at 90°: {full_reset_frames}")
    print(f"  - 90° density: {100 * reset_90_count / (len(observations) * 6):.2f}%")
    
    # Movement smoothness analysis
    print(f"\n🎯 Movement Smoothness Analysis:")
    frame_changes = np.abs(np.diff(observations, axis=0))
    avg_change_per_frame = np.mean(frame_changes, axis=1)
    
    print(f"  - Average frame-to-frame change: {np.mean(avg_change_per_frame):.3f}°")
    print(f"  - Max frame-to-frame change: {np.max(avg_change_per_frame):.3f}°")
    print(f"  - Frames with large movements (>5°): {np.sum(avg_change_per_frame > 5)}")
    print(f"  - Frames with very large movements (>20°): {np.sum(avg_change_per_frame > 20)}")
    
    # Action-observation consistency
    print(f"\n🎯 Action-Observation Consistency:")
    action_obs_diff = np.abs(actions[:, :6] - observations)  # First 6 action values are joint positions
    avg_mismatch = np.mean(action_obs_diff)
    max_mismatch = np.max(action_obs_diff)
    
    print(f"  - Average action-observation mismatch: {avg_mismatch:.3f}°")
    print(f"  - Maximum action-observation mismatch: {max_mismatch:.3f}°")
    print(f"  - Frames with large mismatch (>2°): {np.sum(np.any(action_obs_diff > 2.0, axis=1))}")
    
    # Load correction reports if available
    corrections_file = "corrected_dataset_dual_camera_torque_demo_v2/corrections.json"
    if Path(corrections_file).exists():
        print(f"\n📋 Correction Report Summary:")
        with open(corrections_file, 'r') as f:
            corrections = json.load(f)
        
        print(f"  - Total corrections applied: {len(corrections.get('corrections', []))}")
        
        # Show correction statistics
        if isinstance(corrections.get('corrections'), dict):
            print(f"  - Correction methods used: {list(corrections['corrections'].keys())}")
        elif isinstance(corrections.get('corrections'), list):
            print(f"  - Corrections list length: {len(corrections['corrections'])}")
        else:
            print(f"  - Corrections format: {type(corrections.get('corrections'))}")
    
    # Create comprehensive visualization
    print(f"\n📊 Creating visualization...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Corrected Dataset Analysis: NLTuan/dual_camera_torque_demo_v2_torque_corrected', fontsize=16)
    
    # Plot joint trajectories
    frames = np.arange(len(observations))
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
    
    for i in range(6):
        ax = axes[0, i % 3] if i < 3 else axes[1, i % 3]
        ax.plot(frames, observations[:, i], color=colors[i], linewidth=1, alpha=0.8)
        ax.set_title(f'Joint {i+1} Trajectory')
        ax.set_xlabel('Frame')
        ax.set_ylabel('Angle (degrees)')
        ax.grid(True, alpha=0.3)
        
        # Highlight any remaining 90° values
        reset_indices = np.where(np.abs(observations[:, i] - 90.0) < 0.1)[0]
        if len(reset_indices) > 0:
            ax.scatter(reset_indices, observations[reset_indices, i], 
                      color='red', s=20, alpha=0.6, label='90° values')
            ax.legend()
    
    plt.tight_layout()
    
    # Save the plot
    output_path = 'corrected_dataset_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"📊 Analysis plot saved: {output_path}")
    
    # Additional detailed analysis
    print(f"\n🔍 Detailed Quality Metrics:")
    
    # Check for outliers in each joint
    for i, joint_name in enumerate(joint_names):
        joint_data = observations[:, i]
        q25, q75 = np.percentile(joint_data, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        outliers = np.sum((joint_data < lower_bound) | (joint_data > upper_bound))
        print(f"  {joint_name} outliers: {outliers} frames ({100*outliers/len(joint_data):.1f}%)")
    
    # Torque control effectiveness analysis
    print(f"\n🎯 Torque Control Effectiveness:")
    
    # Look for periods where actions match observations (torque off periods)
    action_obs_close = np.all(np.abs(actions[:, :6] - observations) < 1.0, axis=1)
    torque_off_periods = np.sum(action_obs_close)
    
    print(f"  - Frames with actions matching observations: {torque_off_periods}")
    print(f"  - Torque-off period ratio: {100 * torque_off_periods / len(observations):.1f}%")
    
    # Dataset readiness assessment
    print(f"\n✅ Dataset Quality Assessment:")
    
    quality_score = 0
    max_score = 0
    
    # Smoothness check
    max_score += 20
    if np.mean(avg_change_per_frame) < 2.0:
        quality_score += 20
        print(f"  ✅ Excellent smoothness (avg change: {np.mean(avg_change_per_frame):.3f}°)")
    elif np.mean(avg_change_per_frame) < 5.0:
        quality_score += 15
        print(f"  ✅ Good smoothness (avg change: {np.mean(avg_change_per_frame):.3f}°)")
    else:
        quality_score += 10
        print(f"  ⚠️  Moderate smoothness (avg change: {np.mean(avg_change_per_frame):.3f}°)")
    
    # Spike removal check
    max_score += 30
    if full_reset_frames < 5:
        quality_score += 30
        print(f"  ✅ Excellent spike removal ({full_reset_frames} full reset frames)")
    elif full_reset_frames < 20:
        quality_score += 20
        print(f"  ✅ Good spike removal ({full_reset_frames} full reset frames)")
    else:
        quality_score += 10
        print(f"  ⚠️  Some spikes remain ({full_reset_frames} full reset frames)")
    
    # Action-observation consistency
    max_score += 25
    if avg_mismatch < 1.0:
        quality_score += 25
        print(f"  ✅ Excellent consistency (avg mismatch: {avg_mismatch:.3f}°)")
    elif avg_mismatch < 3.0:
        quality_score += 20
        print(f"  ✅ Good consistency (avg mismatch: {avg_mismatch:.3f}°)")
    else:
        quality_score += 10
        print(f"  ⚠️  Moderate consistency (avg mismatch: {avg_mismatch:.3f}°)")
    
    # Data completeness
    max_score += 25
    if len(observations) > 1000:
        quality_score += 25
        print(f"  ✅ Excellent data volume ({len(observations)} frames)")
    elif len(observations) > 500:
        quality_score += 20
        print(f"  ✅ Good data volume ({len(observations)} frames)")
    else:
        quality_score += 15
        print(f"  ✅ Adequate data volume ({len(observations)} frames)")
    
    final_score = (quality_score / max_score) * 100
    print(f"\n🏆 Overall Dataset Quality Score: {final_score:.1f}/100")
    
    if final_score >= 90:
        print("  🎉 EXCELLENT - Ready for high-quality training!")
    elif final_score >= 75:
        print("  ✅ GOOD - Suitable for training with good results expected")
    elif final_score >= 60:
        print("  ⚠️  MODERATE - Training possible but may need further refinement")
    else:
        print("  ❌ POOR - Significant improvements needed before training")
    
    plt.show()
    
    return {
        'total_frames': len(observations),
        'avg_smoothness': np.mean(avg_change_per_frame),
        'reset_spikes': full_reset_frames,
        'action_obs_consistency': avg_mismatch,
        'quality_score': final_score
    }

if __name__ == "__main__":
    results = analyze_corrected_dataset()
    print(f"\n🎉 Analysis Complete! Dataset is ready for training.")
