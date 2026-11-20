# Task 1 rollout records and analysis

[`rollout_manifest.csv`](rollout_manifest.csv) transcribes the 25 ACT and 25 Diffusion rows from the two policy sheets of `SO101_Task1_25_Episode_Evaluation.xlsx`. The worksheet assigns configuration IDs C01–C25 to the matched initial cube/tray layouts. It supplies IDs without physical coordinates. The stage flags, binary result, partial score, time in seconds, and failure note are the recorded values.

All 19 failed trials have a recorded time of 60 s. Four ACT and ten Diffusion successes exceed 30 s. The 30 s in [`configs/eval_rollout.json`](../configs/eval_rollout.json) is the runner default. The original Task 1 invocation, timer log, and reason-specific elapsed stop times are unavailable here.

The worksheet's video column is blank. The candidate video links match the episode number to the filename in each policy's Drive folder. `filename_match` records that association. `duplicate_clip` and `duplicate_clip_and_score_conflict` flag entries that need the original run-to-file mapping. ACT 17 and Diffusion 6 have identical bytes, as do ACT 18 and Diffusion 7. The Diffusion 6 candidate shows a completed placement, while the row records a grasp failure. All statistics use the worksheet labels.

To reproduce the analysis with Python 3.12, run these commands from this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analyze.py rollout_manifest.csv
```

The script writes `step_results/summary.txt` and `step_results/posterior_violin.png`. It runs mirrored STEP ranking with a 25-pair budget, alpha 0.10, a linear risk budget, and seed 42. Success rates, 90% Wilson intervals, timing summaries, partial scores, and Beta posterior violins use the full set of recorded trials. A shared letter on the violins indicates an inconclusive STEP comparison. The [executed notebook](Task1_STEP_executed.ipynb) also contains the original STEP comparison, Wilson intervals, and posterior violins.
