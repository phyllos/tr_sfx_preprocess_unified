#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from functions.common.config import load_config, normalize_config
from functions.common.memory_monitor import current_rss, process_peak_rss, run_step

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args():
    parser=argparse.ArgumentParser(description="Unified TR-SFX dark/light preprocessing driver")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--list-steps", action="store_true")
    return parser.parse_args()


def select_steps(pipeline, start, stop):
    names=[name for name,_ in pipeline]
    start=start or names[0]; stop=stop or names[-1]
    if start not in names or stop not in names:
        raise ValueError(f"Available steps: {names}")
    i=names.index(start); j=names.index(stop)
    if i>j: raise ValueError("pipeline.start_step must not come after stop_step")
    return pipeline[i:j+1]


def main():
    args=parse_args(); config_path=args.config.expanduser().resolve()
    raw=load_config(config_path); cfg=normalize_config(raw, config_path, PROJECT_ROOT)
    mode=cfg["dataset"]["mode"]
    module=importlib.import_module(f"functions.{mode}.pipeline")
    pipeline=module.get_pipeline()
    if args.list_steps:
        print(" ".join(name for name,_ in pipeline)); return
    state={"config":cfg,"artifacts":{}}
    module.prepare_state(state)
    selection=cfg.get("pipeline",{})
    selected=select_steps(pipeline, str(selection.get("start_step") or "").upper() or None, str(selection.get("stop_step") or "").upper() or None)
    print("="*72); print("Unified TR-SFX preprocessing"); print(f"mode: {mode}"); print(f"config: {config_path}"); print("steps: "+" -> ".join(name for name,_ in selected)); print(f"initial RSS: {current_rss()} | peak: {process_peak_rss()}"); print("="*72)
    for name,function in selected:
        run_step(f"{mode} {name}", function, state)
    print("="*72); print("Pipeline complete")
    for name,path in state["artifacts"].items(): print(f"{name}: {path}")
    print(f"final RSS: {current_rss()} | peak: {process_peak_rss()}")


if __name__ == "__main__": main()
