"""Tests for the JSON-RPC transport layer (sync and async)."""

import httpx
import pytest
import respx

from pimlico.exceptions import PimlicoHTTPError, PimlicoRPCError
from pimlico.transport import AsyncJsonRpcTransport, JsonRpcTransport

URL = "https://api.pimlico.io/v2/11155111/rpc"


@respx.mock
def test_request_returns_result_member():
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": "0xdeadbeef"})
    )
    transport = JsonRpcTransport(URL)

    result = transport.request("eth_sendUserOperation", ["0x", "0xep"])

    assert result == "0xdeadbeef"
    transport.close()


@respx.mock
def test_request_sends_correct_envelope():
    route = respx.post(URL).mock(
        return_value=httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": []})
    )
    transport = JsonRpcTransport(URL)

    transport.request("eth_supportedEntryPoints", [])

    sent = route.calls.last.request
    import json

    body = json.loads(sent.content)
    assert body["jsonrpc"] == "2.0"
    assert body["method"] == "eth_supportedEntryPoints"
    assert body["params"] == []
    assert "id" in body
    transport.close()


@respx.mock
def test_rpc_error_envelope_raises_pimlico_rpc_error():
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32602, "message": "Invalid params", "data": {"x": 1}},
            },
        )
    )
    transport = JsonRpcTransport(URL)

    with pytest.raises(PimlicoRPCError) as exc_info:
        transport.request("eth_sendUserOperation", ["0x"])

    assert exc_info.value.code == -32602
    assert exc_info.value.message == "Invalid params"
    assert exc_info.value.data == {"x": 1}
    transport.close()


@respx.mock
def test_non_2xx_raises_pimlico_http_error():
    respx.post(URL).mock(return_value=httpx.Response(429, text="rate limited"))
    transport = JsonRpcTransport(URL)

    with pytest.raises(PimlicoHTTPError) as exc_info:
        transport.request("eth_supportedEntryPoints", [])

    assert exc_info.value.status_code == 429
    transport.close()


@respx.mock
def test_request_allows_result_to_be_none():
    # A null result (e.g. receipt not yet available) is valid, not an error.
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": None})
    )
    transport = JsonRpcTransport(URL)

    result = transport.request("eth_getUserOperationReceipt", ["0xhash"])

    assert result is None
    transport.close()


@respx.mock
async def test_async_request_returns_result_member():
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": "0xok"})
    )
    transport = AsyncJsonRpcTransport(URL)

    result = await transport.request("eth_sendUserOperation", ["0x"])

    assert result == "0xok"
    await transport.aclose()


@respx.mock
async def test_async_rpc_error_raises():
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "boom"}},
        )
    )
    transport = AsyncJsonRpcTransport(URL)

    with pytest.raises(PimlicoRPCError) as exc_info:
        await transport.request("eth_sendUserOperation", ["0x"])

    assert exc_info.value.code == -32000
    await transport.aclose()
