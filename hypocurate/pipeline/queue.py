"""The queue: claims, the heartbeat and the worker's hold on a run (build step 9b; docs/reviews/step09b_plan.md).

This module is imported by the worker parent, which never imports dspy, litellm or scipy (owner, Q2: memory).
"""
from __future__ import annotations

# How a claim ends (migration 0008 holds the same list).
RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")
