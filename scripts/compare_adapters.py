#!/usr/bin/env python3
"""Comparative READ: 100-gold adapter vs live adapter on 5 prompts.

Uses the product's own Engine class (which handles mlx-lm sampler API correctly)
to generate 5 outputs per adapter and print them side-by-side for human comparison.

PAUSE qc_queue before running. Run one at a time: live adapter unloads before
the new adapter loads.

Usage: PYTHONPATH=src python scripts/compare_adapters.py
"""
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from imagination_engine.inference import Engine
from imagination_engine.config import config

LIVE_ADAPTER = str(Path(__file__).parent.parent / "data/model/adapters")
NEW_ADAPTER  = str(Path.home() / "Downloads/hearth-corpus/GOLD-ADAPTER-0707-1536-n100")

PROMPTS = [
    "walking through a dark pine forest in early morning",
    "the first time meeting someone who will matter",
    "being inside a hurricane eye",
    "the day I finally quit smoking",
    "swimming to the bottom of a still lake",
]

SYSTEM = (
    "You are the Imagination Engine. Write a guided imagination script for the "
    "scene below. Second person, present tense. Vivid, concrete, sensory. "
    "Unique opening (not 'You close your eyes'). 200-300 words."
)

MAX_TOKENS = 400


def gen_with_adapter(adapter_path: str, prompts: list) -> list:
    print(f"\nLoading adapter: {adapter_path}", flush=True)
    engine = Engine.load(model_id=config.model_id, adapter_path=adapter_path)
    outputs = []
    for p in prompts:
        chunks = list(engine.stream(
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Scene: {p}"},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.85,
        ))
        outputs.append("".join(chunks))
        print(f"  [{p[:30]}...] done", flush=True)
    del engine
    return outputs


def main():
    live_out = gen_with_adapter(LIVE_ADAPTER, PROMPTS)
    new_out  = gen_with_adapter(NEW_ADAPTER,  PROMPTS)

    divider = "=" * 80
    for i, prompt in enumerate(PROMPTS):
        print(f"\n{divider}")
        print(f"PROMPT {i+1}: {prompt}")
        print(divider)
        print("\n--- LIVE ADAPTER ---")
        print(textwrap.fill(live_out[i], 78))
        print("\n--- 100-GOLD ADAPTER ---")
        print(textwrap.fill(new_out[i], 78))

    print(f"\n{divider}")
    print("READ: check for (1) unique openings, (2) concrete sensory detail,")
    print("(3) scene specificity matching prompt, (4) no collapse/repetition.")
    print("Promote GOLD-ADAPTER-0707-1536-n100 only if clearly >= live.")


if __name__ == "__main__":
    main()
