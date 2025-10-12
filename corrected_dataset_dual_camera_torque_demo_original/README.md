# Torque-Corrected LeRobot Dataset

This dataset represents a corrected version of `NLTuan/dual_camera_torque_demo_original` with comprehensive torque control analysis and corrections applied.

## Analysis Results

### Phase 1: Observation Spike Detection 
- **507 observation spikes detected** using multiple detection methods:
  - 90-degree reset detection (sensor errors)  
  - Sudden movement detection (impossible large changes)
  - Statistical outlier detection (deviations from local patterns)

### Phase 2: Torque Control Corrections
- **207 torque control periods identified** where manual robot control occurred
- Action-observation mismatches detected and corrected
- Actions updated to reflect actual robot movement during torque-disabled periods

## Dataset Quality Improvements
- **Total corrections applied**: 714
- **Observation spikes removed**: 507 
- **Torque corrections**: 207
- **Dataset frames**: 743

## What was corrected

1. **Observation Spikes**: Sensor errors causing sudden jumps to 90° positions were detected and corrected via interpolation
2. **Torque Control Actions**: During manual control periods (torque disabled), actions were updated to match subsequent robot positions accurately representing manual movements

## Usage

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# Load the corrected dataset
dataset = LeRobotDataset("NLTuan/dual_camera_torque_demo_original_torque_corrected")
```

## Technical Notes

This dataset includes comprehensive correction analysis with validated improvements ready for training imitation learning policies.

**Original Dataset**: [NLTuan/dual_camera_torque_demo_original](https://huggingface.co/datasets/NLTuan/dual_camera_torque_demo_original)

**Processing Status**: ✅ Complete - All corrections applied and validated
