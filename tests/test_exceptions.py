"""Tests for the exception hierarchy."""

from pimlico.exceptions import (
    PimlicoError,
    PimlicoHTTPError,
    PimlicoRPCError,
)


def test_rpc_error_carries_code_message_and_data():
    err = PimlicoRPCError(code=-32602, message="Invalid params", data={"hint": "nope"})

    assert err.code == -32602
    assert err.message == "Invalid params"
    assert err.data == {"hint": "nope"}


def test_rpc_error_str_includes_code_and_message():
    err = PimlicoRPCError(code=-32000, message="bundler rejected")

    text = str(err)
    assert "-32000" in text
    assert "bundler rejected" in text


def test_rpc_error_is_a_pimlico_error():
    err = PimlicoRPCError(code=-1, message="x")

    assert isinstance(err, PimlicoError)


def test_http_error_carries_status_code():
    err = PimlicoHTTPError(status_code=429, message="rate limited")

    assert err.status_code == 429
    assert "429" in str(err)
    assert isinstance(err, PimlicoError)


def test_pimlico_error_is_an_exception():
    assert issubclass(PimlicoError, Exception)


def test_rpc_error_data_defaults_to_none():
    err = PimlicoRPCError(code=-1, message="x")

    assert err.data is None
