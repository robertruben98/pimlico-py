"""Live integration tests against the real Pimlico API.

These are marked ``integration`` and deselected by default (see the ``addopts``
in ``pyproject.toml``). They run only when ``PIMLICO_API_KEY`` is set and are
invoked explicitly with ``pytest -m integration``:

    PIMLICO_API_KEY=pim_... pytest -m integration

They hit the network and assert on the documented contract shapes rather than
exact values, since gas prices and supported entry points change over time.
"""

import os

import pytest

from pimlico import AsyncPimlicoClient, PimlicoClient
from pimlico.models import ENTRYPOINT_V07

pytestmark = pytest.mark.integration

API_KEY = os.environ.get("PIMLICO_API_KEY")
# Sepolia testnet — supported by Pimlico's free tier.
CHAIN = int(os.environ.get("PIMLICO_CHAIN", "11155111"))

requires_key = pytest.mark.skipif(
    not API_KEY, reason="PIMLICO_API_KEY not set; skipping live integration test"
)


def _api_key() -> str:
    """Return the API key, narrowed to ``str``.

    These tests only run under ``@requires_key``, which guarantees the key is
    set; the assertion narrows the ``Optional[str]`` for the type checker.
    """
    assert API_KEY is not None
    return API_KEY


@requires_key
def test_live_supported_entry_points_includes_v07():
    with PimlicoClient(api_key=_api_key(), chain=CHAIN) as client:
        entry_points = client.eth_supported_entry_points()

    assert isinstance(entry_points, list)
    assert entry_points, "expected at least one supported entry point"
    # Pimlico bundlers support EntryPoint v0.7.
    normalized = {ep.lower() for ep in entry_points}
    assert ENTRYPOINT_V07.lower() in normalized


@requires_key
def test_live_gas_price_tiers_are_hex():
    with PimlicoClient(api_key=_api_key(), chain=CHAIN) as client:
        prices = client.pimlico_get_user_operation_gas_price()

    for tier in (prices.slow, prices.standard, prices.fast):
        assert tier.max_fee_per_gas.startswith("0x")
        assert tier.max_priority_fee_per_gas.startswith("0x")
        # Must be parseable as a non-negative integer.
        assert int(tier.max_fee_per_gas, 16) >= 0


@requires_key
def test_live_status_of_unknown_hash_is_not_found():
    unknown = "0x" + "00" * 32
    with PimlicoClient(api_key=_api_key(), chain=CHAIN) as client:
        status = client.pimlico_get_user_operation_status(unknown)

    assert status.status == "not_found"


@requires_key
async def test_live_async_gas_price():
    async with AsyncPimlicoClient(api_key=_api_key(), chain=CHAIN) as client:
        prices = await client.pimlico_get_user_operation_gas_price()

    assert prices.standard.max_fee_per_gas.startswith("0x")
