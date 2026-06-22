"""Tests for the pydantic models."""

from pimlico.models import (
    GasPriceResult,
    GasPriceTier,
    UserOperationGasEstimate,
    UserOperationReceipt,
    UserOperationStatus,
    UserOperationV07,
)


def test_user_operation_v07_serializes_with_camelcase_aliases():
    op = UserOperationV07(
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

    dumped = op.to_rpc()

    assert dumped["sender"] == "0xabc"
    assert dumped["callData"] == "0xdead"
    assert dumped["callGasLimit"] == "0x1"
    assert dumped["maxFeePerGas"] == "0x4"
    assert dumped["maxPriorityFeePerGas"] == "0x5"


def test_user_operation_v07_omits_unset_optional_factory_and_paymaster():
    op = UserOperationV07(
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

    dumped = op.to_rpc()

    assert "factory" not in dumped
    assert "factoryData" not in dumped
    assert "paymaster" not in dumped


def test_user_operation_v07_includes_factory_when_set():
    op = UserOperationV07(
        sender="0xabc",
        nonce="0x0",
        factory="0xfac",
        factory_data="0xfeed",
        call_data="0xdead",
        call_gas_limit="0x1",
        verification_gas_limit="0x2",
        pre_verification_gas="0x3",
        max_fee_per_gas="0x4",
        max_priority_fee_per_gas="0x5",
        signature="0xbeef",
    )

    dumped = op.to_rpc()

    assert dumped["factory"] == "0xfac"
    assert dumped["factoryData"] == "0xfeed"


def test_gas_price_result_parses_camelcase_tiers():
    payload = {
        "slow": {"maxFeePerGas": "0x829b42b5", "maxPriorityFeePerGas": "0x829b42b5"},
        "standard": {"maxFeePerGas": "0x88d36a75", "maxPriorityFeePerGas": "0x88d36a75"},
        "fast": {"maxFeePerGas": "0x8f0b9234", "maxPriorityFeePerGas": "0x8f0b9234"},
    }

    result = GasPriceResult.model_validate(payload)

    assert isinstance(result.standard, GasPriceTier)
    assert result.slow.max_fee_per_gas == "0x829b42b5"
    assert result.fast.max_priority_fee_per_gas == "0x8f0b9234"


def test_gas_estimate_parses_v07_fields():
    payload = {
        "preVerificationGas": "0xd3e3",
        "verificationGasLimit": "0x60b01",
        "callGasLimit": "0x13880",
        "paymasterVerificationGasLimit": "0x0",
        "paymasterPostOpGasLimit": "0x0",
    }

    est = UserOperationGasEstimate.model_validate(payload)

    assert est.pre_verification_gas == "0xd3e3"
    assert est.verification_gas_limit == "0x60b01"
    assert est.call_gas_limit == "0x13880"
    assert est.paymaster_verification_gas_limit == "0x0"
    assert est.paymaster_post_op_gas_limit == "0x0"


def test_gas_estimate_paymaster_fields_optional():
    payload = {
        "preVerificationGas": "0xd3e3",
        "verificationGasLimit": "0x60b01",
        "callGasLimit": "0x13880",
    }

    est = UserOperationGasEstimate.model_validate(payload)

    assert est.paymaster_verification_gas_limit is None


def test_user_operation_status_parses_status_and_tx_hash():
    payload = {
        "status": "included",
        "transactionHash": "0x57465d20",
    }

    status = UserOperationStatus.model_validate(payload)

    assert status.status == "included"
    assert status.transaction_hash == "0x57465d20"


def test_user_operation_status_allows_null_tx_hash():
    payload = {"status": "not_found", "transactionHash": None}

    status = UserOperationStatus.model_validate(payload)

    assert status.status == "not_found"
    assert status.transaction_hash is None


def test_user_operation_receipt_parses_nested_receipt():
    payload = {
        "userOpHash": "0xa5a5",
        "entryPoint": "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789",
        "sender": "0x8C6b",
        "nonce": "0x1855",
        "actualGasUsed": "0x7f550",
        "actualGasCost": "0x4b3b147f788710",
        "success": True,
        "logs": [],
        "receipt": {
            "transactionHash": "0x5746",
            "blockNumber": "0x31de70e",
            "status": "0x1",
        },
    }

    receipt = UserOperationReceipt.model_validate(payload)

    assert receipt.success is True
    assert receipt.user_op_hash == "0xa5a5"
    assert receipt.actual_gas_used == "0x7f550"
    assert receipt.receipt.transaction_hash == "0x5746"
    assert receipt.receipt.block_number == "0x31de70e"
