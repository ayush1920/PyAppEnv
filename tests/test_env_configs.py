import os
import sys
import socket
import pytest

from pyapp_env.main import PyAppEnv
from pyapp_env.classes import (
    BaseEnvironment,
    StringDataType,
    SecretDataType,
    PositiveIntegerDataType,
    AnyDataType
)

from pyapp_env.exceptions import (InvalidEnvironmentConfigError,
                                  ImmutableError)


def validate_hostname(value):
    try:
        if value == "localhost":
            return True
        socket.inet_aton(value)
        return True
    except socket.error:
        raise ValueError(f"Value {value} must be a valid IP address.")


def validate_port(value):
    try:
        value = int(value)
        if value < 0 or value > 65535:
            raise ValueError(f"Value {value} must be a valid port number.")
        return True
    except ValueError:
        raise ValueError(f"Value {value} must be a valid port number.")


def validate_non_empty_string(value):
    if not value:
        raise ValueError("Value must not be empty.")
    return True


db_host_validator = StringDataType(validate_hostname)
db_port_validator = PositiveIntegerDataType(validate_port)
db_name_validator = StringDataType(validate_non_empty_string)
db_user_validator = StringDataType()
db_password_validator = StringDataType()


class EnvironmentTest(BaseEnvironment):
    default_test_config = {
        "db_host": "localhost",
        "db_port": 27017,
        "db_name": "test_db",
        "db_user": "",
        "db_password": "Pass123kdalskdlsk@",
        'TEMP':'my_temp',
        'test':[1]
    }

    default_validators = {
        "db_host": db_host_validator,
        "db_port": db_port_validator,
        "db_name": db_name_validator,
        "db_user": db_user_validator,
        "db_password" :SecretDataType(),
        'test': AnyDataType()
    }

    def __init__(self, config=None, validators=None):
        self.config = config or self.default_test_config
        self.validators = validators or self.default_validators
        super().__init__(self.config, self.validators)


class ProdEnvironment(BaseEnvironment):
    default_prod_config = {
        "db_host": "localhost",
        "db_port": 27017,
        "db_name": "prod_db",
    }

    def __init__(self, config=None, validators=None):
        config = config or self.default_prod_config
        super().__init__(config, validators)


env = PyAppEnv(
    default_env="TEST",
    env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment, 'REACT': {'1':2}},
)


# Test Cases
def test_default_environment():
    env = PyAppEnv(
        default_env="PROD",
        env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment},
    )
    assert env.default_env == "PROD"
    assert env.env_name == "PROD"

    for value in zip(env.env.values(), env.PROD.values()):
        assert value[0] == value[1]

def test_invalid_environment_config():
    with pytest.raises(Exception)  as exc_info:
        env = PyAppEnv(
            default_env="INVALID",
            env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment},
        )

    assert isinstance(exc_info.value, InvalidEnvironmentConfigError)
    assert "Invalid Environment Config. Environment \'INVALID\' not available in env_configs" in str(exc_info.value)

def test_environment_config_validation():
    env = PyAppEnv(
        env_name="TEST",
        default_env="PROD",
        env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment},
    )

    assert env.env_configs["TEST"].config["db_host"] == "localhost"
    assert env.env_configs["TEST"].config["db_port"] == 27017
    assert env.env_configs["TEST"].config["db_name"] == "test_db"


def test_envconfig_immutable():
    env = PyAppEnv(
        env_name="TEST",
        default_env="PROD",
        env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment},
    )
    with pytest.raises(Exception) as exc_info:
        env.TEST["db_host"] = "new_host"
    assert isinstance(exc_info.value, ImmutableError)
    assert "Cannot set or update values of the environment config once initalized." in str(exc_info.value)


def test_application_env():
    
    env = PyAppEnv(
        default_env="TEST",
        env_configs={"TEST": EnvironmentTest, "PROD": ProdEnvironment},
        application_env_available=True
    )

    os.environ['APPLICATION_ENV'] = "APPLICATION_ENV_VALUE"
    print(env.env)
    assert env.env['APPLICATION_ENV'] == "APPLICATION_ENV_VALUE"