# SO-101

LeRobot 0.6.2 scripts for the SO-101 arm. Ports, calibration files, and the wrist camera are in `config.json`. Data is not uploaded.

```bash
conda activate lerobot
```

## Record

```bash
python collect.py preview
python collect.py record --name <name> --episodes 2
python collect.py record --name <name> --episodes 20 --resume
python collect.py inspect --name <name>
```

Press Enter to start an episode, Enter again to end it, then `s` to save or `f` to discard. `q` stops while waiting. An existing directory is not overwritten.

| Directory | Episodes | Use |
| --- | ---: | --- |
| `data/pick_place` | 54 | Task 1 v18 Diffusion and v19 ACT (39,443 recorded frames) |
| `data/task1_home` | 54 | Separate home-start collection (24,050 recorded frames) |
| `data/cube_stack_80_10_13` | 103 | Task 2 v29 block stacking |

The [Task 1 training log](https://github.com/Azhuan-zhou/HRL_2/blob/c9144209dc6276bb6854c2b08460599573357159/LOG.md#L177-L183) identifies `data/pick_place` as the input to both comparison models. The [dataset log](https://github.com/Azhuan-zhou/HRL_2/blob/c9144209dc6276bb6854c2b08460599573357159/LOG.md#L113-L115) records the separate home-start collection.

## Train

```bash
python train_trim.py --drop_first=auto --drop_last=20 --config_path=configs/bench_v30m.json
python fix_dell_model.py models/<model>
```

[`v18.json`](configs/v18.json) (Diffusion) and [`v19.json`](configs/v19.json) (ACT) each train for 6,000 steps on `data/pick_place`.

For stacking, [`v20.json`](configs/v20.json) and [`v21.json`](configs/v21.json) are earlier 20,000-step runs on `data/cube_stack`. [`bench_v30m.json`](configs/bench_v30m.json) is a 30-step smoke test on `data/cube_stack_80_10_13`. The [original deployment notes](https://github.com/Azhuan-zhou/HRL_2/blob/c886db3b1891a7a4ac1b952aad25dafafc8ecb5c/README.md#L89-L114) identify the classroom model as `v29_stack80_10_13_imnet` at 30,000 steps, with an ImageNet-pretrained ResNet-18, 2 observation steps, a 64-step horizon, and 30 executed actions per plan.

## Evaluate Task 1

See [the rollout manifest and reproduction instructions](task1_step/) for all 50 scored trials, candidate videos, STEP, Wilson intervals, and posterior violins. The score sheet records 60 s for every failed trial and includes 14 successes beyond 30 s. The 30 s in [`configs/eval_rollout.json`](configs/eval_rollout.json) is the shared runner default. The original Task 1 invocation and timer logs are unavailable here.

## Deploy Task 2

The recorded launch command for the 30,000-step checkpoint uses the stacking start pose, a 240 s limit, 5 DDIM inference steps, and an override of the default relative-target cap.

```bash
python eval.py --policy.path=models/v29_stack80_10_13_imnet \
  --start=stack --duration=240 --policy.num_inference_steps=5 \
  --robot.max_relative_target=null
```

`--start=home` uses `configs/home_pose.json`. `--grip_offset=8` closes the gripper further while the policy command stays below 20. The default is 0.

The classroom deployment requires the v29 checkpoint directory with its saved policy and processor configuration. That directory and the original training configuration are unavailable in this checkout. The launch command above records the known runtime overrides.

`data/`, `models/`, `runs/`, and `logs/` are gitignored.
