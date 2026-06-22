"""Pydantic models for Pimlico user operations and JSON-RPC responses.

All on-chain numeric values in ERC-4337 JSON-RPC are encoded as ``0x``-prefixed
hexadecimal strings, so the models carry them as ``str``. Field names follow
Python's snake_case convention while serialising/parsing the camelCase shapes
the API uses, via pydantic aliases.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Canonical EntryPoint contract addresses (identical across all chains).
ENTRYPOINT_V06 = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
ENTRYPOINT_V07 = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"


class _CamelModel(BaseModel):
    """Base model that maps snake_case fields to camelCase JSON keys."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class UserOperationV07(_CamelModel):
    """An ERC-4337 **EntryPoint v0.7** user operation.

    v0.7 uses the *unpacked* representation: the account-deployment fields are
    split into ``factory``/``factory_data`` and the paymaster fields into
    ``paymaster``/``paymaster_data`` and their dedicated gas limits, rather than
    the packed ``initCode``/``paymasterAndData`` byte strings of v0.6.

    All gas and fee fields are ``0x``-prefixed hex strings.

    Args:
        sender: The account contract address sending the operation.
        nonce: The account nonce, hex-encoded.
        call_data: The calldata to execute from the sender account.
        call_gas_limit: Gas allocated to the main execution call.
        verification_gas_limit: Gas allocated to account verification.
        pre_verification_gas: Gas to compensate the bundler for pre-verification
            overhead and calldata costs.
        max_fee_per_gas: EIP-1559 max fee per gas.
        max_priority_fee_per_gas: EIP-1559 max priority fee per gas.
        signature: The account signature over the operation.
        factory: Optional account-factory address (for first deployment).
        factory_data: Optional calldata passed to the factory.
        paymaster: Optional paymaster contract address.
        paymaster_verification_gas_limit: Optional paymaster verification gas.
        paymaster_post_op_gas_limit: Optional paymaster post-op gas.
        paymaster_data: Optional calldata passed to the paymaster.
    """

    sender: str
    nonce: str
    call_data: str
    call_gas_limit: str
    verification_gas_limit: str
    pre_verification_gas: str
    max_fee_per_gas: str
    max_priority_fee_per_gas: str
    signature: str

    factory: Optional[str] = None
    factory_data: Optional[str] = None
    paymaster: Optional[str] = None
    paymaster_verification_gas_limit: Optional[str] = None
    paymaster_post_op_gas_limit: Optional[str] = None
    paymaster_data: Optional[str] = None

    def to_rpc(self) -> Dict[str, Any]:
        """Serialise to the camelCase dict the JSON-RPC API expects.

        Optional fields that were never set are omitted entirely so the bundler
        receives a clean operation object.
        """
        return self.model_dump(by_alias=True, exclude_none=True)


class GasPriceTier(_CamelModel):
    """A single gas-price tier returned by ``pimlico_getUserOperationGasPrice``.

    Args:
        max_fee_per_gas: EIP-1559 max fee per gas for this tier (hex).
        max_priority_fee_per_gas: EIP-1559 max priority fee per gas (hex).
    """

    max_fee_per_gas: str
    max_priority_fee_per_gas: str


class GasPriceResult(_CamelModel):
    """The three speed/cost tiers from ``pimlico_getUserOperationGasPrice``.

    Args:
        slow: The cheapest, slowest-to-include tier.
        standard: The balanced default tier.
        fast: The most expensive, fastest-to-include tier.
    """

    slow: GasPriceTier
    standard: GasPriceTier
    fast: GasPriceTier


class UserOperationGasEstimate(_CamelModel):
    """Result of ``eth_estimateUserOperationGas`` for EntryPoint v0.7.

    Args:
        pre_verification_gas: Estimated pre-verification gas (hex).
        verification_gas_limit: Estimated verification gas limit (hex).
        call_gas_limit: Estimated call gas limit (hex).
        paymaster_verification_gas_limit: Estimated paymaster verification gas
            (hex); present only when a paymaster is involved.
        paymaster_post_op_gas_limit: Estimated paymaster post-op gas (hex);
            present only when a paymaster is involved.
    """

    pre_verification_gas: str
    verification_gas_limit: str
    call_gas_limit: str
    paymaster_verification_gas_limit: Optional[str] = None
    paymaster_post_op_gas_limit: Optional[str] = None


class UserOperationStatus(_CamelModel):
    """Result of ``pimlico_getUserOperationStatus``.

    The ``status`` is one of: ``not_found``, ``not_submitted``, ``submitted``,
    ``rejected``, ``included``, ``failed`` or ``queued``. Status is retained by
    the bundler for one hour, after which queries return ``not_found``.

    Args:
        status: The current lifecycle status string.
        transaction_hash: The bundle transaction hash, present only when the
            operation has been ``submitted``, ``included`` or ``failed``.
    """

    status: str
    transaction_hash: Optional[str] = None


class TransactionReceipt(_CamelModel):
    """The on-chain transaction receipt nested inside a user-op receipt.

    Only the commonly used fields are typed explicitly; any additional fields
    the node returns are preserved.

    Args:
        transaction_hash: Hash of the bundle transaction.
        transaction_index: Index of the transaction within its block (hex).
        block_hash: Hash of the including block.
        block_number: Number of the including block (hex).
        from_address: Sender of the bundle transaction (the bundler EOA).
        to_address: Recipient of the bundle transaction (the EntryPoint).
        cumulative_gas_used: Cumulative gas used in the block up to this tx (hex).
        gas_used: Gas used by this transaction (hex).
        status: On-chain execution status, ``0x1`` success or ``0x0`` revert.
        effective_gas_price: Effective gas price paid (hex).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    transaction_hash: Optional[str] = None
    transaction_index: Optional[str] = None
    block_hash: Optional[str] = None
    block_number: Optional[str] = None
    from_address: Optional[str] = Field(default=None, alias="from")
    to_address: Optional[str] = Field(default=None, alias="to")
    cumulative_gas_used: Optional[str] = None
    gas_used: Optional[str] = None
    status: Optional[str] = None
    effective_gas_price: Optional[str] = None


class UserOperationReceipt(_CamelModel):
    """Result of ``eth_getUserOperationReceipt``.

    Args:
        user_op_hash: The hash of the user operation.
        entry_point: The EntryPoint contract that processed the operation.
        sender: The account that sent the operation.
        nonce: The operation nonce (hex).
        actual_gas_used: Total gas used by the operation (hex).
        actual_gas_cost: Total wei cost paid for the operation (hex).
        success: Whether the operation's execution phase succeeded.
        logs: Event logs emitted during the operation.
        receipt: The underlying on-chain transaction receipt.
    """

    user_op_hash: str
    entry_point: Optional[str] = None
    sender: Optional[str] = None
    nonce: Optional[str] = None
    actual_gas_used: Optional[str] = None
    actual_gas_cost: Optional[str] = None
    success: bool
    logs: List[Any] = Field(default_factory=list)
    receipt: TransactionReceipt


class UserOperationByHash(_CamelModel):
    """Result of ``eth_getUserOperationByHash``.

    Args:
        user_operation: The full user operation as it was submitted.
        entry_point: The EntryPoint contract that processed the operation.
        block_number: The block the operation was included in (hex), if mined.
        block_hash: The hash of the including block, if mined.
        transaction_hash: The bundle transaction hash, if mined.
    """

    user_operation: UserOperationV07
    entry_point: Optional[str] = None
    block_number: Optional[str] = None
    block_hash: Optional[str] = None
    transaction_hash: Optional[str] = None


class Sponsor(_CamelModel):
    """Sponsor metadata returned by paymaster methods (ERC-7677).

    Args:
        name: Human-readable sponsor name, for display in wallets.
        icon: Optional data-URI icon for the sponsor.
    """

    name: str
    icon: Optional[str] = None


class PaymasterStubData(_CamelModel):
    """Result of ``pm_getPaymasterStubData`` for EntryPoint v0.7 (ERC-7677).

    Stub data is gas-estimation-only placeholder data used before the final,
    signed paymaster data is requested via ``pm_getPaymasterData``.

    Args:
        paymaster: The paymaster contract address.
        paymaster_data: Placeholder paymaster calldata (hex).
        paymaster_verification_gas_limit: Suggested paymaster verification gas.
        paymaster_post_op_gas_limit: Suggested paymaster post-op gas.
        sponsor: Optional sponsor metadata for wallet display.
        is_final: When ``True``, this stub data is also valid as final data and
            a separate ``pm_getPaymasterData`` call is unnecessary.
    """

    paymaster: str
    paymaster_data: str
    paymaster_verification_gas_limit: Optional[str] = None
    paymaster_post_op_gas_limit: Optional[str] = None
    sponsor: Optional[Sponsor] = None
    is_final: Optional[bool] = None


class PaymasterData(_CamelModel):
    """Result of ``pm_getPaymasterData`` for EntryPoint v0.7 (ERC-7677).

    Args:
        paymaster: The paymaster contract address.
        paymaster_data: The final, signed paymaster calldata (hex).
    """

    paymaster: str
    paymaster_data: str


class SponsorUserOperationResult(_CamelModel):
    """Result of ``pm_sponsorUserOperation`` for EntryPoint v0.7.

    Args:
        paymaster: The paymaster contract address.
        paymaster_data: The signed paymaster calldata (hex).
        paymaster_verification_gas_limit: Paymaster verification gas (hex).
        paymaster_post_op_gas_limit: Paymaster post-op gas (hex).
        sponsor: Optional sponsor metadata for wallet display.
        is_final: Whether this sponsorship is final.
    """

    paymaster: str
    paymaster_data: str
    paymaster_verification_gas_limit: Optional[str] = None
    paymaster_post_op_gas_limit: Optional[str] = None
    sponsor: Optional[Sponsor] = None
    is_final: Optional[bool] = None
