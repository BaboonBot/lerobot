#!/usr/bin/env python3
"""
Analyze the corrected dataset to find remaining spikes that weren't detected
"""
import pandas as pd
import numpy as np
from huggingface_hub import hf_hub_download
import matplotlib.pyplot as plt

def analyze_remaining_spikes(repo_id):
    print(f"🔍 Analyzing remaining spikes in: {repo_id}")
    
    # Use the local corrected parquet file
    parquet_path = "corrected_dataset_dual_camera_torque_demo_v2/episode_000000.parquet"
    
    # Load the data
    df = pd.read_parquet(parquet_path)
    observations = np.array([obs for obs in df['observation.state']])
    actions = np.array([act for act in df['action']])
    
    print(f"📊 Dataset info:")
    print(f"  - Total frames: {len(observations)}")
    print(f"  - Observation shape: {observations.shape}")
    print(f"  - Action shape: {actions.shape}")
    
    # Enhanced spike detection methods
    spikes_found = set()
    
    # Method 1: Detect sudden jumps (enhanced sensitivity)
    print("\n🎯 Method 1: Detecting sudden jumps...")
    for i in range(1, len(observations)):
        prev_obs = observations[i-1]
        curr_obs = observations[i]
        
        # Calculate changes
        changes = np.abs(curr_obs - prev_obs)
        
        # Multiple criteria for sudden jumps
        if np.any(changes > 0.8):  # Reduced from 1.5°
            spikes_found.add(i)
            print(f"  Frame {i}: Sudden jump detected, max change: {np.max(changes):.1f}°")
    
    # Method 2: Detect 90° resets (any joint)
    print("\n🎯 Method 2: Detecting 90° resets...")
    for i in range(len(observations)):
        obs = observations[i]
        
        # Count joints at exactly 90°
        joints_at_90 = np.sum(np.abs(obs - 90.0) < 0.1)
        
        # If 3+ joints are at 90°, it's likely a reset
        if joints_at_90 >= 3:
            spikes_found.add(i)
            print(f"  Frame {i}: {joints_at_90}/6 joints at 90°: {obs}")
    
    # Method 3: Detect outliers using rolling statistics
    print("\n🎯 Method 3: Detecting statistical outliers...")
    window_size = 10
    for joint in range(6):
        joint_values = observations[:, joint]
        
        for i in range(window_size, len(joint_values) - window_size):
            # Get neighborhood (excluding current point)
            neighborhood = np.concatenate([
                joint_values[i-window_size:i],
                joint_values[i+1:i+1+window_size]
            ])
            
            current_val = joint_values[i]
            mean_val = np.mean(neighborhood)
            std_val = np.std(neighborhood)
            
            # Z-score based detection (more sensitive)
            if std_val > 0:
                z_score = abs(current_val - mean_val) / std_val
                if z_score > 1.5:  # Reduced threshold
                    spikes_found.add(i)
                    print(f"  Frame {i}: Joint {joint+1} outlier, z-score: {z_score:.1f}, value: {current_val:.1f}°")
    
    # Method 4: Detect impossible velocities
    print("\n🎯 Method 4: Detecting impossible velocities...")
    for i in range(2, len(observations)):
        prev_obs = observations[i-2]
        curr_obs = observations[i-1]
        next_obs = observations[i]
        
        # Calculate velocities
        vel1 = np.abs(curr_obs - prev_obs)
        vel2 = np.abs(next_obs - curr_obs)
        
        # If velocity changes dramatically, it's likely a spike
        vel_change = np.abs(vel2 - vel1)
        if np.any(vel_change > 1.0):  # Velocity change threshold
            spikes_found.add(i-1)
            print(f"  Frame {i-1}: Impossible velocity change, max: {np.max(vel_change):.1f}°")
    
    # Method 5: Detect action-observation mismatches
    print("\n🎯 Method 5: Detecting action-observation mismatches...")
    for i in range(len(observations)):
        obs = observations[i]
        act = actions[i][:6]  # First 6 values are joint actions
        
        # Calculate mismatch
        mismatch = np.abs(obs - act)
        
        # If mismatch is too large, observation might be spiked
        if np.any(mismatch > 2.0):  # Reduced threshold
            spikes_found.add(i)
            print(f"  Frame {i}: Large action-obs mismatch, max: {np.max(mismatch):.1f}°")
    
    # Method 6: Detect consecutive identical values (sensor stuck)
    print("\n🎯 Method 6: Detecting sensor stuck patterns...")
    for joint in range(6):
        joint_values = observations[:, joint]
        
        consecutive_count = 1
        for i in range(1, len(joint_values)):
            if abs(joint_values[i] - joint_values[i-1]) < 0.01:  # Identical values
                consecutive_count += 1
            else:
                # If we had a long run of identical values, mark them as spikes
                if consecutive_count >= 5:
                    for j in range(max(0, i - consecutive_count), i):
                        spikes_found.add(j)
                        print(f"  Frame {j}: Joint {joint+1} stuck at {joint_values[j]:.1f}° ({consecutive_count} frames)")
                consecutive_count = 1
    
    print(f"\n📈 Summary:")
    print(f"  - Total frames analyzed: {len(observations)}")
    print(f"  - Remaining spikes detected: {len(spikes_found)}")
    print(f"  - Spike density: {100 * len(spikes_found) / len(observations):.2f}%")
    
    # Show some examples
    spike_list = sorted(list(spikes_found))
    if spike_list:
        print(f"\n🎯 Sample remaining spikes:")
        for i, frame_idx in enumerate(spike_list[:10]):  # Show first 10
            obs = observations[frame_idx]
            print(f"  Frame {frame_idx}: {obs}")
        
        if len(spike_list) > 10:
            print(f"  ... and {len(spike_list) - 10} more")
    
    return spike_list, observations, actions

if __name__ == "__main__":
    repo_id = "NLTuan/dual_camera_torque_demo_v2_torque_corrected"
    spike_list, observations, actions = analyze_remaining_spikes(repo_id)
