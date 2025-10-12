#!/usr/bin/env python3
"""
Clean torque post-processing for LeRobot datasets.

Two-phase approach:
1. Remove observation spikes using multiple detection methods
2. Add torque-aware actions where torque was disabled

Usage:
    python torque_postprocess_clean.py --repo_id="NLTuan/dual_camera_torque_demo_original" --push_to_hub
"""

import argparse
import numpy as np
import pandas as pd
import json
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

def detect_observation_spikes(observations, threshold_90deg=2.0, threshold_sudden=25.0, threshold_outlier=15.0):
    """
    Phase 1: Detect observation spikes using multiple methods.
    
    Args:
        observations: numpy array of shape (n_frames, n_joints)
        threshold_90deg: degrees tolerance for 90-degree reset detection
        threshold_sudden: degrees threshold for sudden movement detection
        threshold_outlier: degrees threshold for outlier detection
    
    Returns:
        list of dicts: [{'frame': idx, 'method': str, 'reason': str, 'values': array}]
    """
    n_frames, n_joints = observations.shape
    spikes = []
    
    print(f"🔍 Phase 1: Detecting observation spikes in {n_frames} frames...")
    
    for i in range(1, n_frames - 1):
        curr = observations[i]
        prev = observations[i-1]
        next_frame = observations[i+1]
        
        # Method 1: 90-degree reset spikes (sensor error)
        joints_near_90 = np.sum(np.abs(curr - 90.0) < threshold_90deg)
        if joints_near_90 >= 3:  # 3+ joints suddenly at ~90°
            max_change = np.max(np.abs(curr - prev))
            if max_change > 10.0:  # Significant change from previous
                spikes.append({
                    'frame': i,
                    'method': '90_degree_reset',
                    'reason': f'{joints_near_90}/{n_joints} joints at 90°, max change: {max_change:.1f}°',
                    'values': curr.copy()
                })
                continue
        
        # Method 2: Sudden large movements
        max_change_prev = np.max(np.abs(curr - prev))
        max_change_next = np.max(np.abs(curr - next_frame))
        if max_change_prev > threshold_sudden and max_change_next > threshold_sudden:
            # Check if neighbors are similar (spike in middle)
            neighbor_diff = np.max(np.abs(prev - next_frame))
            if neighbor_diff < threshold_sudden / 2:
                spikes.append({
                    'frame': i,
                    'method': 'sudden_movement',
                    'reason': f'Sudden spike: {max_change_prev:.1f}° from prev, {max_change_next:.1f}° to next',
                    'values': curr.copy()
                })
                continue
        
        # Method 3: Statistical outlier detection
        if i >= 2 and i < n_frames - 2:
            window = [observations[i-2], observations[i-1], observations[i+1], observations[i+2]]
            window_mean = np.mean(window, axis=0)
            outlier_distance = np.max(np.abs(curr - window_mean))
            if outlier_distance > threshold_outlier:
                spikes.append({
                    'frame': i,
                    'method': 'statistical_outlier',
                    'reason': f'Outlier: {outlier_distance:.1f}° from local mean',
                    'values': curr.copy()
                })
    
    print(f"  ✅ Detected {len(spikes)} observation spikes")
    return spikes

def interpolate_observation(observations, spike_frame, window_size=3):
    """
    Interpolate a spike observation using neighboring clean frames.
    
    Args:
        observations: numpy array of shape (n_frames, n_joints)
        spike_frame: frame index to interpolate
        window_size: number of frames to look before/after
    
    Returns:
        numpy array: interpolated observation values
    """
    n_frames = len(observations)
    
    # Find nearest clean frames
    before_idx = max(0, spike_frame - window_size)
    after_idx = min(n_frames - 1, spike_frame + window_size)
    
    # Linear interpolation between before and after
    if before_idx != spike_frame and after_idx != spike_frame:
        before_obs = observations[before_idx]
        after_obs = observations[after_idx]
        # Simple midpoint interpolation
        return (before_obs + after_obs) / 2.0
    elif before_idx != spike_frame:
        return observations[before_idx].copy()
    elif after_idx != spike_frame:
        return observations[after_idx].copy()
    else:
        return observations[spike_frame].copy()  # Fallback

def remove_observation_spikes(df, spikes):
    """
    Phase 1: Remove detected spikes from observations using interpolation.
    
    Args:
        df: pandas DataFrame with dataset
        spikes: list of spike detection results
    
    Returns:
        pandas DataFrame: dataset with cleaned observations
    """
    if not spikes:
        print("  ℹ️  No spikes to remove")
        return df
    
    print(f"🔧 Removing {len(spikes)} observation spikes...")
    
    # Work on a copy
    df_clean = df.copy()
    
    # Convert observations to numpy for easier manipulation
    observations = np.array([np.frombuffer(row, dtype=np.float32) for row in df_clean['observation.state']])
    
    # Remove spikes by interpolation
    for spike in spikes:
        frame_idx = spike['frame']
        interpolated = interpolate_observation(observations, frame_idx)
        observations[frame_idx] = interpolated
        print(f"  📍 Frame {frame_idx}: {spike['method']} - {spike['reason']}")
    
    # Update dataframe with cleaned observations
    for i, obs in enumerate(observations):
        df_clean.loc[i, 'observation.state'] = obs.tobytes()
    
    print(f"  ✅ Observation spikes removed successfully")
    return df_clean

def detect_torque_control_frames(actions, observations, movement_threshold=1.0):
    """
    Phase 2: Detect frames where torque control should be applied.
    
    Args:
        actions: numpy array of shape (n_frames, action_dim)
        observations: numpy array of shape (n_frames, n_joints)
        movement_threshold: minimum degrees of movement to consider manual control
    
    Returns:
        list of dicts: [{'frame': idx, 'reason': str, 'movement': float}]
    """
    n_frames = len(actions)
    torque_frames = []
    
    print(f"🎯 Phase 2: Detecting torque control periods in {n_frames} frames...")
    
    for i in range(n_frames - 1):
        curr_action = actions[i][:6]    # First 6 are joint positions
        curr_obs = observations[i]      # Current robot position
        next_obs = observations[i+1]    # Next robot position (where it actually moved)
        
        # Calculate action vs observation mismatch
        action_obs_diff = np.max(np.abs(curr_action - curr_obs))
        
        # Calculate actual robot movement
        movement = np.max(np.abs(next_obs - curr_obs))
        
        # Detect manual control: significant movement but action doesn't match current position
        if movement > movement_threshold and action_obs_diff > movement_threshold:
            torque_frames.append({
                'frame': i,
                'reason': f'Manual control: {movement:.1f}° movement, {action_obs_diff:.1f}° action mismatch',
                'movement': movement,
                'action_before': curr_action.copy(),
                'obs_before': curr_obs.copy(),
                'obs_after': next_obs.copy()
            })
    
    print(f"  ✅ Detected {len(torque_frames)} torque control periods")
    return torque_frames

def apply_torque_corrections(df, torque_frames):
    """
    Phase 2: Apply torque control corrections by updating actions.
    
    Args:
        df: pandas DataFrame with dataset
        torque_frames: list of torque control detection results
    
    Returns:
        tuple: (corrected_dataframe, corrections_dict)
    """
    if not torque_frames:
        print("  ℹ️  No torque control corrections needed")
        return df, {}
    
    print(f"🔧 Applying {len(torque_frames)} torque control corrections...")
    
    df_corrected = df.copy()
    corrections = {}
    
    for torque_frame in torque_frames:
        frame_idx = torque_frame['frame']
        
        # Get the next frame's observation (where robot actually moved)
        if frame_idx + 1 < len(df):
            next_obs = np.frombuffer(df.iloc[frame_idx + 1]['observation.state'], dtype=np.float32)
            
            # Current action
            curr_action = np.frombuffer(df.iloc[frame_idx]['action'], dtype=np.float32)
            
            # Create new action: update joint positions (first 6 elements) to match next observation
            new_action = curr_action.copy()
            new_action[:6] = next_obs[:6]  # Copy joint positions from next observation
            
            # Update the action in dataframe
            df_corrected.at[frame_idx, 'action'] = new_action.tobytes()
            
            # Save correction info
            corrections[frame_idx] = {
                'reason': torque_frame['reason'],
                'movement': float(torque_frame['movement']),
                'original_action': torque_frame['action_before'].tolist(),
                'corrected_action': new_action[:6].tolist(),
                'target_observation': next_obs[:6].tolist()
            }
            
            print(f"  📍 Frame {frame_idx}: {torque_frame['reason']}")
    
    print(f"  ✅ Applied {len(corrections)} action corrections")
    return df_corrected, corrections

def create_dataset_metadata(df, corrections, original_repo_id, spikes, torque_frames):
    """
    Create LeRobot-compatible metadata for the corrected dataset.
    """
    return {
        'info': {
            "codebase_version": "0.3.4",
            "dataset_type": "LeRobotDataset", 
            "total_episodes": 1,
            "total_frames": len(df),
            "total_tasks": 1,
            "total_videos": 2,
            "original_dataset": original_repo_id,
            "corrections_applied": {
                "observation_spikes_removed": len(spikes),
                "torque_corrections": len(corrections)
            }
        },
        'stats': {
            "observation.state": {"max": [180.0] * 6, "mean": [90.0] * 6, "min": [0.0] * 6, "std": [45.0] * 6},
            "action": {"max": [180.0] * 6, "mean": [90.0] * 6, "min": [0.0] * 6, "std": [45.0] * 6}
        },
        'episodes': [{"episode_index": 0, "length": len(df), "timestamp": "2025-10-06T00:00:00"}]
    }

def create_dataset_card(original_repo_id, total_frames, corrections_count, spikes_count):
    """
    Create a comprehensive dataset card for the corrected dataset.
    """
    return f"""# Torque-Corrected LeRobot Dataset

This dataset is a post-processed version of `{original_repo_id}` with comprehensive corrections applied.

## Post-Processing Applied

### Phase 1: Observation Spike Removal
- **Spikes removed**: {spikes_count}
- **Detection methods**: 90-degree resets, sudden movements, statistical outliers
- **Correction method**: Linear interpolation from neighboring frames

### Phase 2: Torque Control Corrections  
- **Corrections applied**: {corrections_count}
- **Total frames**: {total_frames}
- **Correction rate**: {corrections_count/total_frames*100:.1f}%

## What was corrected

1. **Observation Spikes**: Removed sensor errors and reset artifacts that caused sudden jumps to 90° positions
2. **Torque Actions**: Updated actions to match subsequent robot positions during manual control periods when torque was disabled

This ensures the dataset accurately represents both the robot's sensor readings and the intended actions during demonstrations.

## Usage

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# Load the corrected dataset
dataset = LeRobotDataset("{original_repo_id}_torque_corrected")
```

## Quality Metrics
- Total episodes: 1
- Total frames: {total_frames}
- Observation spikes removed: {spikes_count}
- Action corrections: {corrections_count}
"""

def save_and_upload_dataset(df, corrections, original_repo_id, output_repo_id, spikes, torque_frames):
    """
    Save corrected dataset locally and upload to HuggingFace Hub.
    """
    print(f"💾 Saving and uploading corrected dataset...")
    
    # Create local dataset structure
    local_path = Path(f"./corrected_dataset_{original_repo_id.split('/')[-1]}")
    local_path.mkdir(exist_ok=True)
    data_path = local_path / "data" / "chunk-000"
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Save corrected parquet
    parquet_path = data_path / "episode_000000.parquet"
    df.to_parquet(parquet_path, index=False)
    
    # Create dataset metadata
    metadata = create_dataset_metadata(df, corrections, original_repo_id, spikes, torque_frames)
    
    # Save metadata files
    (local_path / "meta").mkdir(exist_ok=True)
    with open(local_path / "meta" / "info.json", "w") as f:
        json.dump(metadata['info'], f, indent=2)
    
    with open(local_path / "meta" / "stats.json", "w") as f:
        json.dump(metadata['stats'], f, indent=2)
    
    with open(local_path / "meta" / "episodes.json", "w") as f:
        json.dump(metadata['episodes'], f, indent=2)
    
    # Create dataset card
    dataset_card = create_dataset_card(original_repo_id, len(df), len(corrections), len(spikes))
    with open(local_path / "README.md", "w") as f:
        f.write(dataset_card)
    
    print(f"✅ Local dataset saved: {local_path}")
    
    # Upload to HuggingFace Hub
    try:
        api = HfApi()
        
        print(f"🚀 Uploading to {output_repo_id}...")
        
        # Upload all files
        api.upload_folder(
            folder_path=str(local_path),
            repo_id=output_repo_id,
            repo_type="dataset"
        )
        
        print(f"🎉 Successfully uploaded to: https://huggingface.co/datasets/{output_repo_id}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print(f"📁 Dataset saved locally at: {local_path}")

def postprocess_dataset(repo_id: str, output_suffix: str = "_torque_corrected", push_to_hub: bool = False):
    """
    Complete two-phase post-processing pipeline:
    1. Remove observation spikes
    2. Add torque-aware actions
    
    Args:
        repo_id: HuggingFace dataset repository ID
        output_suffix: suffix for output dataset name
        push_to_hub: whether to upload results to HuggingFace Hub
    """
    print(f"🚀 Starting two-phase post-processing for: {repo_id}")
    
    # Download parquet file from Hub
    parquet_path = hf_hub_download(repo_id=repo_id, filename="data/chunk-000/episode_000000.parquet", repo_type="dataset")
    print(f"📥 Downloaded parquet from {repo_id}")
    
    # Load dataset
    df = pd.read_parquet(parquet_path)
    print(f"📊 Loaded {len(df)} frames")
    
    # Extract observations and actions
    observations = np.array([np.frombuffer(row, dtype=np.float32) for row in df['observation.state']])
    actions = np.array([np.frombuffer(row, dtype=np.float32) for row in df['action']])
    
    print(f"  - Observation shape: {observations[0].shape}")
    print(f"  - Action shape: {actions[0].shape}")
    
    # PHASE 1: Remove observation spikes
    spikes = detect_observation_spikes(observations)
    df_clean = remove_observation_spikes(df, spikes)
    
    # Re-extract observations after spike removal
    observations_clean = np.array([np.frombuffer(row, dtype=np.float32) for row in df_clean['observation.state']])
    
    # PHASE 2: Add torque control corrections
    torque_frames = detect_torque_control_frames(actions, observations_clean)
    df_final, corrections = apply_torque_corrections(df_clean, torque_frames)
    
    # Save results and upload to Hub if requested
    if push_to_hub:
        output_repo_id = f"{repo_id}{output_suffix}"
        save_and_upload_dataset(df_final, corrections, repo_id, output_repo_id, spikes, torque_frames)
    else:
        # Just save locally
        local_output_path = Path(f"./corrected_dataset_{repo_id.split('/')[-1]}")
        local_output_path.mkdir(exist_ok=True)
        
        corrected_parquet_path = local_output_path / "episode_000000.parquet"
        df_final.to_parquet(corrected_parquet_path, index=False)
        
        print(f"💾 Saved corrected dataset locally: {corrected_parquet_path}")
    
    # Summary
    print(f"\n🎉 Post-processing complete!")
    print(f"  - Observation spikes removed: {len(spikes)}")
    print(f"  - Torque corrections applied: {len(corrections)}")
    print(f"  - Total frames processed: {len(df_final)}")

def main():
    """
    Main entry point for torque post-processing.
    """
    parser = argparse.ArgumentParser(description="Clean two-phase torque post-processing")
    parser.add_argument("--repo_id", type=str, required=True, 
                       help="HuggingFace dataset repository ID")
    parser.add_argument("--output_suffix", type=str, default="_torque_corrected",
                       help="Suffix for output dataset name")
    parser.add_argument("--push_to_hub", action="store_true",
                       help="Upload corrected dataset to HuggingFace Hub")
    
    args = parser.parse_args()
    
    # Run the complete two-phase post-processing
    postprocess_dataset(args.repo_id, args.output_suffix, args.push_to_hub)

if __name__ == "__main__":
    main()
