# pimlico-py

[![CI](https://github.com/robertruben98/pimlico-py/actions/workflows/ci.yml/badge.svg)](https://github.com/robertruben98/pimlico-py/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pimlico-py.svg)](https://pypi.org/project/pimlico-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/pimlico-py.svg)](https://pypi.org/project/pimlico-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/robertruben98/pimlico-py/blob/main/LICENSE)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A typed Python client for the [Pimlico](https://docs.pimlico.io) ERC-4337
account-abstraction API: **bundler**, **paymaster**, and **gas estimation** over
JSON-RPC.

- Sync (`PimlicoClient`) and async (`AsyncPimlicoClient`) clients on top of
  [`httpx`](https://www.python-httpx.org/).
- [Pydantic v2](https://docs.pydantic.dev/) models for user operations and every
  RPC response.
- JSON-RPC error envelopes surfaced as Python exceptions.
- Ships `py.typed` — full type information for downstream type checkers.
- Python **3.9+**, no mandatory web3 dependency.

> **Heads up:** this client targets **EntryPoint v0.7**
> (`0x0000000071727De22E5E9d8BAf0edAc6f37da032`), the current default for Pimlico
> bundlers and paymasters. See [EntryPoint version](#entrypoint-version) below.

## Installation

```bash
pip install pimlico-py
```

Optional signing/execution helpers (`web3`, `eth-account`) live behind an extra:

```bash
pip install "pimlico-py[exec]"
```

## Quick start

The Pimlico API is keyed by chain ID and authenticated with an API key passed as
a query parameter. Get a free key at <https://dashboard.pimlico.io>.

```python
from pimlico import PimlicoClient

client = PimlicoClient(api_key="pim_xxx", chain=11155111)  # Sepolia

# Current gas prices for user operations (slow / standard / fast).
prices = client.pimlico_get_user_operation_gas_price()
print(prices.standard.max_fee_per_gas)

# Which EntryPoint contracts does this bundler support?
print(client.eth_supported_entry_points())

client.close()
```

`PimlicoClient` is also a context manager:

```python
with PimlicoClient(api_key="pim_xxx", chain=8453) as client:  # Base
    status = client.pimlico_get_user_operation_status("0x9bd0...")
    print(status.status)
```

### Async

```python
import asyncio

from pimlico import AsyncPimlicoClient


async def main() -> None:
    async with AsyncPimlicoClient(api_key="pim_xxx", chain=11155111) as client:
        prices = await client.pimlico_get_user_operation_gas_price()
        print(prices.fast.max_fee_per_gas)


asyncio.run(main())
```

### Sending a user operation and waiting for the receipt

```python
from pimlico import PimlicoClient, UserOperationV07

client = PimlicoClient(api_key="pim_xxx", chain=11155111)

user_op = UserOperationV07(
    sender="0x5a6b47F4131bf1feAFA56A05573314BcF44C9149",
    nonce="0x0",
    call_data="0x...",
    call_gas_limit="0x0",
    verification_gas_limit="0x0",
    pre_verification_gas="0x0",
    max_fee_per_gas="0x7a5cf70d5",
    max_priority_fee_per_gas="0x3b9aca00",
    signature="0xfffffff...",
)

# Estimate gas, then submit.
gas = client.eth_estimate_user_operation_gas(user_op)
user_op.call_gas_limit = gas.call_gas_limit
user_op.verification_gas_limit = gas.verification_gas_limit
user_op.pre_verification_gas = gas.pre_verification_gas

user_op_hash = client.eth_send_user_operation(user_op)

# Poll until the operation is mined (or raise on timeout).
receipt = client.wait_for_user_operation_receipt(user_op_hash, timeout=120.0)
print("success:", receipt.success)
```

### Custom base URL

The base URL is configurable for self-hosted bundlers or alternative regions.
By default it is `https://api.pimlico.io/v2/{chain}/rpc?apikey={api_key}`.

```python
client = PimlicoClient(
    api_key="pim_xxx",
    chain=1,
    base_url="https://my-bundler.example.com/rpc",
)
```

## EntryPoint version

ERC-4337 has shipped multiple `EntryPoint` contracts whose `UserOperation`
layouts differ. This client models **EntryPoint v0.7**, which uses the unpacked
fields (`factory`, `factoryData`, `paymaster`, `paymasterData`,
`paymasterVerificationGasLimit`, `paymasterPostOpGasLimit`). The v0.7 EntryPoint
address (`0x0000000071727De22E5E9d8BAf0edAc6f37da032`) is the default for all
requests; you can override it per call with the `entry_point` argument.

## Error handling

```python
from pimlico import PimlicoClient, PimlicoRPCError, PimlicoHTTPError

client = PimlicoClient(api_key="pim_xxx", chain=11155111)

try:
    client.eth_send_user_operation(user_op)
except PimlicoRPCError as exc:
    # JSON-RPC error envelope: exc.code, exc.message, exc.data
    print("RPC error", exc.code, exc.message)
except PimlicoHTTPError as exc:
    # Non-2xx HTTP response: exc.status_code
    print("HTTP error", exc.status_code)
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). In short:

```bash
pip install -e ".[dev]"
ruff check . && mypy && pytest
```

## License

[MIT](LICENSE)
