#!/usr/bin/env python3
"""
Test script for Hugging Face authentication and dataset upload functionality.

This script helps verify that Hugging Face authentication is working
and tests the upload process before doing actual recordings.
"""

import os
import sys
from pathlib import Path

def check_huggingface_setup():
    """Check if Hugging Face CLI is installed and user is authenticated."""
    print("🔍 Checking Hugging Face Setup...")
    
    # Check if huggingface_hub is installed
    try:
        import huggingface_hub
        print(f"✅ huggingface_hub installed (version: {huggingface_hub.__version__})")
    except ImportError:
        print("❌ huggingface_hub not installed")
        print("   Install with: pip install huggingface_hub")
        return False
    
    # Check authentication
    try:
        from huggingface_hub import whoami
        user_info = whoami()
        print(f"✅ Authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"❌ Not authenticated with Hugging Face")
        print(f"   Error: {e}")
        print("   Run: huggingface-cli login")
        return False

def test_repository_access():
    """Test creating and accessing a test repository."""
    print("\n🧪 Testing Repository Access...")
    
    try:
        from huggingface_hub import HfApi, create_repo, delete_repo
        
        api = HfApi()
        test_repo_name = "test-rosmaster-dataset"
        
        # Get username
        user_info = api.whoami()
        username = user_info['name']
        repo_id = f"{username}/{test_repo_name}"
        
        print(f"📝 Testing with repository: {repo_id}")
        
        # Try to create a test repository
        try:
            create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=True,  # Use private for testing
                exist_ok=True
            )
            print(f"✅ Repository created/accessed successfully")
            
            # Clean up - delete the test repository
            try:
                delete_repo(repo_id=repo_id, repo_type="dataset")
                print(f"✅ Test repository cleaned up")
            except Exception as e:
                print(f"⚠️  Could not delete test repository: {e}")
                print(f"   You may need to manually delete: https://huggingface.co/datasets/{repo_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Repository creation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Repository access test failed: {e}")
        return False

def show_recording_examples():
    """Show example commands for recording with Hugging Face upload."""
    print("\n📋 Example Recording Commands:")
    
    print("\n1. Record locally (no upload):")
    print("""
lerobot-record \\
  --robot.type=rosmaster \\
  --robot.com="/dev/ttyUSB0" \\
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \\
  --teleop.type=rosmaster_keyboard \\
  --dataset.repo_id="local_user/my_dataset" \\
  --dataset.single_task="Test recording" \\
  --dataset.num_episodes=1 \\
  --dataset.episode_time_s=10 \\
  --dataset.fps=10 \\
  --dataset.push_to_hub=false \\
  --dataset.root="data/recordings"
""")
    
    print("\n2. Record and upload to Hugging Face (public):")
    print("""
lerobot-record \\
  --robot.type=rosmaster \\
  --robot.com="/dev/ttyUSB0" \\
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \\
  --teleop.type=rosmaster_keyboard \\
  --dataset.repo_id="YOUR_USERNAME/rosmaster_demo" \\
  --dataset.single_task="Rosmaster robot demonstration" \\
  --dataset.num_episodes=5 \\
  --dataset.episode_time_s=15 \\
  --dataset.fps=10 \\
  --dataset.push_to_hub=true \\
  --dataset.private=false \\
  --dataset.tags="robotics,rosmaster,imitation-learning,manipulation" \\
  --dataset.root="data/recordings"
""")
    
    print("\n3. Record and upload to Hugging Face (private):")
    print("""
lerobot-record \\
  --robot.type=rosmaster \\
  --robot.com="/dev/ttyUSB0" \\
  --robot.cameras="{front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}}" \\
  --teleop.type=rosmaster_keyboard \\
  --dataset.repo_id="YOUR_USERNAME/private_rosmaster_data" \\
  --dataset.single_task="Private robot training data" \\
  --dataset.num_episodes=10 \\
  --dataset.episode_time_s=20 \\
  --dataset.fps=10 \\
  --dataset.push_to_hub=true \\
  --dataset.private=true \\
  --dataset.tags="robotics,rosmaster,private" \\
  --dataset.root="data/recordings"
""")

def show_manual_upload_examples():
    """Show examples for manually uploading existing datasets."""
    print("\n📤 Manual Upload Examples:")
    
    print("\n1. Upload using huggingface-cli:")
    print("""
# Upload entire dataset folder
huggingface-cli upload-folder \\
  --repo-id="YOUR_USERNAME/my_dataset" \\
  --folder-path="data/recordings" \\
  --repo-type="dataset"

# Upload specific files
huggingface-cli upload \\
  --repo-id="YOUR_USERNAME/my_dataset" \\
  --repo-type="dataset" \\
  data/recordings/data/chunk-000/train-*.parquet
""")
    
    print("\n2. Upload using Python:")
    print("""
from lerobot.datasets import LeRobotDataset

# Load local dataset
dataset = LeRobotDataset("data/recordings")

# Upload to Hub
dataset.push_to_hub(
    repo_id="YOUR_USERNAME/my_dataset",
    private=False,
    tags=["robotics", "rosmaster", "imitation-learning"]
)
""")

def main():
    """Main function to run all tests and show examples."""
    print("🤖 Hugging Face Setup Test for Rosmaster Recording")
    print("=" * 60)
    
    # Test 1: Check basic setup
    if not check_huggingface_setup():
        print("\n❌ Setup incomplete. Please install huggingface_hub and authenticate.")
        print("   Run these commands:")
        print("   pip install huggingface_hub")
        print("   huggingface-cli login")
        return False
    
    # Test 2: Test repository access
    if not test_repository_access():
        print("\n❌ Repository access test failed.")
        print("   Check your authentication token has 'write' permissions.")
        return False
    
    print("\n✅ All tests passed! Your Hugging Face setup is ready.")
    
    # Show examples
    show_recording_examples()
    show_manual_upload_examples()
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Replace 'YOUR_USERNAME' with your actual Hugging Face username")
    print("2. Choose meaningful dataset names")
    print("3. Test with a short recording first")
    print("4. Add descriptive task descriptions and tags")
    print("5. Check https://huggingface.co/datasets/YOUR_USERNAME after upload")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
