#!/usr/bin/env python3
"""
Simple torque post-processor that creates a corrections file.
This avoids memory issues by just saving the corrections metadata.
"""

import argparse
import numpy as np
import json
from pathlib import Path
from lerobot.datasets.lerobot_dataset import LeRobotDataset

def create_corrections_file(repo_id: str):
    """Create a corrections file that documents all the changes needed."""
    print(f"🔄 Loading dataset: {repo_id}")
    
    dataset = LeRobotDataset(repo_id)
    print(f"📊 Dataset: {len(dataset)} frames")
    
    corrections = {}
    modifications_made = 0
    
    print("🔍 Detecting manual control frames...")
    
    for i in range(1, len(dataset)):
        curr_sample = dataset[i-1]
        next_sample = dataset[i]
        
        curr_action = curr_sample['action'].numpy()[:6]  # First 6 joints
        curr_obs = curr_sample['observation.state'].numpy()
        next_obs = next_sample['observation.state'].numpy()
        
        # Detect manual movement
        action_to_obs_diff = np.abs(curr_action - curr_obs).max()
        obs_change = np.abs(next_obs - curr_obs).max()
        
        if action_to_obs_diff > 3.0 and obs_change > 1.0:
            # Store the correction
            corrections[str(i-1)] = {
                'original_action': curr_action.tolist(),
                'corrected_action': next_obs.tolist(),
                'frame_type': 'manual_control'
            }
            modifications_made += 1
    
    # Save corrections file
    output_file = f"torque_corrections_{repo_id.split('/')[-1]}.json"
    
    correction_data = {
        'dataset_repo_id': repo_id,
        'total_frames': len(dataset),
        'corrections_count': modifications_made,
        'corrections': corrections,
        'description': 'Torque control corrections - actions updated to match manual robot movements'
    }
    
    with open(output_file, 'w') as f:
        json.dump(correction_data, f, indent=2)
    
    print(f"✅ Corrections saved to: {output_file}")
    print(f"📊 {modifications_made} corrections documented")
    
    # Create a summary report
    report_file = f"torque_report_{repo_id.split('/')[-1]}.txt"
    with open(report_file, 'w') as f:
        f.write(f"Torque Control Post-Processing Report\n")
        f.write(f"=====================================\n\n")
        f.write(f"Original dataset: {repo_id}\n")
        f.write(f"Total frames: {len(dataset)}\n")
        f.write(f"Frames needing correction: {modifications_made}\n")
        f.write(f"Correction rate: {modifications_made/len(dataset)*100:.1f}%\n\n")
        f.write(f"Manual movement detected in frames:\n")
        
        frame_numbers = sorted([int(k) for k in corrections.keys()])
        for i, frame_num in enumerate(frame_numbers[:10]):  # Show first 10
            correction = corrections[str(frame_num)]
            f.write(f"  Frame {frame_num}: {correction['corrected_action'][:3]}\n")
        
        if len(frame_numbers) > 10:
            f.write(f"  ... and {len(frame_numbers) - 10} more frames\n")
    
    print(f"📄 Report saved to: {report_file}")
    return output_file, report_file

def main():
    parser = argparse.ArgumentParser(description="Create torque control corrections file")
    parser.add_argument("--repo_id", type=str, required=True, help="HuggingFace dataset repository ID")
    
    args = parser.parse_args()
    
    corrections_file, report_file = create_corrections_file(args.repo_id)
    
    print(f"\n🎉 Success! Files created:")
    print(f"   📁 Corrections: {corrections_file}")
    print(f"   📄 Report: {report_file}")
    print(f"\n💡 These files document which frames need action corrections for proper torque behavior.")

if __name__ == "__main__":
    main()
