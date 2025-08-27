#!/bin/bash

# Official LeRobot CLI Recording Script for Rosmaster Robot
# This uses the built-in lerobot-record command

echo "🤖 Rosmaster Data Recording using LeRobot CLI"
echo "=============================================="

# Set your Hugging Face username (optional for local recording)
HF_USER=$(huggingface-cli whoami 2>/dev/null | head -n 1 || echo "local_user")
echo "📁 HF User: $HF_USER"

# Recording with cameras (full setup)
echo "📹 Recording with cameras..."
lerobot-record \
  --robot.type=rosmaster \
  --robot.com="/dev/ttyUSB0" \
  --robot.id="my_rosmaster_robot" \
  --robot.cameras="{ 
    front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30}, 
    wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}
  }" \
  --teleop.type=rosmaster_keyboard \
  --teleop.joint_step=2.0 \
  --dataset.repo_id="${HF_USER}/rosmaster_pick_place" \
  --dataset.single_task="Pick up the object and place it in the target location" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=15 \
  --dataset.fps=30 \
  --dataset.push_to_hub=false \
  --display_data=true

echo "✅ Recording completed!"
