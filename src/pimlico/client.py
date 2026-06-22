"""High-level Pimlico clients (synchronous and asynchronous).

:class:`PimlicoClient` and :class:`AsyncPimlicoClient` expose one Python method
per JSON-RPC method, parse responses into the models in :mod:`pimlico.models`,
and provide a poll-for-receipt helper. They build the default Pimlico endpoint
URL from a chain ID and API key, or accept a custom ``base_url``.

Both clients target **EntryPoint v0.7** by default; pass ``entry_point`` to any
method that accepts it to override the contract used.
"""

import asyncio
import time
from types import TracebackType
from typing import Any, List, Optional, Type
from urllib.parse import quote

import httpx

from pimlico.exceptions import PimlicoTimeoutError
from pimlico.models import (
    ENTRYPOINT_V07,
    GasPriceResult,
    PaymasterData,
    PaymasterStubData,
    SponsorUserOperationResult,
    UserOperationByHash,
    UserOperationGasEstimate,
    UserOperationReceipt,
    UserOperationStatus,
    UserOperationV07,
)
from pimlico.transport import (
    DEFAULT_TIMEOUT,
    AsyncJsonRpcTransport,
    JsonRpcTransport,
)

DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_RECEIPT_TIMEOUT = 60.0


def _build_url(api_key: str, chain: int, base_url: Optional[str]) -> str:
    """Build the RPC endpoint URL.

    When ``base_url`` is given it is used verbatim (the caller is responsible
    for any authentication it needs). Otherwise the standard Pimlico endpoint is
    constructed: ``https://api.pimlico.io/v2/{chain}/rpc?apikey={api_key}``.
    """
    if base_url is not None:
        return base_url
    return f"https://api.pimlico.io/v2/{chain}/rpc?apikey={quote(api_key, safe='')}"


class PimlicoClient:
    """Synchronous client for the Pimlico ERC-4337 API.

    Args:
        api_key: Your Pimlico API key. Sent as the ``apikey`` query parameter on
            the default endpoint.
        chain: The numeric chain ID (for example ``11155111`` for Sepolia). Used
            to build the default endpoint URL and as the ``chainId`` argument to
            ERC-7677 paymaster methods.
        base_url: Optional fully-qualified RPC URL that overrides the default
            Pimlico endpoint (for self-hosted bundlers or proxies).
        timeout: Per-request HTTP timeout in seconds.
        client: Optional pre-configured :class:`httpx.Client`.

    Example:
        >>> client = PimlicoClient(api_key="pim_xxx", chain=11155111)
        >>> prices = client.pimlico_get_user_operation_gas_price()
        >>> client.close()
    """

    def __init__(
        self,
        api_key: str,
        chain: int,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.api_key = api_key
        self.chain = chain
        self.url = _build_url(api_key, chain, base_url)
        self._transport = JsonRpcTransport(self.url, timeout=timeout, client=client)

    # -- Bundler methods ---------------------------------------------------

    def eth_supported_entry_points(self) -> List[str]:
        """Return the EntryPoint contract addresses this bundler supports."""
        result = self._transport.request("eth_supportedEntryPoints", [])
        return list(result)

    def pimlico_get_user_operation_gas_price(self) -> GasPriceResult:
        """Return current ``slow``/``standard``/``fast`` user-operation gas prices."""
        result = self._transport.request("pimlico_getUserOperationGasPrice", [])
        return GasPriceResult.model_validate(result)

    def eth_estimate_user_operation_gas(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
    ) -> UserOperationGasEstimate:
        """Estimate the gas limits required for ``user_operation``.

        Args:
            user_operation: The operation to estimate (gas-limit fields may be
                zero/placeholder).
            entry_point: The EntryPoint contract address (defaults to v0.7).
        """
        result = self._transport.request(
            "eth_estimateUserOperationGas",
            [user_operation.to_rpc(), entry_point],
        )
        return UserOperationGasEstimate.model_validate(result)

    def eth_send_user_operation(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
    ) -> str:
        """Submit ``user_operation`` to the bundler and return its hash.

        Args:
            user_operation: The fully-populated, signed operation.
            entry_point: The EntryPoint contract address (defaults to v0.7).

        Returns:
            The user-operation hash, used to poll for status and receipt.
        """
        result = self._transport.request(
            "eth_sendUserOperation",
            [user_operation.to_rpc(), entry_point],
        )
        return str(result)

    def eth_get_user_operation_receipt(self, user_op_hash: str) -> Optional[UserOperationReceipt]:
        """Return the receipt for ``user_op_hash``, or ``None`` if not yet mined."""
        result = self._transport.request("eth_getUserOperationReceipt", [user_op_hash])
        if result is None:
            return None
        return UserOperationReceipt.model_validate(result)

    def eth_get_user_operation_by_hash(self, user_op_hash: str) -> Optional[UserOperationByHash]:
        """Return the operation for ``user_op_hash``, or ``None`` if unknown."""
        result = self._transport.request("eth_getUserOperationByHash", [user_op_hash])
        if result is None:
            return None
        return UserOperationByHash.model_validate(result)

    def pimlico_get_user_operation_status(self, user_op_hash: str) -> UserOperationStatus:
        """Return the lifecycle status of ``user_op_hash``."""
        result = self._transport.request("pimlico_getUserOperationStatus", [user_op_hash])
        return UserOperationStatus.model_validate(result)

    # -- Paymaster methods -------------------------------------------------

    def pm_sponsor_user_operation(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> SponsorUserOperationResult:
        """Request paymaster sponsorship for ``user_operation``.

        Args:
            user_operation: The operation to sponsor.
            entry_point: The EntryPoint contract address (defaults to v0.7).
            context: Optional sponsorship context object passed to the paymaster.
        """
        params: List[Any] = [user_operation.to_rpc(), entry_point]
        if context is not None:
            params.append(context)
        result = self._transport.request("pm_sponsorUserOperation", params)
        return SponsorUserOperationResult.model_validate(result)

    def pm_get_paymaster_stub_data(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> PaymasterStubData:
        """Return ERC-7677 paymaster *stub* data for gas estimation.

        Args:
            user_operation: The operation to sponsor.
            entry_point: The EntryPoint contract address (defaults to v0.7).
            context: Optional sponsorship context object.

        Note:
            Per ERC-7677 the chain ID is passed as a hex-encoded string as the
            third positional parameter.
        """
        params: List[Any] = [user_operation.to_rpc(), entry_point, hex(self.chain)]
        params.append(context)
        result = self._transport.request("pm_getPaymasterStubData", params)
        return PaymasterStubData.model_validate(result)

    def pm_get_paymaster_data(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> PaymasterData:
        """Return ERC-7677 final, signed paymaster data.

        Args:
            user_operation: The operation to sponsor.
            entry_point: The EntryPoint contract address (defaults to v0.7).
            context: Optional sponsorship context object.
        """
        params: List[Any] = [user_operation.to_rpc(), entry_point, hex(self.chain)]
        params.append(context)
        result = self._transport.request("pm_getPaymasterData", params)
        return PaymasterData.model_validate(result)

    # -- Helpers -----------------------------------------------------------

    def wait_for_user_operation_receipt(
        self,
        user_op_hash: str,
        timeout: float = DEFAULT_RECEIPT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> UserOperationReceipt:
        """Poll ``eth_getUserOperationReceipt`` until a receipt is available.

        Args:
            user_op_hash: The hash returned by :meth:`eth_send_user_operation`.
            timeout: Maximum seconds to wait before giving up.
            poll_interval: Seconds to sleep between polls.

        Returns:
            The user-operation receipt once the operation is mined.

        Raises:
            PimlicoTimeoutError: If no receipt appears within ``timeout``.
        """
        deadline = time.monotonic() + timeout
        while True:
            receipt = self.eth_get_user_operation_receipt(user_op_hash)
            if receipt is not None:
                return receipt
            if time.monotonic() >= deadline:
                raise PimlicoTimeoutError(
                    f"No receipt for user operation {user_op_hash} after {timeout}s"
                )
            time.sleep(poll_interval)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._transport.close()

    def __enter__(self) -> "PimlicoClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()


class AsyncPimlicoClient:
    """Asynchronous client for the Pimlico ERC-4337 API.

    The async counterpart of :class:`PimlicoClient`; every RPC method is a
    coroutine. See :class:`PimlicoClient` for argument documentation.

    Example:
        >>> async with AsyncPimlicoClient(api_key="pim_xxx", chain=11155111) as c:
        ...     prices = await c.pimlico_get_user_operation_gas_price()
    """

    def __init__(
        self,
        api_key: str,
        chain: int,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key
        self.chain = chain
        self.url = _build_url(api_key, chain, base_url)
        self._transport = AsyncJsonRpcTransport(self.url, timeout=timeout, client=client)

    # -- Bundler methods ---------------------------------------------------

    async def eth_supported_entry_points(self) -> List[str]:
        """Return the EntryPoint contract addresses this bundler supports."""
        result = await self._transport.request("eth_supportedEntryPoints", [])
        return list(result)

    async def pimlico_get_user_operation_gas_price(self) -> GasPriceResult:
        """Return current ``slow``/``standard``/``fast`` user-operation gas prices."""
        result = await self._transport.request("pimlico_getUserOperationGasPrice", [])
        return GasPriceResult.model_validate(result)

    async def eth_estimate_user_operation_gas(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
    ) -> UserOperationGasEstimate:
        """Estimate the gas limits required for ``user_operation``."""
        result = await self._transport.request(
            "eth_estimateUserOperationGas",
            [user_operation.to_rpc(), entry_point],
        )
        return UserOperationGasEstimate.model_validate(result)

    async def eth_send_user_operation(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
    ) -> str:
        """Submit ``user_operation`` to the bundler and return its hash."""
        result = await self._transport.request(
            "eth_sendUserOperation",
            [user_operation.to_rpc(), entry_point],
        )
        return str(result)

    async def eth_get_user_operation_receipt(
        self, user_op_hash: str
    ) -> Optional[UserOperationReceipt]:
        """Return the receipt for ``user_op_hash``, or ``None`` if not yet mined."""
        result = await self._transport.request("eth_getUserOperationReceipt", [user_op_hash])
        if result is None:
            return None
        return UserOperationReceipt.model_validate(result)

    async def eth_get_user_operation_by_hash(
        self, user_op_hash: str
    ) -> Optional[UserOperationByHash]:
        """Return the operation for ``user_op_hash``, or ``None`` if unknown."""
        result = await self._transport.request("eth_getUserOperationByHash", [user_op_hash])
        if result is None:
            return None
        return UserOperationByHash.model_validate(result)

    async def pimlico_get_user_operation_status(self, user_op_hash: str) -> UserOperationStatus:
        """Return the lifecycle status of ``user_op_hash``."""
        result = await self._transport.request("pimlico_getUserOperationStatus", [user_op_hash])
        return UserOperationStatus.model_validate(result)

    # -- Paymaster methods -------------------------------------------------

    async def pm_sponsor_user_operation(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> SponsorUserOperationResult:
        """Request paymaster sponsorship for ``user_operation``."""
        params: List[Any] = [user_operation.to_rpc(), entry_point]
        if context is not None:
            params.append(context)
        result = await self._transport.request("pm_sponsorUserOperation", params)
        return SponsorUserOperationResult.model_validate(result)

    async def pm_get_paymaster_stub_data(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> PaymasterStubData:
        """Return ERC-7677 paymaster *stub* data for gas estimation."""
        params: List[Any] = [user_operation.to_rpc(), entry_point, hex(self.chain)]
        params.append(context)
        result = await self._transport.request("pm_getPaymasterStubData", params)
        return PaymasterStubData.model_validate(result)

    async def pm_get_paymaster_data(
        self,
        user_operation: UserOperationV07,
        entry_point: str = ENTRYPOINT_V07,
        context: Optional[Any] = None,
    ) -> PaymasterData:
        """Return ERC-7677 final, signed paymaster data."""
        params: List[Any] = [user_operation.to_rpc(), entry_point, hex(self.chain)]
        params.append(context)
        result = await self._transport.request("pm_getPaymasterData", params)
        return PaymasterData.model_validate(result)

    # -- Helpers -----------------------------------------------------------

    async def wait_for_user_operation_receipt(
        self,
        user_op_hash: str,
        timeout: float = DEFAULT_RECEIPT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> UserOperationReceipt:
        """Poll ``eth_getUserOperationReceipt`` until a receipt is available.

        Raises:
            PimlicoTimeoutError: If no receipt appears within ``timeout``.
        """
        deadline = time.monotonic() + timeout
        while True:
            receipt = await self.eth_get_user_operation_receipt(user_op_hash)
            if receipt is not None:
                return receipt
            if time.monotonic() >= deadline:
                raise PimlicoTimeoutError(
                    f"No receipt for user operation {user_op_hash} after {timeout}s"
                )
            await asyncio.sleep(poll_interval)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncPimlicoClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()
