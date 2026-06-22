"""pimlico-py: a typed Python client for the Pimlico ERC-4337 API.

Exposes synchronous (:class:`PimlicoClient`) and asynchronous
(:class:`AsyncPimlicoClient`) clients for Pimlico's bundler, paymaster, and gas
estimation JSON-RPC methods, plus the pydantic models and exception types.
"""

from pimlico.client import AsyncPimlicoClient, PimlicoClient
from pimlico.exceptions import (
    PimlicoError,
    PimlicoHTTPError,
    PimlicoRPCError,
    PimlicoTimeoutError,
)
from pimlico.models import (
    ENTRYPOINT_V06,
    ENTRYPOINT_V07,
    GasPriceResult,
    GasPriceTier,
    PaymasterData,
    PaymasterStubData,
    Sponsor,
    SponsorUserOperationResult,
    TransactionReceipt,
    UserOperationByHash,
    UserOperationGasEstimate,
    UserOperationReceipt,
    UserOperationStatus,
    UserOperationV07,
)

__version__ = "0.1.0"

__all__ = [
    "ENTRYPOINT_V06",
    "ENTRYPOINT_V07",
    "AsyncPimlicoClient",
    "GasPriceResult",
    "GasPriceTier",
    "PaymasterData",
    "PaymasterStubData",
    "PimlicoClient",
    "PimlicoError",
    "PimlicoHTTPError",
    "PimlicoRPCError",
    "PimlicoTimeoutError",
    "Sponsor",
    "SponsorUserOperationResult",
    "TransactionReceipt",
    "UserOperationByHash",
    "UserOperationGasEstimate",
    "UserOperationReceipt",
    "UserOperationStatus",
    "UserOperationV07",
    "__version__",
]
