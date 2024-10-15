class DefaultEnvironmentError(Exception):
    def __init__(self):
        super().__init__("Default environment must be available and should be a string.")

class InvalidEnvironmentConfigError(Exception):
    def __init__(self, message):
        super().__init__(f"Invalid Environment Config. {message}")

class ImmutableError(Exception):
    """Custom exception raised when attempting to modify an immutable attribute."""
    pass
