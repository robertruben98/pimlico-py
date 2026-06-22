# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-22

### Added

- Initial release of `pimlico-py`, a typed Python client for the
  [Pimlico](https://docs.pimlico.io) ERC-4337 API.
- Synchronous `PimlicoClient` and asynchronous `AsyncPimlicoClient`, both built
  on `httpx` with a shared JSON-RPC envelope layer.
- Bundler methods: `eth_send_user_operation`, `eth_estimate_user_operation_gas`,
  `eth_get_user_operation_receipt`, `eth_get_user_operation_by_hash`,
  `eth_supported_entry_points`, `pimlico_get_user_operation_gas_price`, and
  `pimlico_get_user_operation_status`.
- Paymaster methods: `pm_sponsor_user_operation`, `pm_get_paymaster_data`, and
  `pm_get_paymaster_stub_data`.
- `wait_for_user_operation_receipt` polling helper (sync and async).
- Pydantic v2 models for EntryPoint v0.7 user operations and all RPC responses.
- JSON-RPC errors surfaced as `PimlicoRPCError`; transport failures as
  `PimlicoHTTPError`.
- Ships `py.typed` for full downstream type checking.

[Unreleased]: https://github.com/robertruben98/pimlico-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robertruben98/pimlico-py/releases/tag/v0.1.0
