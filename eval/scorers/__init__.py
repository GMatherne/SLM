"""Scorers turn (text, scenario) into a dict of metrics.

Each scorer exposes `name` and `score(text, scenario) -> dict`. run_eval.py
merges every enabled scorer's dict into one flat record per output. Add a new
scorer by dropping a module here and wiring it in run_eval.build_scorers().
"""
