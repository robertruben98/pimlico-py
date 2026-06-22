# Contributing to pimlico-py

Thanks for your interest in improving `pimlico-py`! This document explains how
to set up a development environment and the checks your change must pass.

## Development setup

```bash
git clone https://github.com/robertruben98/pimlico-py.git
cd pimlico-py
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality gates

Every change must pass the same gates CI enforces:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

- **Tests are written first.** This project follows test-driven development.
  Add a failing test that describes the behaviour you want, then implement the
  minimal code to make it pass.
- Unit tests mock the JSON-RPC endpoint with [`respx`](https://lundberg.github.io/respx/)
  and never touch the network.
- Live integration tests are marked `@pytest.mark.integration` and are
  deselected by default. They run only when `PIMLICO_API_KEY` is set:

  ```bash
  PIMLICO_API_KEY=pim_... pytest -m integration
  ```

## Compatibility constraints

- The package supports **Python 3.9+**. Do not use PEP 604 unions
  (`X | Y`) in runtime annotations — pydantic evaluates them at runtime and
  they raise `TypeError` on 3.9. Use `typing.Optional` / `typing.Union`.
- `web3` and `eth-account` are optional and live behind the `exec` extra. Core
  code must import cleanly without them.

## Commit & PR conventions

- Keep commits focused and use clear, conventional messages.
- Update `CHANGELOG.md` under `[Unreleased]` for user-facing changes.
- Open pull requests against `main`.
