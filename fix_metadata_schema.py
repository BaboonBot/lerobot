#!/usr/bin/env python3
"""
Fix metadata schema mismatch by regenerating proper metadata files for the corrected dataset
"""
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

def fix_metadata_schema(dataset_dir):
    """
    Fix the metadata schema mismatch by regenerating consistent metadata files
    """
    print(f"🔧 Fixing metadata schema for: {dataset_dir}")
    
    # Load the corrected parquet data
    parquet_path = os.path.join(dataset_dir, "episode_000000.parquet")
    df = pd.read_parquet(parquet_path)
    
    print(f"📊 Dataset info:")
    print(f"  - Total frames: {len(df)}")
    print(f"  - Columns: {list(df.columns)}")
    
    # Create meta directory if it doesn't exist
    meta_dir = os.path.join(dataset_dir, "meta")
    os.makedirs(meta_dir, exist_ok=True)
    
    # 1. Create episodes.jsonl with simple schema
    episodes_data = {
        "episode_index": 0,
        "tasks": ["Pick and place"],  # Simple string list
        "length": len(df)
    }
    
    episodes_path = os.path.join(meta_dir, "episodes.jsonl")
    with open(episodes_path, 'w') as f:
        f.write(json.dumps(episodes_data) + '\n')
    
    print(f"✅ Created {episodes_path}")
    
    # 2. Remove episodes_stats.jsonl to avoid schema conflict
    episodes_stats_path = os.path.join(meta_dir, "episodes_stats.jsonl")
    if os.path.exists(episodes_stats_path):
        os.remove(episodes_stats_path)
        print(f"🗑️ Removed conflicting {episodes_stats_path}")
    
    # 3. Create info.json with basic dataset info
    info_data = {
        "codebase_version": "0.3.4",
        "robot_type": "rosmaster",
        "total_episodes": 1,
        "total_frames": len(df),
        "total_tasks": 1,
        "fps": 30,
        "episode_length": len(df),
        "data_type": "lerobot_dataset",
        "encoding": "h264",
        "video": {
            "observation.images.front": {
                "shape": [480, 640, 3],
                "names": ["height", "width", "channel"]
            },
            "observation.images.wrist": {
                "shape": [480, 640, 3],
                "names": ["height", "width", "channel"]
            }
        }
    }
    
    info_path = os.path.join(meta_dir, "info.json")
    with open(info_path, 'w') as f:
        json.dump(info_data, f, indent=2)
    
    print(f"✅ Created {info_path}")
    
    # 4. Create tasks.jsonl with simple task info
    tasks_data = {
        "task_index": 0,
        "task": "Pick and place"
    }
    
    tasks_path = os.path.join(meta_dir, "tasks.jsonl")
    with open(tasks_path, 'w') as f:
        f.write(json.dumps(tasks_data) + '\n')
    
    print(f"✅ Created {tasks_path}")
    
    print(f"\n🎉 Metadata files regenerated successfully!")
    print(f"   - Simple schema used for consistency")
    print(f"   - Removed conflicting statistics file")
    print(f"   - Dataset should now load properly in HuggingFace viewer")

if __name__ == "__main__":
    dataset_dir = "corrected_dataset_dual_camera_torque_demo_v2"
    fix_metadata_schema(dataset_dir)
