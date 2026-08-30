# Evaluation

`scripts/evaluate_all.py` enumerates all scenario folders, runs the numerical detector and retrieval evaluation, records the configuration, seed, timestamp and Git commit, and writes `data/evaluation/latest.json`.

The compact dataset is intended to prove reproducibility and exercise failure paths. It is not statistically representative of production incidents. Root-cause labels in this first dataset are used to validate the ranking workflow; future work should add noisy multi-fault incidents, blinded labels and confidence calibration.
