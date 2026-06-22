"""Exception hierarchy for :mod:`pimlico`.

All errors raised by the client derive from :class:`PimlicoError`, so callers
can catch every library-specific failure with a single ``except`` clause.
"""

from typing import Any, Optional


class PimlicoError(Exception):
    """Base class for every error raised by ``pimlico-py``."""


class PimlicoRPCError(PimlicoError):
    """A JSON-RPC ``error`` object was returned by the Pimlico endpoint.

    The Pimlico API answers with HTTP ``200`` even for application-level
    failures, signalling them through the JSON-RPC ``error`` member. This
    exception carries the three standard JSON-RPC error fields.

    Args:
        code: The integer JSON-RPC error code (for example ``-32602`` for
            invalid params).
        message: The human-readable error message returned by the server.
        data: Optional structured data the server attached to the error.
    """

    def __init__(
        self,
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC error {code}: {message}")


class PimlicoHTTPError(PimlicoError):
    """The Pimlico endpoint returned a non-success HTTP status code.

    Raised for transport-level failures (for example ``401`` for a bad API key
    or ``429`` when rate limited) where no JSON-RPC envelope is available.

    Args:
        status_code: The HTTP status code of the response.
        message: A human-readable description of the failure.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class PimlicoTimeoutError(PimlicoError):
    """A polling helper exhausted its timeout before the condition was met.

    Raised by :meth:`PimlicoClient.wait_for_user_operation_receipt` (and its
    async counterpart) when no receipt becomes available within the deadline.
    """
