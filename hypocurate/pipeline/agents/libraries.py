"""The one place that imports the model-call libraries, DSPy and litellm (step 8a).

`load()` sets their environment before importing them, every time, overriding whatever the
process had:
- `LITELLM_MODE=PRODUCTION`: otherwise litellm reads a `.env` file when it is imported (the file
  guard caught it reading the repository's `.env`, which holds the secrets);
- `LITELLM_LOCAL_MODEL_COST_MAP=True`: litellm uses the price map shipped with it instead of
  fetching one over the network. Our costs come from our own price table, never from litellm's.

Then it turns off litellm's own retries (one HTTP request is one recorded model call; retries are
ours, each reserved and recorded) and DSPy's caches (a cached answer would be a model output that
no recorded call produced).
"""
from __future__ import annotations

import os
from types import MappingProxyType

LIBRARY_ENVIRONMENT = MappingProxyType({
    "LITELLM_MODE": "PRODUCTION",
    "LITELLM_LOCAL_MODEL_COST_MAP": "True",
})


def load():
    """Returns the modules (litellm, dspy), imported with their environment set."""
    for name, value in LIBRARY_ENVIRONMENT.items():
        os.environ[name] = value
    import litellm
    litellm.num_retries = 0
    litellm.telemetry = False
    litellm.suppress_debug_info = True
    import dspy
    dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)
    return litellm, dspy


def lm15():
    """DSPy's provider-neutral request, response and error types (after `load`)."""
    load()
    from dspy import lm15 as module
    return module


def litellm_engine(**client_options):
    """DSPy's one-attempt litellm engine (after `load`)."""
    load()
    from dspy.clients.engines.litellm_engine import LiteLLMEngine
    return LiteLLMEngine(**client_options)


def request_kwargs(request) -> dict:
    """A DSPy request as the keyword arguments litellm receives (after `load`)."""
    load()
    from dspy.clients.lm15_boundary import request_kwargs as convert
    return convert(request, "chat")
