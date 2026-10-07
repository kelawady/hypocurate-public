"""The price table for model calls (step 8a; register entry 'model_prices').

Cost is computed by code from the token usage the provider reports, times this table: the provider
reports tokens, not money. Each model call stores the table's version (`PRICE_TABLE_VERSION`), so a
cost can be recomputed if prices change. Prices are US dollars per million tokens, from Anthropic's
published pricing as cached on 2026-09-25; before the first live call the table is checked against
the published page, and work stops if it differs (owner, 2026-10-06).

Cache writes cost 1.25 times the input price (the five-minute cache). The agents never ask for
prompt caching, so cache reads and writes are expected to be zero; they are priced in case the
provider reports any.

The maximum cost reserved before a request (`max_cost`) is an upper bound: every token of the
request is counted as at least one byte of its UTF-8 JSON (a token is never shorter than a byte),
plus a fixed allowance for the provider's own framing, all at the input price, and the request's
output limit at the output price (thinking tokens are output tokens and fall under the same limit).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

PRICE_TABLE_VERSION = "anthropic-2026-09-25"
PER_MILLION = Decimal(1_000_000)
FRAMING_ALLOWANCE_TOKENS = 1000  # the provider's own tokens around a request (system framing)


@dataclass(frozen=True)
class Price:
    input: Decimal
    output: Decimal
    cache_read: Decimal
    cache_write: Decimal


PRICES = MappingProxyType({
    "claude-opus-5-5": Price(Decimal("4"), Decimal("20"), Decimal("0.20"), Decimal("5")),
    "claude-sonnet-5-5": Price(Decimal("2"), Decimal("10"), Decimal("0.20"), Decimal("2.5")),
    "claude-haiku-4-5": Price(Decimal("1"), Decimal("5"), Decimal("0.10"), Decimal("1.25")),
})
# How litellm names each model (provider prefix).
PROVIDER_MODEL = MappingProxyType({m: f"anthropic/{m}" for m in PRICES})


class UnknownModel(Exception):
    """A model without a price cannot be called: its cost could not be computed or capped."""


def price(model: str) -> Price:
    if model not in PRICES:
        raise UnknownModel(model)
    return PRICES[model]


def max_cost(model: str, request_bytes: int, max_output_tokens: int) -> Decimal:
    """The most the request can cost (see the module docstring)."""
    p = price(model)
    return ((Decimal(request_bytes + FRAMING_ALLOWANCE_TOKENS) * p.input
             + Decimal(max_output_tokens) * p.output) / PER_MILLION)


def cost(model: str, input_tokens: int, output_tokens: int, cache_read_tokens: int, cache_write_tokens: int) -> Decimal:
    """The cost of a reported usage. `input_tokens` includes the cached ones (as reported)."""
    p = price(model)
    uncached = input_tokens - cache_read_tokens - cache_write_tokens
    if min(uncached, output_tokens, cache_read_tokens, cache_write_tokens) < 0:
        raise ValueError("token counts do not add up")
    return (Decimal(uncached) * p.input + Decimal(cache_read_tokens) * p.cache_read
            + Decimal(cache_write_tokens) * p.cache_write + Decimal(output_tokens) * p.output) / PER_MILLION
