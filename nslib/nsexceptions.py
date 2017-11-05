
class InvalidCredentials(Exception):
    """The username or password are invalid."""

class TooManyRequests(Exception):
    """Invalid card number presented."""

class InvalidCard(Exception):
    """Invalid card number presented."""

class ConnectionError(Exception):
    """Could not connect to NS servers."""
