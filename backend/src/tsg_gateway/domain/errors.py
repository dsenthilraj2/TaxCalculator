"""Domain exceptions: expected, user-facing errors mapped to HTTP responses in one place."""


class TaxGatewayError(Exception):
    """Base class for expected errors."""

    code = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidRequestError(TaxGatewayError):
    """The request is well-formed but its content is not acceptable."""

    code = "invalid-request"


class NotFoundError(TaxGatewayError):
    """A referenced resource does not exist."""

    code = "not-found"


class UnsupportedError(TaxGatewayError):
    """The request is valid but outside what this engine or jurisdiction supports."""

    code = "unsupported"
