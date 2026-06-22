"""Tests for the synchronous PimlicoClient."""

import json

import httpx
import pytest
import respx

from pimlico import PimlicoClient
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


def test_default_base_url_includes_chain_and_apikey():
    client = PimlicoClient(api_key="pim_secret", chain=11155111)

    assert client.url == "https://api.pimlico.io/v2/11155111/rpc?apikey=pim_secret"
    client.close()


def test_custom_base_url_is_used_verbatim():
    client = PimlicoClient(
        api_key="pim_secret",
        chain=1,
        base_url="https://my-bundler.example.com/rpc",
    )

    assert client.url == "https://my-bundler.example.com/rpc"
    client.close()


@respx.mock
def test_eth_supported_entry_points():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc([ENTRYPOINT_V07]))
    client = PimlicoClient(api_key="k", chain=11155111)

    result = client.eth_supported_entry_points()

    assert result == [ENTRYPOINT_V07]
    client.close()


@respx.mock
def test_gas_price_returns_parsed_model():
    payload = {
        "slow": {"maxFeePerGas": "0x1", "maxPriorityFeePerGas": "0x1"},
        "standard": {"maxFeePerGas": "0x2", "maxPriorityFeePerGas": "0x2"},
        "fast": {"maxFeePerGas": "0x3", "maxPriorityFeePerGas": "0x3"},
    }
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    prices = client.pimlico_get_user_operation_gas_price()

    assert prices.fast.max_fee_per_gas == "0x3"
    client.close()


@respx.mock
def test_send_user_operation_passes_op_and_default_entrypoint():
    route = respx.route(host="api.pimlico.io").mock(return_value=_rpc("0xuserophash"))
    client = PimlicoClient(api_key="k", chain=11155111)

    result = client.eth_send_user_operation(_user_op())

    assert result == "0xuserophash"
    body = json.loads(route.calls.last.request.content)
    assert body["method"] == "eth_sendUserOperation"
    assert body["params"][0]["sender"] == "0xabc"
    assert body["params"][0]["callData"] == "0xdead"
    # Default entryPoint is v0.7.
    assert body["params"][1] == ENTRYPOINT_V07
    client.close()


@respx.mock
def test_send_user_operation_honours_custom_entrypoint():
    route = respx.route(host="api.pimlico.io").mock(return_value=_rpc("0xh"))
    client = PimlicoClient(api_key="k", chain=11155111)

    client.eth_send_user_operation(_user_op(), entry_point="0xcustomEP")

    body = json.loads(route.calls.last.request.content)
    assert body["params"][1] == "0xcustomEP"
    client.close()


@respx.mock
def test_estimate_gas_returns_parsed_model():
    payload = {
        "preVerificationGas": "0xd3e3",
        "verificationGasLimit": "0x60b01",
        "callGasLimit": "0x13880",
    }
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    est = client.eth_estimate_user_operation_gas(_user_op())

    assert est.call_gas_limit == "0x13880"
    client.close()


@respx.mock
def test_get_receipt_returns_none_when_null():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(None))
    client = PimlicoClient(api_key="k", chain=11155111)

    assert client.eth_get_user_operation_receipt("0xhash") is None
    client.close()


@respx.mock
def test_get_receipt_parses_model():
    payload = {
        "userOpHash": "0xa5a5",
        "success": True,
        "actualGasUsed": "0x1",
        "receipt": {"transactionHash": "0xtx", "status": "0x1"},
    }
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    receipt = client.eth_get_user_operation_receipt("0xa5a5")

    assert receipt is not None
    assert receipt.success is True
    client.close()


@respx.mock
def test_get_user_operation_by_hash_returns_none_when_null():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(None))
    client = PimlicoClient(api_key="k", chain=11155111)

    assert client.eth_get_user_operation_by_hash("0xhash") is None
    client.close()


@respx.mock
def test_status_returns_parsed_model():
    respx.route(host="api.pimlico.io").mock(
        return_value=_rpc({"status": "included", "transactionHash": "0xtx"})
    )
    client = PimlicoClient(api_key="k", chain=11155111)

    status = client.pimlico_get_user_operation_status("0xhash")

    assert status.status == "included"
    assert status.transaction_hash == "0xtx"
    client.close()


@respx.mock
def test_sponsor_user_operation_parses_result():
    payload = {
        "paymaster": "0xpm",
        "paymasterData": "0xdata",
        "paymasterVerificationGasLimit": "0x1",
        "paymasterPostOpGasLimit": "0x2",
    }
    route = respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    result = client.pm_sponsor_user_operation(_user_op())

    assert result.paymaster == "0xpm"
    body = json.loads(route.calls.last.request.content)
    assert body["method"] == "pm_sponsorUserOperation"
    assert body["params"][1] == ENTRYPOINT_V07
    client.close()


@respx.mock
def test_get_paymaster_stub_data_sends_hex_chain_id():
    payload = {"paymaster": "0xpm", "paymasterData": "0xdata"}
    route = respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    client.pm_get_paymaster_stub_data(_user_op())

    body = json.loads(route.calls.last.request.content)
    assert body["method"] == "pm_getPaymasterStubData"
    # ERC-7677: chainId is the third param, hex-encoded.
    assert body["params"][2] == hex(11155111)
    client.close()


@respx.mock
def test_get_paymaster_data_parses_result():
    payload = {"paymaster": "0xpm", "paymasterData": "0xfinal"}
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(payload))
    client = PimlicoClient(api_key="k", chain=11155111)

    result = client.pm_get_paymaster_data(_user_op())

    assert result.paymaster_data == "0xfinal"
    client.close()


@respx.mock
def test_wait_for_receipt_polls_until_available():
    responses = [
        _rpc(None),
        _rpc(None),
        _rpc({"userOpHash": "0xh", "success": True, "receipt": {}}),
    ]
    respx.route(host="api.pimlico.io").mock(side_effect=responses)
    client = PimlicoClient(api_key="k", chain=11155111)

    receipt = client.wait_for_user_operation_receipt("0xh", timeout=5.0, poll_interval=0.0)

    assert receipt.success is True
    client.close()


@respx.mock
def test_wait_for_receipt_raises_timeout():
    respx.route(host="api.pimlico.io").mock(return_value=_rpc(None))
    client = PimlicoClient(api_key="k", chain=11155111)

    with pytest.raises(PimlicoTimeoutError):
        client.wait_for_user_operation_receipt("0xh", timeout=0.0, poll_interval=0.0)
    client.close()


def test_client_is_context_manager():
    with PimlicoClient(api_key="k", chain=1) as client:
        assert client.url.endswith("apikey=k")
