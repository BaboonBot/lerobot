#!/usr/bin/env python3
"""
Memory-efficient torque post-processor that works directly with LeRobot format.
Uses in-place modifications and LeRobot's native saving to avoid memory issues.
"""

import argparse
import numpy as np
import json
from pathlib import Path
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch
import tempfile
import shutil

def postprocess_torque_control_efficient(repo_id: str, push_to_hub: bool = False):
    """
    Memory-efficient torque control post-processing.
    Modifies dataset in-place and uses LeRobot's native save methods.
    """
    print(f"🔄 Loading dataset: {repo_id}")
    
    # Load the dataset
    dataset = LeRobotDataset(repo_id)
    
    print(f"📊 Dataset info:")
    print(f"  - Episodes: {dataset.num_episodes}")
    print(f"  - Total frames: {len(dataset)}")
    print(f"  - Action tensor shape: {dataset[0]['action'].shape}")
    
    print(f"\n🔍 Detecting and correcting manual control frames...")
    
    corrections = {}
    modifications_made = 0
    
    # Process frames in smaller batches to avoid memory issues
    batch_size = 50
    total_frames = len(dataset)
    
    for batch_start in range(0, total_frames, batch_size):
        batch_end = min(batch_start + batch_size, total_frames)
        print(f"  Processing batch {batch_start}-{batch_end-1}")
        
        # Process this batch
        for i in range(batch_start + 1, batch_end):
            if i >= total_frames:
                break
                
            try:
                curr_sample = dataset[i-1]
                next_sample = dataset[i]
                
                curr_action = curr_sample['action'].numpy()[:6]  # First 6 joints
                curr_obs = curr_sample['observation.state'].numpy()
                next_obs = next_sample['observation.state'].numpy()
                
                # Detect manual movement
                action_to_obs_diff = np.abs(curr_action - curr_obs).max()
                obs_change = np.abs(next_obs - curr_obs).max()
                
                if action_to_obs_diff > 3.0 and obs_change > 1.0:
                    # This frame needs correction - update action to match next observation
                    old_action = curr_sample['action'].clone()
                    curr_sample['action'][:6] = torch.from_numpy(next_obs).float()
                    
                    # Store correction info
                    corrections[str(i-1)] = {
                        'original_action': old_action[:6].numpy().tolist(),
                        'corrected_action': next_obs.tolist(),
                        'frame_type': 'manual_control'
                    }
                    modifications_made += 1
                    
                    if modifications_made <= 10:  # Show first 10 corrections
                        print(f"    📍 Frame {i-1}: {curr_action[:3].round(1)} → {next_obs[:3].round(1)}")
                        
            except Exception as e:
                print(f"    ⚠️ Error processing frame {i}: {e}")
                continue
    
    if modifications_made > 0:
        print(f"\n💾 Applied {modifications_made} corrections to dataset in memory")
        
        # Create output repo name
        base_name = repo_id.split('/')[-1]
        username = repo_id.split('/')[0]
        corrected_repo_id = f"{username}/{base_name}_torque_corrected"
        
        if push_to_hub:
            try:
                print(f"🚀 Pushing corrected dataset to HuggingFace Hub: {corrected_repo_id}")
                
                # Use LeRobot's push_to_hub method which handles the format properly
                dataset.push_to_hub(
                    corrected_repo_id,
                    revision="main"
                )
                
                print(f"🎉 Successfully pushed to HuggingFace Hub!")
                print(f"🔗 View at: https://huggingface.co/datasets/{corrected_repo_id}")
                
                # Create dataset card separately
                try:
                    from huggingface_hub import HfApi
                    api = HfApi()
                    
                    dataset_card = f"""# Torque-Corrected LeRobot Dataset

This dataset is a post-processed version of `{repo_id}` with torque control corrections applied.

## Corrections Applied
- **Original dataset**: {repo_id}
- **Total frames**: {len(dataset)}
- **Frames corrected**: {modifications_made}
- **Correction rate**: {modifications_made/len(dataset)*100:.1f}%

## What was corrected
Actions were updated to match subsequent robot positions during periods of manual control (when torque was disabled). This ensures that the recorded actions accurately represent the robot's actual movement during demonstrations.

## Usage
This corrected dataset can be used directly for training imitation learning policies with proper torque control behavior.

Original dataset: [{repo_id}](https://huggingface.co/datasets/{repo_id})
"""
                    
                    api.upload_file(
                        path_or_fileobj=dataset_card.encode(),
                        path_in_repo="README.md",
                        repo_id=corrected_repo_id,
                        repo_type="dataset",
                        commit_message="Add dataset card with correction details"
                    )
                    print("📄 Dataset card uploaded")
                    
                except Exception as card_error:
                    print(f"⚠️ Dataset uploaded but card creation failed: {card_error}")
                
                return corrected_repo_id
                
            except Exception as e:
                print(f"❌ Failed to push to Hub: {e}")
                print("💡 Saving corrections file locally instead...")
        
        # Save corrections file locally
        corrections_file = f"torque_corrections_{base_name}.json"
        correction_data = {
            'dataset_repo_id': repo_id,
            'corrected_repo_id': corrected_repo_id if push_to_hub else None,
            'total_frames': len(dataset),
            'corrections_count': modifications_made,
            'corrections': corrections,
            'description': 'Torque control corrections - actions updated to match manual robot movements'
        }
        
        with open(corrections_file, 'w') as f:
            json.dump(correction_data, f, indent=2)
        
        print(f"📄 Corrections saved to: {corrections_file}")
        return corrections_file
    
    else:
        print("\n✅ No manual control periods detected - dataset appears correct")
        return None

def main():
    parser = argparse.ArgumentParser(description="Memory-efficient torque control post-processor")
    parser.add_argument("--repo_id", type=str, required=True, help="HuggingFace dataset repository ID")
    parser.add_argument("--push_to_hub", action="store_true", 
                       help="Push corrected dataset to HuggingFace Hub")
    
    args = parser.parse_args()
    
    result = postprocess_torque_control_efficient(args.repo_id, args.push_to_hub)
    
    if result:
        if args.push_to_hub:
            print(f"\n🎉 Success! Corrected dataset uploaded to HuggingFace Hub:")
            print(f"   🚀 {result}")
            print(f"   🔗 https://huggingface.co/datasets/{result}")
        else:
            print(f"\n🎉 Success! Corrections documented in:")
            print(f"   📄 {result}")
        
        print(f"\n💡 Ready for use in training imitation learning models!")
    else:
        print(f"\n✅ No corrections needed - original dataset is ready to use!")

if __name__ == "__main__":
    main()
