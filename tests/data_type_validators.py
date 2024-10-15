import socket

def validate_port(value):
    try:
        value = int(value)
        if value < 0 or value > 65535:
            raise ValueError(f"Value {value} must be a valid port number.")
        return True
    except ValueError:
        raise ValueError(f"Value {value} must be a valid port number.")
    

def validate_hostname(value):
    try:
        if value == "localhost":
            return True
        socket.inet_aton(value)
        return True
    except socket.error:
        raise ValueError(f"Value {value} must be a valid IP address.")


def validate_non_empty_string(value):
    if not value:
        raise ValueError("Value must not be empty.")
    return True