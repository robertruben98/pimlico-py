"""Tests for paymaster and getUserOperationByHash response models."""

from pimlico.models import (
    PaymasterData,
    PaymasterStubData,
    SponsorUserOperationResult,
    UserOperationByHash,
    UserOperationV07,
)


def test_paymaster_stub_data_parses_v07_fields():
    payload = {
        "paymaster": "0xpm",
        "paymasterData": "0xdata",
        "paymasterVerificationGasLimit": "0x1",
        "paymasterPostOpGasLimit": "0x2",
        "isFinal": False,
        "sponsor": {"name": "Pimlico", "icon": "data:image/png;base64,xx"},
    }

    stub = PaymasterStubData.model_validate(payload)

    assert stub.paymaster == "0xpm"
    assert stub.paymaster_data == "0xdata"
    assert stub.paymaster_verification_gas_limit == "0x1"
    assert stub.paymaster_post_op_gas_limit == "0x2"
    assert stub.is_final is False
    assert stub.sponsor is not None
    assert stub.sponsor.name == "Pimlico"


def test_paymaster_stub_data_optional_fields_default():
    payload = {"paymaster": "0xpm", "paymasterData": "0xdata"}

    stub = PaymasterStubData.model_validate(payload)

    assert stub.is_final is None
    assert stub.sponsor is None
    assert stub.paymaster_verification_gas_limit is None


def test_paymaster_data_parses_v07_fields():
    payload = {"paymaster": "0xpm", "paymasterData": "0xdata"}

    data = PaymasterData.model_validate(payload)

    assert data.paymaster == "0xpm"
    assert data.paymaster_data == "0xdata"


def test_sponsor_result_parses_v07_fields():
    payload = {
        "paymaster": "0xpm",
        "paymasterData": "0xdata",
        "paymasterVerificationGasLimit": "0x1",
        "paymasterPostOpGasLimit": "0x2",
    }

    result = SponsorUserOperationResult.model_validate(payload)

    assert result.paymaster == "0xpm"
    assert result.paymaster_data == "0xdata"
    assert result.paymaster_verification_gas_limit == "0x1"


def test_user_operation_by_hash_parses_nested_user_operation():
    payload = {
        "userOperation": {
            "sender": "0xabc",
            "nonce": "0x0",
            "callData": "0xdead",
            "callGasLimit": "0x1",
            "verificationGasLimit": "0x2",
            "preVerificationGas": "0x3",
            "maxFeePerGas": "0x4",
            "maxPriorityFeePerGas": "0x5",
            "signature": "0xbeef",
        },
        "entryPoint": "0x0000000071727De22E5E9d8BAf0edAc6f37da032",
        "blockNumber": "0x10",
        "blockHash": "0xblock",
        "transactionHash": "0xtx",
    }

    by_hash = UserOperationByHash.model_validate(payload)

    assert isinstance(by_hash.user_operation, UserOperationV07)
    assert by_hash.user_operation.sender == "0xabc"
    assert by_hash.entry_point == "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
    assert by_hash.block_number == "0x10"
    assert by_hash.transaction_hash == "0xtx"
