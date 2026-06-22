"""Tests for the asynchronous AsyncPimlicoClient."""

import httpx
import pytest
import respx

from pimlico import AsyncPimlicoClient
from pimlico.exceptions import PimlicoTimeoutError
from pimlico.models import ENTRYPOINT_V07, UserOperationV07


def _user_op() -> UserOperationV07:
    return UserOperationV07(
        sender="0xabc",
        nonce="0x0",
        call_data="0xdead",
        call_gas_limit="0x1",
        verification_gas_limit="0x2",
        pre_verification_gas="0x3",
        max_fee_per_gas="0x4",
        max_priority_fee_per_gas="0x5",
        signature="0xbeef",
    )


def _rpc(result):
    return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result})


def test_default_url_built():
    client = AsyncPimlicoClient(api_key="k", chain=8453)
    assert client.url == "https://api.pimlico.io/v2/8453/rpc?apikey=k"


@respx.mock
async def test_async_send_user_operation():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc("0xhash"))
    client = AsyncPimlicoClient(api_key="k", chain=11155111)

    result = await client.eth_send_user_operation(_user_op())

    assert result == "0xhash"
    await client.aclose()


@respx.mock
async def test_async_gas_price():
    payload = {
        "slow": {"maxFeePerGas": "0x1", "maxPriorityFeePerGas": "0x1"},
        "standard": {"maxFeePerGas": "0x2", "maxPriorityFeePerGas": "0x2"},
        "fast": {"maxFeePerGas": "0x3", "maxPriorityFeePerGas": "0x3"},
    }
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = AsyncPimlicoClient(api_key="k", chain=11155111)

    prices = await client.pimlico_get_user_operation_gas_price()

    assert prices.standard.max_fee_per_gas == "0x2"
    await client.aclose()


@respx.mock
async def test_async_receipt_none_then_present():
    responses = [_rpc(None), _rpc({"userOpHash": "0xh", "success": True, "receipt": {}})]
    respx.route(host="api.pimlico.io").mock(side_effect=responses)
    client = AsyncPimlicoClient(api_key="k", chain=11155111)

    receipt = await client.wait_for_user_operation_receipt("0xh", timeout=5.0, poll_interval=0.0)

    assert receipt.success is True
    await client.aclose()


@respx.mock
async def test_async_wait_for_receipt_timeout():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(None))
    client = AsyncPimlicoClient(api_key="k", chain=11155111)

    with pytest.raises(PimlicoTimeoutError):
        await client.wait_for_user_operation_receipt("0xh", timeout=0.0, poll_interval=0.0)
    await client.aclose()


@respx.mock
async def test_async_context_manager_closes():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc([ENTRYPOINT_V07]))

    async with AsyncPimlicoClient(api_key="k", chain=11155111) as client:
        result = await client.eth_supported_entry_points()

    assert result == [ENTRYPOINT_V07]
