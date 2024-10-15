import sys
import os


from pyapp_env.classes import (
    BaseEnvironment,
    StringDataType
)

from pyapp_env.main import PyAppEnv

sample_env = BaseEnvironment({
    "sample_key": 1
},
validators={'sample_key': StringDataType()})

env  = PyAppEnv()
