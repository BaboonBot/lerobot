#!/usr/bin/env bash
set -euo pipefail

REPO_ID="NLTuan/diffusion_bi_transfer_cleaned"
OUTPUT_DIR="outputs/train/diffusion_bi_transfer_cleaned"
JOB_NAME="diffusion_bi_transfer_cleaned"

CHUNK_SIZE=50000
# 500 epochs over the 90% train split: ceil((47408 * 0.9) / 32) * 500 = 667000
FINAL_STEPS=667000

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found on PATH." >&2
  exit 1
fi
uv run hf auth whoami >/dev/null
uv run wandb status >/dev/null || true


upload_checkpoint() {
  local step="$1"
  local step_id
  step_id="$(printf "%06d" "${step}")"
  local checkpoint_dir="${OUTPUT_DIR}/checkpoints/${step_id}"
  local revision="ckpt-${step_id}"

  if [[ ! -d "${checkpoint_dir}/pretrained_model" || ! -d "${checkpoint_dir}/training_state" ]]; then
    echo "Expected full checkpoint at ${checkpoint_dir}, but it is incomplete or missing." >&2
    exit 1
  fi

  uv run python - "${REPO_ID}" "${revision}" "${checkpoint_dir}" "${step_id}" <<'PY'
import sys
from huggingface_hub import HfApi

repo_id, revision, checkpoint_dir, step_id = sys.argv[1:]
api = HfApi()
api.create_repo(repo_id, repo_type="model", private=False, exist_ok=True)
api.create_branch(repo_id, branch=revision, repo_type="model", exist_ok=True)
api.upload_folder(
    repo_id=repo_id,
    repo_type="model",
    revision=revision,
    folder_path=checkpoint_dir,
    path_in_repo=".",
    commit_message=f"Upload training checkpoint {step_id}",
)
PY
}

delete_checkpoint() {
  local step="$1"
  local step_id
  step_id="$(printf "%06d" "${step}")"
  local checkpoint_dir="${OUTPUT_DIR}/checkpoints/${step_id}"

  if [[ -d "${checkpoint_dir}" ]]; then
    rm -rf "${checkpoint_dir}"
  fi
}

run_first_chunk() {
  uv run lerobot-train \
    --dataset.repo_id=NLTuan/bi_transfer_cleaned \
    --dataset.eval_split=0.1 \
    --policy.type=diffusion \
    --policy.repo_id="${REPO_ID}" \
    --policy.push_to_hub=false \
    --policy.private=false \
    --policy.device=cuda \
    --policy.use_amp=false \
    --policy.n_obs_steps=2 \
    --policy.horizon=32 \
    --policy.n_action_steps=16 \
    --policy.resize_shape=[224,224] \
    --policy.num_train_timesteps=100 \
    --policy.num_inference_steps=50 \
    --policy.optimizer_lr=1e-4 \
    --policy.optimizer_lr_backbone=1e-5 \
    --batch_size=32 \
    --steps="${CHUNK_SIZE}" \
    --save_freq="${CHUNK_SIZE}" \
    --env_eval_freq=0 \
    --eval_steps="${CHUNK_SIZE}" \
    --eval.n_episodes=50 \
    --eval.batch_size=10 \
    --eval.use_async_envs=false \
    --wandb.enable=true \
    --wandb.project=lerobot-diffusion \
    --wandb.mode=online \
    --job_name="${JOB_NAME}" \
    --output_dir="${OUTPUT_DIR}"
}

run_resume_chunk() {
  local previous_step="$1"
  local target_step="$2"
  local previous_id
  previous_id="$(printf "%06d" "${previous_step}")"

  uv run lerobot-train \
    --config_path="${OUTPUT_DIR}/checkpoints/${previous_id}/pretrained_model/train_config.json" \
    --resume=true \
    --policy.push_to_hub=false \
    --steps="${target_step}" \
    --save_freq="${CHUNK_SIZE}" \
    --env_eval_freq=0 \
    --eval_steps="${CHUNK_SIZE}" \
    --eval.n_episodes=50 \
    --eval.batch_size=10 \
    --eval.use_async_envs=false \
    --wandb.enable=true \
    --wandb.project=lerobot-diffusion \
    --wandb.mode=online
}

main() {
  local previous_step=0
  local target_step="${CHUNK_SIZE}"

  while [[ "${previous_step}" -lt "${FINAL_STEPS}" ]]; do
    if [[ "${target_step}" -gt "${FINAL_STEPS}" ]]; then
      target_step="${FINAL_STEPS}"
    fi

    local target_id
    target_id="$(printf "%06d" "${target_step}")"
    local target_checkpoint="${OUTPUT_DIR}/checkpoints/${target_id}"

    if [[ -d "${target_checkpoint}/pretrained_model" && -d "${target_checkpoint}/training_state" ]]; then
      echo "Checkpoint ${target_id} already exists locally; skipping training for this chunk."
    elif [[ "${previous_step}" -eq 0 ]]; then
      run_first_chunk
    else
      run_resume_chunk "${previous_step}" "${target_step}"
    fi

    upload_checkpoint "${target_step}"

    if [[ "${previous_step}" -gt 0 ]]; then
      delete_checkpoint "${previous_step}"
    fi

    previous_step="${target_step}"
    target_step=$((target_step + CHUNK_SIZE))
  done

  echo "Done. Final local checkpoint is ${OUTPUT_DIR}/checkpoints/$(printf "%06d" "${FINAL_STEPS}")"
  echo "Uploaded checkpoint revisions every ${CHUNK_SIZE} steps, plus final ckpt-$(printf "%06d" "${FINAL_STEPS}")"
}
main "$@"
