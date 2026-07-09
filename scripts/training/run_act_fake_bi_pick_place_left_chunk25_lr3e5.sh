#!/usr/bin/env bash
set -euo pipefail

DATASET_REPO_ID="vraiRobotLab/fake_bi_pick_place_left"
REPO_ID="NLTuan/act_fake_bi_pick_place_left_chunk25_lr3e5"
OUTPUT_DIR="outputs/train/act_fake_bi_pick_place_left_chunk25_lr3e5"
JOB_NAME="act_fake_bi_pick_place_left_chunk25_lr3e5"
WANDB_PROJECT="act-fake-bi-pick-place"

CHUNK_SIZE=5000
EVAL_STEPS=5000
FINAL_STEPS=30000

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found on PATH." >&2
  exit 1
fi
uv run hf auth whoami >/dev/null
uv run wandb status >/dev/null || true

remote_pretrained_revision_exists() {
  local revision="$1"

  uv run python - "${REPO_ID}" "${revision}" <<'PY_REMOTE'
import sys
from huggingface_hub import HfApi
from huggingface_hub.errors import RepositoryNotFoundError, RevisionNotFoundError

repo_id, revision = sys.argv[1:]
api = HfApi()
try:
    files = set(api.list_repo_files(repo_id, repo_type="model", revision=revision))
except (RepositoryNotFoundError, RevisionNotFoundError):
    raise SystemExit(1)

required = {"config.json", "model.safetensors"}
raise SystemExit(0 if required.issubset(files) else 1)
PY_REMOTE
}

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

  if remote_pretrained_revision_exists "${revision}"; then
    echo "Checkpoint ${revision} already exists on Hugging Face; skipping upload."
    return
  fi

  uv run python - "${REPO_ID}" "${revision}" "${checkpoint_dir}" "${step_id}" <<'PY_UPLOAD'
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
    folder_path=f"{checkpoint_dir}/pretrained_model",
    path_in_repo=".",
    commit_message=f"Upload pretrained model files for checkpoint {step_id}",
)
api.upload_folder(
    repo_id=repo_id,
    repo_type="model",
    revision=revision,
    folder_path=f"{checkpoint_dir}/training_state",
    path_in_repo="training_state",
    commit_message=f"Upload training state for checkpoint {step_id}",
)
PY_UPLOAD
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

latest_local_checkpoint_step() {
  local checkpoint_root="${OUTPUT_DIR}/checkpoints"

  if [[ ! -d "${checkpoint_root}" ]]; then
    echo 0
    return
  fi

  find "${checkpoint_root}" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" \
    | awk '/^[0-9]+$/ { print $0 + 0 }' \
    | while read -r step; do
        local step_id
        step_id="$(printf "%06d" "${step}")"
        if [[ -d "${checkpoint_root}/${step_id}/pretrained_model" && -d "${checkpoint_root}/${step_id}/training_state" ]]; then
          echo "${step}"
        fi
      done \
    | sort -n \
    | tail -1
}

run_first_chunk() {
  uv run lerobot-train \
    --dataset.repo_id="${DATASET_REPO_ID}" \
    --dataset.eval_split=0.1 \
    --policy.type=act \
    --policy.repo_id="${REPO_ID}" \
    --policy.push_to_hub=false \
    --policy.private=false \
    --policy.device=cuda \
    --policy.use_amp=false \
    --policy.n_obs_steps=1 \
    --policy.chunk_size=25 \
    --policy.n_action_steps=25 \
    --policy.normalization_mapping='{"ACTION": "MIN_MAX", "STATE": "MIN_MAX", "VISUAL": "MEAN_STD"}' \
    --policy.optimizer_lr=3e-5 \
    --policy.optimizer_lr_backbone=3e-5 \
    --batch_size=64 \
    --steps="${CHUNK_SIZE}" \
    --save_freq="${CHUNK_SIZE}" \
    --env_eval_freq=0 \
    --eval_steps="${EVAL_STEPS}" \
    --eval.n_episodes=50 \
    --eval.batch_size=10 \
    --eval.use_async_envs=false \
    --wandb.enable=true \
    --wandb.disable_artifact=true \
    --wandb.project="${WANDB_PROJECT}" \
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
    --eval_steps="${EVAL_STEPS}" \
    --eval.n_episodes=50 \
    --eval.batch_size=10 \
    --eval.use_async_envs=false \
    --wandb.enable=true \
    --wandb.disable_artifact=true \
    --wandb.project="${WANDB_PROJECT}" \
    --wandb.mode=online
}

main() {
  local previous_step
  previous_step="$(latest_local_checkpoint_step)"
  previous_step="${previous_step:-0}"

  if [[ "${previous_step}" -gt 0 ]]; then
    echo "Resuming from local checkpoint $(printf "%06d" "${previous_step}")."
    upload_checkpoint "${previous_step}"
  fi

  local target_step=$((previous_step + CHUNK_SIZE))

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

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
