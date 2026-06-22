"""JSON-RPC transport over ``httpx``.

This module owns the wire protocol: it builds the JSON-RPC 2.0 envelope, sends
it to the configured endpoint, and unwraps the response — returning the
``result`` member or raising :class:`PimlicoRPCError` when the server returns an
``error`` member. Non-success HTTP status codes raise :class:`PimlicoHTTPError`.

Two transports are provided: :class:`JsonRpcTransport` (synchronous) and
:class:`AsyncJsonRpcTransport` (asynchronous). Both share the envelope-building
and response-unwrapping logic.
"""

import itertools
from typing import Any, Dict, List, Optional

import httpx

from pimlico.exceptions import PimlicoHTTPError, PimlicoRPCError

DEFAULT_TIMEOUT = 30.0


def _build_payload(method: str, params: List[Any], request_id: int) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 request envelope."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }


def _unwrap_response(response: httpx.Response) -> Any:
    """Validate an HTTP response and return the JSON-RPC ``result``.

    Raises:
        PimlicoHTTPError: If the HTTP status code is not 2xx.
        PimlicoRPCError: If the JSON-RPC envelope contains an ``error`` member.
    """
    if response.status_code >= 400:
        raise PimlicoHTTPError(status_code=response.status_code, message=response.text)

    body = response.json()
    error = body.get("error")
    if error is not None:
        raise PimlicoRPCError(
            code=error.get("code", 0),
            message=error.get("message", ""),
            data=error.get("data"),
        )
    return body.get("result")


class JsonRpcTransport:
    """Synchronous JSON-RPC transport backed by an :class:`httpx.Client`.

    Args:
        url: The fully-qualified RPC endpoint (including any API-key query
            parameter).
        timeout: Per-request timeout in seconds.
        client: An optional pre-configured ``httpx.Client``. When omitted, the
            transport creates and owns one.
    """

    def __init__(
        self,
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._url = url
        self._ids = itertools.count(1)
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def request(self, method: str, params: List[Any]) -> Any:
        """Send a single JSON-RPC request and return its ``result``.

        Args:
            method: The JSON-RPC method name.
            params: The positional parameter list.

        Returns:
            The decoded ``result`` member (may be ``None`` for a null result).
        """
        payload = _build_payload(method, params, next(self._ids))
        response = self._client.post(self._url, json=payload)
        return _unwrap_response(response)

    def close(self) -> None:
        """Close the underlying HTTP client if this transport owns it."""
        if self._owns_client:
            self._client.close()


class AsyncJsonRpcTransport:
    """Asynchronous JSON-RPC transport backed by an :class:`httpx.AsyncClient`.

    Args:
        url: The fully-qualified RPC endpoint (including any API-key query
            parameter).
        timeout: Per-request timeout in seconds.
        client: An optional pre-configured ``httpx.AsyncClient``. When omitted,
            the transport creates and owns one.
    """

    def __init__(
        self,
        url: str,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._url = url
        self._ids = itertools.count(1)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def request(self, method: str, params: List[Any]) -> Any:
        """Send a single JSON-RPC request and return its ``result``.

        Args:
            method: The JSON-RPC method name.
            params: The positional parameter list.

        Returns:
            The decoded ``result`` member (may be ``None`` for a null result).
        """
        payload = _build_payload(method, params, next(self._ids))
        response = await self._client.post(self._url, json=payload)
        return _unwrap_response(response)

    async def aclose(self) -> None:
        """Close the underlying HTTP client if this transport owns it."""
        if self._owns_client:
            await self._client.aclose()
