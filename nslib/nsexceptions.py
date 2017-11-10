class InvalidCredentials(Exception):
    """The username or password are invalid."""

class TooManyRequests(Exception):
    """Invalid card number presented."""

class InvalidCard(Exception):
    """Invalid card number presented."""

class ConnectionError(Exception):
    """Could not connect to NS servers."""

class InvalidResponse(Exception):
    """The NS servers returned unexpected data."""

class MalfomedRoute(Exception):
    """Invalid route array."""

class InvalidStation(Exception):
    """Unknown station code, make sure it's in full caps."""
