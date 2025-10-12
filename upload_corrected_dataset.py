#!/usr/bin/env python3
"""
Parquet-compatible torque post-processing for LeRobot datasets.
Uses pandas operations that maintain proper parquet schema.
"""

import argparse
import numpy as np
import pandas as pd
import json
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

def process_and_upload_corrected_dataset(repo_id: str, output_suffix: str = "_torque_corrected", push_to_hub: bool = False):
    """
    Download dataset, apply corrections, and create new parquet with proper schema.
    """
    print(f"🚀 Processing dataset: {repo_id}")
    
    # Download and load original parquet
    parquet_path = hf_hub_download(repo_id=repo_id, filename="data/chunk-000/episode_000000.parquet", repo_type="dataset")
    print(f"📥 Downloaded parquet from {repo_id}")
    
    # Load the parquet file
    df = pd.read_parquet(parquet_path)
    print(f"📊 Loaded {len(df)} frames")
    
    # Load our corrections analysis
    corrections_file = "corrected_dataset_dual_camera_torque_demo_original/corrections_analysis.json"
    if not Path(corrections_file).exists():
        print(f"❌ No corrections file found at {corrections_file}")
        print("Please run the analysis first without --push_to_hub flag")
        return
    
    with open(corrections_file, 'r') as f:
        analysis = json.load(f)
    
    corrections = analysis['corrections']
    print(f"📋 Found {len(corrections)} torque corrections to apply")
    
    # Apply corrections directly to the dataframe
    print("🔧 Applying corrections to parquet data...")
    
    for frame_idx_str, correction_data in corrections.items():
        frame_idx = int(frame_idx_str)
        
        # Get the original action as bytes
        action_bytes = df.iloc[frame_idx]['action']
        
        # Convert to numpy array
        action_array = np.frombuffer(action_bytes, dtype=np.float32).copy()
        
        # Apply correction
        action_array[:6] = np.array(correction_data['corrected_action'], dtype=np.float32)
        
        # Convert back to bytes and update dataframe
        df.iloc[frame_idx, df.columns.get_loc('action')] = action_array.tobytes()
        
        if len(corrections) <= 10 or frame_idx < 50:  # Show progress for first few
            print(f"  ✅ Frame {frame_idx}: Updated action")
    
    print(f"✅ All {len(corrections)} corrections applied to dataframe")
    
    # Save locally first
    local_output_path = Path(f"./final_corrected_{repo_id.split('/')[-1]}")
    local_output_path.mkdir(exist_ok=True)
    
    data_path = local_output_path / "data" / "chunk-000"
    data_path.mkdir(parents=True, exist_ok=True)
    
    corrected_parquet_path = data_path / "episode_000000.parquet"
    print(f"💾 Saving corrected dataset to: {corrected_parquet_path}")
    
    # Save with original schema preserved
    df.to_parquet(corrected_parquet_path, index=False)
    print("✅ Corrected parquet saved successfully!")
    
    # Create README
    readme_content = f"""# Torque-Corrected LeRobot Dataset

This is a corrected version of `{repo_id}` with torque control fixes applied.

## Corrections Applied
- **Observation spikes removed**: {analysis['corrections_identified']['observation_spikes']}
- **Torque corrections**: {len(corrections)}
- **Total frames**: {len(df)}

## Usage
```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset
dataset = LeRobotDataset("{repo_id}{output_suffix}")
```

Original dataset: [{repo_id}](https://huggingface.co/datasets/{repo_id})
"""
    
    with open(local_output_path / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"📄 Dataset card saved")
    
    # Upload to Hub if requested
    if push_to_hub:
        output_repo_id = f"{repo_id}{output_suffix}"
        print(f"🚀 Uploading to HuggingFace Hub: {output_repo_id}")
        
        try:
            api = HfApi()
            api.create_repo(repo_id=output_repo_id, repo_type="dataset", exist_ok=True)
            
            # Upload the corrected dataset
            api.upload_folder(
                folder_path=str(local_output_path),
                repo_id=output_repo_id,
                repo_type="dataset",
                commit_message=f"Add torque-corrected dataset with {len(corrections)} corrections"
            )
            
            print(f"🎉 Successfully uploaded to: https://huggingface.co/datasets/{output_repo_id}")
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            print(f"📁 Dataset saved locally at: {local_output_path}")
    
    print(f"✅ Processing complete!")
    print(f"  - Dataset: {len(df)} frames")
    print(f"  - Corrections: {len(corrections)} torque fixes")
    print(f"  - Local path: {local_output_path}")
    if push_to_hub:
        print(f"  - Hub URL: https://huggingface.co/datasets/{output_repo_id}")

def main():
    parser = argparse.ArgumentParser(description="Upload corrected torque dataset")
    parser.add_argument("--repo_id", type=str, required=True)
    parser.add_argument("--output_suffix", type=str, default="_torque_corrected")
    parser.add_argument("--push_to_hub", action="store_true")
    
    args = parser.parse_args()
    process_and_upload_corrected_dataset(args.repo_id, args.output_suffix, args.push_to_hub)

if __name__ == "__main__":
    main()
