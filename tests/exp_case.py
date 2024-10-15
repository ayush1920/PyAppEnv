import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import PyAppEnv

from classes import (
    StringDataType,
    PositiveIntegerDataType,
    NegativeIntegerDataType,
    BooleanDataType,
    ListDataType,
    DictDataType,
    SecretDataType,
    StrongPassword,
    BaseEnvironment,
)


sample_env = BaseEnvironment({"sample_key": 1}, validators={"sample_key": StringDataType()})


env = PyAppEnv("TEST", {'ABC': sample_env})
