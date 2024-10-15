import re
import json
import copy
import types
from tld import get_tld
from abc import ABC, abstractmethod
from .secure_value import CreateSecureValue

from . import exceptions
from .global_vars import (
    LoggerType,
    show_secured_values as glb_show_secured_values,
    make_secured_values_mutable as glb_make_secured_values_mutable,
)

supported_log_levels = ["info", "error", "warning", "debug", "critical", "log"]
pyappenv_logger: LoggerType


class DefaultLogger:
    def __init__(self):
        for log_level in supported_log_levels:
            setattr(self, log_level, lambda x: None)


class ParamValues:
    def __init__(self, value, *kwargs):
        self.value = value
        for key, value in kwargs:
            setattr(self, key, value)


class NoLogger:
    def __init__(self):
        for log_level in supported_log_levels:
            setattr(self, log_level, lambda x: None)


class NoInheritClass(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        if bases:
            raise exceptions.ImmutableError(f"Subclassing of {name} is not allowed")


class BaseDataType(ABC):
    mask_value = False

    def precheck_empty_value(self):
        if not hasattr(self, "value") or self.value == "NOT_SET":
            raise ValueError("Value not set.")

    def __set_value__(self, value):
        self.value = value

    @abstractmethod
    def convert_type(self):
        pass

    @abstractmethod
    def validate_type(self):
        pass

    @abstractmethod
    def value_validator(self):
        pass


class ConfigValue(metaclass=NoInheritClass):
    def __init__(self, value_validator):
        self._value_validator = value_validator
        self.value = value_validator.value

    @property
    def value_validator(self):
        return self._value_validator

    @value_validator.setter
    def value_validator(self, validator):
        if not isinstance(validator, BaseDataType):
            raise ValueError("value_validator must be a subclass of BaseDataType.")
        self._value_validator = validator
        

class EnvConfig(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_dict_initialized = False
        for key, value in self.items():
            try:
                getattr(self, key)
            except AttributeError:
                setattr(self, key, value)

        self.is_dict_initialized = True


    def __repr__(self):
        prnt_list = []
        for key, value in self.items():
            if isinstance(key, str):
                key = f'"{key}"'

            if isinstance(value, ConfigValue):
                value = value.value

            if isinstance(value, str):
                value = f'"{str(value)}"'

            prnt_list.append(f"{key}: {str(value)}")
        return "{" + ", ".join(prnt_list) + "}"

    def __str__(self) -> str:
        return self.__repr__()

    def get_config_value(self, key):
        return self.get(key, None)

    def get(self, key, default=None):
        value = super().get(key, default)
        return value.value if isinstance(value, ConfigValue) else value

    def __getitem__(self, key):
        value = super().__getitem__(key)
        return value.value if isinstance(value, ConfigValue) else value

    def __setitem__(self, key, value) -> types.NoneType:

        if self.is_dict_initialized:
            raise exceptions.ImmutableError("Cannot set or update values of the environment config once initalized.")

        if not isinstance(value, ConfigValue):
            raise ValueError("Value must be an instance of ConfigValue.")

        value = super().__setitem__(key, value)
        try:
            value = getattr(self, key)
            if isinstance(value, ConfigValue):
                setattr(self, key, value)
        except AttributeError:
            setattr(self, key, value)

        return value

    def __delitem__(self, key) -> types.NoneType:
        value = super().__delitem__(key)
        try:
            delattr(self, key)
        except AttributeError:
            pass
        return value

    def popitem(self) -> tuple:
        key, value = super().popitem()
        try:
            delattr(self, key)
        except AttributeError:
            pass
        return key, value

    def pop(self, key, default=None):
        value = super().pop(key, default)
        try:
            delattr(self, key)
        except AttributeError:
            pass
        return value

    def values(self) -> list:
        return [value.value for value in super().values()]

    def items(self) -> tuple:
        return ((key, value.value) for key, value in super().items())

class BaseEnvironment(ABC):
    def __init__(self, config, validators=None):
        self.config = config
        self.validators = validators or {}

    def _init_from_PyEnv(self):
        self.__load_config(self.config, self.validators)

    def __load_config(self, config, validators):
        if not isinstance(config, dict):
            raise exceptions.InvalidEnvironmentConfigError("Environment configs must be a dictionary.")

        derieved_config = {}

        for key, value in config.items():
            validator = None

            if key in validators:
                validator = validators[key]

                if not isinstance(validator, BaseDataType):
                    raise exceptions.InvalidEnvironmentConfigError(
                        f"Environment validator for {key} must be a subclass of BaseDataType.\nImport from classes.py"
                    )
                try:
                    validator.__set_value__(value)
                except Exception as e:
                    pyappenv_logger.error(f"Error setting value for {key}: {e}")
                    raise

            if not validator:
                validator = AnyDataType()
                validator.__set_value__(value)

            config_value = ConfigValue(validator)
            derieved_config[key] = config_value

        # derieved_config should be a type EnvConfig
        self.config = EnvConfig(derieved_config)


class StandardDataType(BaseDataType):
    def __init__(self, datatype, datatype_name=None, value_validator=None):
        self.data_type = datatype
        self.datatype_name = datatype_name or datatype.__name__

        if not (value_validator is None or callable(value_validator)):
            raise ValueError("value_validator must be a callable.")

        if value_validator:
            self.user_validator = value_validator

        if hasattr(self, "_value_validator") and callable(self._value_validator):
            self.value_validator = self._value_validator

    def convert_type(self):
        """This method is meant to be overridden by subclasses."""
        pass

    def validate_type(self):
        if not isinstance(self.value, self.data_type):
            raise TypeError(f"Data must be of type {self.datatype_name} for value {self.value}.")

    def value_validator(self):
        """This method is meant to be overridden by subclasses."""
        pass

    def user_validator(self, *args, **kwargs):
        """This method is meant to be overridden by subclasses."""
        pass

    def convert_to_secure_value(self, value):
        if hasattr(self, "mask_value") and self.mask_value and not glb_show_secured_values:
            return CreateSecureValue(value, is_mutable=glb_make_secured_values_mutable, ignored_class=ConfigValue)
        return value

    def __set_value__(self, value, return_self = False):
        self.value = self.convert_to_secure_value(value)
        self.precheck_empty_value()
        self.convert_type()

        self.validate_type()
        self.value_validator()
        self.user_validator(self.value)
        if return_self:
            return self


class StringDataType(StandardDataType):
    def __init__(self, value_validator=None):
        super().__init__(str, "string", value_validator)

    def _value_validator(self):
        if not isinstance(self.value, str):
            raise ValueError(f"Value {self.value} must be a string.")


class IntegerDataType(StandardDataType):
    def __init__(self, value_validator=None, convert=True, support_boolean=False):
        self.support_boolean = support_boolean
        super().__init__(int, "integer", value_validator)
        if not convert:
            self.convert_type = lambda: None

    def convert_type(self):
        if isinstance(self.value, int) and not (isinstance(self.value, bool) and not self.support_boolean):
            self.value = int(self.value)
            return

        try:
            int_value = int(self.value)
            float_value = float(self.value)
            if int_value != float_value or type(self.value) not in [str, float]:
                raise ValueError(f"Value {self.value} must be an integer not of type float or boolean.")
            self.value = int_value

        except Exception as e:
            pyappenv_logger.error(f"Value {self.value} must be an integer.")
            raise

    def _value_validator(self):
        if not isinstance(self.value, int):
            raise ValueError(f"Value {self.value} must be an integer.")


class PositiveIntegerDataType(IntegerDataType):
    def __init__(self, value_validator=None, convert=True):
        super().__init__(value_validator, convert)

    def _value_validator(self):
        if self.value <= 0:
            raise ValueError(f"Value {self.value} must be a positive integer.")


class NegativeIntegerDataType(IntegerDataType):
    def __init__(self, value_validator=None, convert=True):
        super().__init__(value_validator, convert)

    def _value_validator(self):
        if self.value >= 0:
            raise ValueError(f"Value {self.value} must be a negative integer.")


class FloatDataType(StandardDataType):
    def __init__(self, value_validator=None, convert=True, support_inf=False, support_boolean=False):
        self.support_inf = support_inf
        self.support_boolean = support_boolean
        super().__init__(float, "float", value_validator)
        if not convert:
            self.convert_type = lambda: None

    def convert_type(self):
        if isinstance(self.value, float) and not (isinstance(self.value, bool) and not self.support_boolean):
            return

        try:
            if not self.support_inf and isinstance(self.value, str):
                temp_string = self.value.lower().strip()
                if temp_string in ["inf", "-inf"]:
                    raise ValueError(f"Value {self.value} must be a finite float.")

            if not self.support_boolean and isinstance(self.value, bool):
                raise ValueError(f"Value {self.value} must be a float and not a boolean.")

            self.value = float(self.value)
        except Exception as e:
            pyappenv_logger.error(f"Value {self.value} must be a float.")
            raise


class BooleanDataType(StandardDataType):
    def __init__(self, value_validator=None, convert=True):
        super().__init__(bool, "boolean", value_validator)

        if not convert:
            self.convert_type = lambda: None

    def convert_type(self):
        err_msg = f"Value {self.value} must be in a string format or boolean. Valid values are: true, 1, yes, y, false, 0, no, n."
        if isinstance(self.value, bool):
            return

        if isinstance(self.value, int):
            if self.value in [0, 1]:
                self.value = bool(self.value)
                return
            raise ValueError(f"Value {self.value} as an interger is not supported for boolean conversion.")

        if not isinstance(self.value, str):
            raise ValueError(err_msg)

        true_values = ["true", "1", "yes", "y"]
        false_values = ["false", "0", "no", "n"]

        if self.value.strip().lower() in true_values:
            self.value = True
        elif self.value.strip().lower() in false_values:
            self.value = False
        else:
            raise ValueError(err_msg)


class ListDataType(StandardDataType):
    def __init__(self, value_validator=None, convert=True):
        super().__init__(list, "list", value_validator)

        if not convert:
            self.convert_type = lambda: None

    def convert_type(self):
        if isinstance(self.value, list):
            return

        if isinstance(self.value, str):
            try:
                self.value = json.loads(self.value)
            except json.JSONDecodeError:
                raise ValueError(f"Value {self.value} is not a valid list in JSON format.")


class DictDataType(StandardDataType):
    def __init__(self, value_validator=None, convert=True):
        super().__init__(dict, "dictionary", value_validator)
        if not convert:
            self.convert_type = lambda: None

    def convert_type(self):
        if isinstance(self.value, dict):
            return

        if isinstance(self.value, str):
            try:
                self.value = json.loads(self.value)
            except json.JSONDecodeError:
                raise ValueError(f"Value {self.value} is not a valid dictionary in JSON format.")


class AnyDataType(StandardDataType):
    def __init__(self, value_validator=None):
        super().__init__(object, "any", value_validator)


class SecretDataType(StandardDataType):
    def __init__(self, value_validator=None):
        self.mask_value = True
        super().__init__(object, "string", value_validator)


class StrongPasswordDataType(SecretDataType):
    __SPECIAL_CHARS = "!@#$%^&*()_+"
    __DEFAULT_MAX_LENGTH = float("inf")

    def __init__(
        self,
        value_validator=None,
        min_length=8,
        max_length=None,
        special_chars=True,
        numbers=True,
        uppercase=True,
        lowercase=True,
        special_chars_list=None,
    ):
        self.is_password = True
        self.min_length = min_length
        self.max_length = max_length or self.__DEFAULT_MAX_LENGTH
        self.special_chars = special_chars
        self.numbers = numbers
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.special_chars_list = special_chars_list or self.__SPECIAL_CHARS
        self.__validate_special_chars()

        super().__init__(value_validator)

    def __validate_special_chars(self):
        if not self.special_chars:
            return

        if isinstance(self.special_chars_list, list):
            self.special_chars_list = "".join(self.special_chars_list)

        if not isinstance(self.special_chars_list, str):
            raise ValueError("Special characters must be a string or list of characters.")

    def _value_validator(self):
        # Check length
        password_value = self.value
        if self.value.__class__.__name__ == "SecureValue":
            password_value = self.value._original_data

        if len(password_value) < self.min_length:
            raise ValueError(f"Password must be at least {self.min_length} characters long.")

        if len(password_value) > self.max_length:
            raise ValueError(f"Password must be at most {self.max_length} characters long.")

        # Check for uppercase
        if not re.search(r"[A-Z]", password_value):
            raise ValueError("Password must contain at least one uppercase letter.")

        # Check for lowercase
        if not re.search(r"[a-z]", password_value):
            raise ValueError("Password must contain at least one lowercase letter.")

        # Check for digits
        if not re.search(r"\d", password_value):
            raise ValueError("Password must contain at least one digit.")

        # Check for special characters
        if not re.search(f"[{self.special_chars_list}]", password_value):
            raise ValueError("Password must contain at least one special character.")

        # Check for common patterns
        # if re.search(r"(.)\1{3,}", password_value):  # Repeated characters
        #     raise ValueError("Password should not contain repeated characters.")

        if re.search(
            r"1234|abcd|qwerty|password|abc@123|password@123|12345678",
            password_value,
            re.IGNORECASE,
        ):
            raise ValueError("Password should not contain common patterns or sequences.")


class EmailDataType(StandardDataType):
    def __init__(self, value_validator=None):
        super().__init__(str, "string", value_validator)

    def _value_validator(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.value):
            raise ValueError(f"Value '{self.value}' is not a valid email address.")

        # validate domain name
        domain_name = self.value.split("@")
        if domain_name and len(domain_name) == 2:
            is_valid_domain = self.is_valid_domain_name(domain_name[1])
            if not is_valid_domain:
                raise ValueError(f"Value '{self.value}' is not a valid email address.")

    def is_valid_domain_name(self, domain_name):
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain_name):
            return False

        try:
            url = f"http://{domain_name}"
            pattern = r'https?://(?:www\.)?([a-zA-Z0-9.-]+)'
            match = re.match(pattern, url)
            if not match:
                return False

            # This will raise an exception if the TLD is not valid
            tld = get_tld(url, as_object=True)
            return True
        except Exception as e:
            return False
