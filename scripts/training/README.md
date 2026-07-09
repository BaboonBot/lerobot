# Training Bash Scripts

This directory contains local training launchers for the LeRobot runs used in this workspace. They are intended to be run from the repository root:

```bash
cd /workspace/lerobot
bash scripts/training/<script-name>.sh
```

Most scripts are **chunked**. A chunked script trains to the next checkpoint, uploads that checkpoint to Hugging Face as a revision, deletes the previous local checkpoint, and continues. This keeps disk usage bounded while still preserving intermediate checkpoints online.

## Common Requirements

Before running these scripts:

```bash
uv run hf auth whoami
uv run wandb status
```

The scripts assume:

- Hugging Face auth is already configured.
- W&B auth is already configured if `--wandb.mode=online`.
- The command is run from `/workspace/lerobot`.
- Enough disk is available for the current checkpoint, W&B logs, and upload staging.

Check storage:

```bash
df -h /workspace/lerobot
```

Check active training jobs:

```bash
ps -eo pid,ppid,sid,etime,cmd | rg 'lerobot-train|run_.*\\.sh'
```

## Running Detached

To keep a run alive without attaching it to a tmux window, use `setsid`:

```bash
setsid -f bash -lc 'cd /workspace/lerobot; bash scripts/training/run_act_fake_bi_pick_place_left_chunked.sh > /tmp/act_left.log 2>&1'
tail -n 120 /tmp/act_left.log
```

Avoid launching these from a tmux helper that creates or closes windows unless that is intentional.

## Checkpoint Upload Behavior

Each chunked script:

1. Trains until the next target step.
2. Expects a full local checkpoint at `OUTPUT_DIR/checkpoints/<step>/`.
3. Creates or reuses a Hugging Face model repo.
4. Creates a revision named `ckpt-XXXXXX`.
5. Uploads `pretrained_model/` to the revision root.
6. Uploads `training_state/` under `training_state/`.
7. Deletes the previous local checkpoint after the new one is uploaded.

Example revision names:

```text
ckpt-005000
ckpt-010000
ckpt-020000
ckpt-100000
```

The final local checkpoint is kept. Older local checkpoints are removed by the script, but their Hugging Face revisions remain.

For inference, the important files are in the revision root, especially:

```text
config.json
model.safetensors
train_config.json
policy_preprocessor.json
policy_postprocessor.json
```

The uploaded `training_state/` is for resuming training, not normal inference.

## Resume Behavior

On startup, each script checks `OUTPUT_DIR/checkpoints/` for the latest complete local checkpoint. If it finds one, it resumes from that checkpoint and continues to `FINAL_STEPS`.

If a Hugging Face revision already contains `config.json` and `model.safetensors`, upload for that revision is skipped.

Important: LeRobot resume restores optimizer state from `training_state/`. If you try to change learning rate only by passing a new CLI flag during resume, the optimizer state can overwrite it. For real per-chunk LR schedules, edit the saved optimizer param groups or run a fresh output directory.

## ACT Fake Bimanual Pick Place Scripts

These scripts train ACT on `vraiRobotLab/fake_bi_pick_place` and `vraiRobotLab/fake_bi_pick_place_left`.

All current ACT scripts use:

```bash
--policy.normalization_mapping='{"ACTION": "MIN_MAX", "STATE": "MIN_MAX", "VISUAL": "MEAN_STD"}'
```

This matters. The default ACT action/state normalization is not ideal for these datasets because near-constant state/action dimensions can blow up under mean/std normalization.

| Script | Dataset | HF repo | LR | Chunk / eval | Final steps | ACT chunk |
| --- | --- | --- | --- | --- | --- | --- |
| `run_act_fake_bi_pick_place_chunked.sh` | `vraiRobotLab/fake_bi_pick_place` | `NLTuan/act_fake_bi_pick_place` | `1e-5` | train 10k, eval 5k | 50k | 50 |
| `run_act_fake_bi_pick_place_lr3e5_chunked.sh` | `vraiRobotLab/fake_bi_pick_place` | `NLTuan/act_fake_bi_pick_place_lr3e5` | `3e-5` | train 10k, eval 5k | 50k | 50 |
| `run_act_fake_bi_pick_place_lr1e4_chunked.sh` | `vraiRobotLab/fake_bi_pick_place` | `NLTuan/act_fake_bi_pick_place_lr1e4` | `1e-4` | train 10k, eval 5k | 50k | 50 |
| `run_act_fake_bi_pick_place_left_chunked.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left` | `3e-5` | train/eval 5k | 50k | 50 |
| `run_act_fake_bi_pick_place_left_lr1e4_short.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_lr1e4` | `1e-4` | train/eval 5k | 10k | 50 |
| `run_act_fake_bi_pick_place_left_lr1e5_short.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_lr1e5` | `1e-5` | train/eval 5k | 20k | 50 |
| `run_act_fake_bi_pick_place_left_lr1e5_30k.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_lr1e5_30k` | `1e-5` | train/eval 5k | 30k | 50 |
| `run_act_fake_bi_pick_place_left_lr3e5_30k.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_lr3e5_30k` | `3e-5` | train/eval 5k | 30k | 50 |
| `run_act_fake_bi_pick_place_left_lr6e5_30k.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_lr6e5_30k` | `6e-5` | train/eval 5k | 30k | 50 |
| `run_act_fake_bi_pick_place_left_chunk25_lr3e5.sh` | `vraiRobotLab/fake_bi_pick_place_left` | `NLTuan/act_fake_bi_pick_place_left_chunk25_lr3e5` | `3e-5` | train/eval 5k | 30k | 25 |

Known useful checkpoints from prior runs:

- Right arm `3e-5`: best validation loss around `ckpt-015000`.
- Left arm `3e-5`: best validation loss around `ckpt-010000`.
- Left arm `1e-5` and `6e-5` sweeps did not beat the left `3e-5` validation floor.

## Diffusion Scripts

These scripts train diffusion policies and use the same checkpoint revision pattern.

| Script | Task / dataset | HF repo | LR | Batch | Chunk | Final steps | Horizon / action steps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run_diffusion_pusht_chunked.sh` | `lerobot/pusht`, `env.type=pusht` | `NLTuan/diffusion_pusht` | `1e-4` | 32 | 20k | 100k | 16 / 8 |
| `run_diffusion_aloha_transfer_cube_chunked.sh` | ALOHA transfer cube sim, `env.type=aloha` | `NLTuan/diffusion_aloha_transfer_cube` | `1e-4` | 24 | 20k | 100k | 64 / 32 |
| `run_diffusion_bi_transfer_cleaned_chunked.sh` | cleaned bimanual transfer dataset | `NLTuan/diffusion_bi_transfer_cleaned` | `1e-4` | 64 | 20k | 133400 | 32 / 16 |

The ALOHA script exports:

```bash
MUJOCO_GL=egl
PYOPENGL_PLATFORM=egl
```

This avoids GLFW display initialization failures during headless simulation eval.

## W&B Notes

Most scripts set:

```bash
--wandb.enable=true
--wandb.mode=online
--wandb.disable_artifact=true
```

`--wandb.disable_artifact=true` is intentional. Checkpoint storage is handled by Hugging Face revisions instead of W&B artifacts, which avoids W&B staging large model files under `~/.local/share/wandb/artifacts/staging`.

## Local Cleanup

The scripts automatically delete the previous checkpoint after the next checkpoint uploads successfully. To inspect disk usage:

```bash
du -h -d 3 outputs/train | sort -h | tail -n 30
```

Do not manually delete the current latest checkpoint for an active run unless you are intentionally abandoning resume capability.

## Adding A New Experiment

The safest way to add a new training experiment is:

1. Copy the closest existing script.
2. Change `REPO_ID`, `OUTPUT_DIR`, and `JOB_NAME` together.
3. Change only the experiment parameters: LR, batch size, chunk length, horizon, etc.
4. Keep checkpoint upload/delete logic unchanged.
5. Run `bash -n scripts/training/<new-script>.sh`.
6. Start detached with `setsid` and a unique `/tmp/*.log`.

Example:

```bash
cp scripts/training/run_act_fake_bi_pick_place_left_chunked.sh scripts/training/run_act_fake_bi_pick_place_left_new_exp.sh
bash -n scripts/training/run_act_fake_bi_pick_place_left_new_exp.sh
setsid -f bash -lc 'cd /workspace/lerobot; bash scripts/training/run_act_fake_bi_pick_place_left_new_exp.sh > /tmp/act_left_new_exp.log 2>&1'
```
