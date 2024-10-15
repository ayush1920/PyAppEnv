import json
import pytest


from pyapp_env.main import PyAppEnv

from pyapp_env.classes import (
    StringDataType,
    IntegerDataType,
    PositiveIntegerDataType,
    NegativeIntegerDataType,
    FloatDataType,
    BooleanDataType,
    ListDataType,
    DictDataType,
    AnyDataType,
    SecretDataType,
    StrongPasswordDataType,
    EmailDataType,
    BaseEnvironment,
)


def check_datatype_user_method(config_value, BaseValidatorClass, key):
    """
    Test the custom validation method for a given data type.

    This function sets up a sample environment with a custom validator for the specified key
    and checks if the custom validator raises the expected exception.

    Args:
        config_value (dict): The configuration value to be validated.
        BaseValidatorClass (class): The validator class to be used for validation.
        key (str): The key in the configuration value to be validated.

    Raises:
        RuntimeError: If the custom validator raises a RuntimeError.
    """

    def custom_validator(value):
        raise RuntimeError("This is a custom test exception")

    sample_env = BaseEnvironment(config_value, validators={key: BaseValidatorClass(value_validator=custom_validator)})
    with pytest.raises(Exception) as exc_info:
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
    assert isinstance(exc_info.value, RuntimeError)
    assert "This is a custom test exception" in str(exc_info.value)


def test_datetype_contains_methods():

    for _class in (
        StringDataType,
        IntegerDataType,
        PositiveIntegerDataType,
        NegativeIntegerDataType,
        BooleanDataType,
        ListDataType,
        DictDataType,
        SecretDataType,
        StrongPasswordDataType,
        EmailDataType,
    ):
        assert hasattr(_class, "validate_type")
        assert hasattr(_class, "convert_type")
        assert hasattr(_class, "__set_value__")


def test_validate_string_datetype():

    check_datatype_user_method({"sample_key": "localhost"}, StringDataType, "sample_key")

    for values in [1, 1.0, True, False, [1], {1: 1}, None]:
        sample_env = BaseEnvironment({"sample_key": values}, validators={"sample_key": StringDataType()})

        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type string for value {values}" in str(exc_info.value)


def test_validate_integer_datetype():

    check_datatype_user_method({"sample_key": 1}, IntegerDataType, "sample_key")

    for value in ["1", 1.0, 2.0, 99999999999, 0, -1, -99999999999]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": IntegerDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == int(value)

    for value in [9.99, True, False]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": IntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be an integer not of type float or boolean." in str(exc_info.value)

    for value in [[1], {1: 1}, None]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": IntegerDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert (
            f"argument must be a string, a bytes-like object or a real number, not '{value.__class__.__name__}'"
            in str(exc_info.value)
        )

    for value in ["inf", "-inf"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": IntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"invalid literal for int() with base 10: '{value}'" in str(exc_info.value)

    # check for boolean support

    for value in [True, False]:
        sample_env = BaseEnvironment(
            {"sample_key": value}, validators={"sample_key": IntegerDataType(support_boolean=True)}
        )
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == int(value)

    # test if enable conversion is disabled
    for value in ["1", "0"]:
        sample_env = BaseEnvironment(
            {"sample_key": value}, validators={"sample_key": IntegerDataType(convert=False, support_boolean=True)}
        )

        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type integer for value {value}" in str(exc_info.value)


def test_validate_positive_integer_datetype():

    check_datatype_user_method({"sample_key": 1}, PositiveIntegerDataType, "sample_key")

    for value in ["1", 1.0, 2.0, 99999999999]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": PositiveIntegerDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == int(value)

    for value in [0, -1, -99999999999]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": PositiveIntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be a positive integer." in str(exc_info.value)

    for value in [9.99, True, False]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": PositiveIntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be an integer not of type float or boolean." in str(exc_info.value)

    for value in [None]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": PositiveIntegerDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert (
            f"argument must be a string, a bytes-like object or a real number, not '{value.__class__.__name__}'"
            in str(exc_info.value)
        )

    # test if enable conversion is disabled
    for value in ["1"]:
        sample_env = BaseEnvironment(
            {"sample_key": value}, validators={"sample_key": PositiveIntegerDataType(convert=False)}
        )

        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type integer for value {value}" in str(exc_info.value)


def test_validate_negative_integer_datatype():

    check_datatype_user_method({"sample_key": -1}, NegativeIntegerDataType, "sample_key")

    for value in ["-1", -1.0, -2.0, -99999999999]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": NegativeIntegerDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == int(value)

    for value in [0, 1, 99999999999]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": NegativeIntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be a negative integer." in str(exc_info.value)

    for value in [-9.99, True, False]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": NegativeIntegerDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be an integer not of type float or boolean." in str(exc_info.value)

    for value in [None]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": NegativeIntegerDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert (
            f"argument must be a string, a bytes-like object or a real number, not '{value.__class__.__name__}'"
            in str(exc_info.value)
        )

    # test if enable conversion is disabled
    for value in ["-1"]:
        sample_env = BaseEnvironment(
            {"sample_key": value}, validators={"sample_key": NegativeIntegerDataType(convert=False)}
        )

        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)

        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type integer for value {value}" in str(exc_info.value)


def test_validate_float_datatype():

    check_datatype_user_method({"sample_key": 4 / 3}, FloatDataType, "sample_key")

    for value in ["1", 1.0, 1.01, 99999999999, 4 / 3, -4 / 9, -9999, -1.33, -1.01]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == float(value)

    for value in [None, {1: 1}, [1], [], {}]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"float() argument must be a string or a real number, not '{value.__class__.__name__}'" in str(
            exc_info.value
        )

    for value in [True, False]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
    assert f"Value {value} must be a float and not a boolean." in str(exc_info.value)

    for value in [True, False]:
        sample_env = BaseEnvironment(
            {"sample_key": value}, validators={"sample_key": FloatDataType(support_boolean=True)}
        )
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == float(value)

    for value in ["inf", "-inf"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} must be a finite float." in str(exc_info.value)

    for value in ["inf", "-inf"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType(support_inf=True)})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == float(value)

    # test if enable conversion is disabled
    for value in ["1", "1.001"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": FloatDataType(convert=False)})

        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)

        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type float for value {value}" in str(exc_info.value)


def test_validate_boolean_datatype():

    check_datatype_user_method({"sample_key": True}, BooleanDataType, "sample_key")

    for value in [True, False]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": BooleanDataType(convert=False)})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == bool(value)

    test_case = {
        "true": True,
        "1": True,
        "yes": True,
        "y": True,
        "false": False,
        "0": False,
        "no": False,
        "n": False,
        "YES": True,
        "   YES     ": True,
        "    NO": False,
        1: True,
        0: False,
    }

    for key_value, bool_value in test_case.items():
        sample_env = BaseEnvironment(
            {"sample_key": key_value}, validators={"sample_key": BooleanDataType(convert=True)}
        )
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == bool_value

    for value in [[], [1], {}, {1: 2}, "", "abc", "def"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": BooleanDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert (
            f"Value {value} must be in a string format or boolean. Valid values are: true, 1, yes, y, false, 0, no, n."
            in str(exc_info.value)
        )

    for value in [10, 12211, -1, -100]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": BooleanDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} as an interger is not supported for boolean conversion." in str(exc_info.value)

    for value in test_case.keys():
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": BooleanDataType(convert=False)})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type boolean for value {value}" in str(exc_info.value)


def test_validate_list_datatype():

    check_datatype_user_method({"sample_key": [1, 2, 3]}, ListDataType, "sample_key")

    for value in [[1], [1, 2, 3], [1, "2", 3], [1, 2, 3, [1, 2, 3]], [1, 2, 3, {1: 2, 3: 4}], []]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": ListDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == value

    for value in [{1: 2}, {1: 2, 3: 4}, {1: [1, 2, 3]}, {1: {1: 2, 3: 4}}, 1, 1.0, True, False, None]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": ListDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type list for value {value}" in str(exc_info.value)

    for value in ['[{"1": 2}, {"1": 2, "3": 4}, {"1": [1, 2, 3]}, {"1": {"1": 2, "3": 4}}, 1, 1.0, true, false, null]']:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": ListDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == [
            {"1": 2},
            {"1": 2, "3": 4},
            {"1": [1, 2, 3]},
            {"1": {"1": 2, "3": 4}},
            1,
            1.0,
            True,
            False,
            None,
        ]

    for value in ["[{1: 2}, {1: 2, 3: 4}, {1: [1, 2, 3]}, {1: {1: 2, 3: 4}}, 1, 1.0, true, false, None]"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": ListDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} is not a valid list in JSON format." in str(exc_info.value)

    for value in ["{}", '"abc"', "1", '"{1:2}"']:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": ListDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type list for value {json.loads(value)}." in str(exc_info.value)


def test_validate_dict_datatype():

    check_datatype_user_method({"sample_key": {1: 2}}, DictDataType, "sample_key")

    for value in [{1: 2}, {1: 2, 3: 4}, {1: [1, 2, 3]}, {1: {1: 2, 3: 4}}, {}]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == value

    for value in ["dasd", "das"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value {value} is not a valid dictionary in JSON format." in str(exc_info.value)

    for value in [[1, 2, "a"], 1, 1.0, True, False, None]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type dictionary for value {value}" in str(exc_info.value)

    for value in [
        '{"1": 2}',
        '{"1": 2, "3": 4}',
        '{"1": [1, 2, 3]}',
        '{"1": {"1": 2, "3": 4}}',
        '{"a":null}',
        '{"b":false, "c":true}',
        '{"a": {"b": [{"C": 1}]}}',
    ]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == json.loads(value)

    for value in ["[{1: 2}, {1: 2, 3: 4}, {1: [1, 2, 3]}, {1: {1: 2, 3: 4}}, 1, 1.0, true, false, None]"]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert "" in str(exc_info.value)

    for value in ["[]", '"abc"', "1", '["1"]', '[1, 2, "a", {"a": 1}]']:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": DictDataType()})
        with pytest.raises(TypeError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, TypeError)
        assert f"Data must be of type dictionary for value {json.loads(value)}." in str(exc_info.value)


def test_any_datatype():
    # anydatatype should be able to set value
    check_datatype_user_method({"sample_key": "any_datatype"}, AnyDataType, "sample_key")

    # check if any datatype supports all types
    class CustomClass:
        def __init__(self, value):
            self.value = value

    for value in [
        1,
        1.0,
        True,
        False,
        [1],
        {1: 1},
        None,
        "1",
        "1.0",
        "True",
        "False",
        "[1]",
        "{1:1}",
        json.dumps,
        CustomClass,
        CustomClass(1),
    ]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": AnyDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert env.TEST["sample_key"] == value


def test_secret_datatype():
    check_datatype_user_method({"sample_key": "secret"}, SecretDataType, "sample_key")

    # check if secret data type is working as expected
    sample_env = BaseEnvironment({"sample_key": 2}, validators={"sample_key": SecretDataType()})
    env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
    assert str(env.TEST["sample_key"]) == "******"
    assert env.TEST["sample_key"].__repr__() == "******"
    assert env.TEST["sample_key"].unmasked == 2

    # check if enablicng show_secured_values is returning a normal variable
    sample_env = BaseEnvironment({"sample_key": "secret"}, validators={"sample_key": SecretDataType()})
    env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False, show_secured_values=True)
    assert env.TEST["sample_key"] == "secret"
    assert str(env.TEST["sample_key"]) == "secret"
    assert not hasattr(env.TEST["sample_key"], "unmasked")

    # check if disabling mutable values is working as expected
    # It should return a normal class when any opertaion is done on the value
    sample_env = BaseEnvironment({"sample_key": "secret"}, validators={"sample_key": SecretDataType()})
    env = PyAppEnv("TEST", {"TEST": sample_env}, make_secured_values_mutable=False, print_logs=False)

    assert env.TEST["sample_key"] == "secret"
    assert str(env.TEST["sample_key"]) == "******"
    assert env.TEST["sample_key"].unmasked == "secret"

    new_var = env.TEST["sample_key"] + "123"
    assert new_var == "secret123" and type(new_var) == str

    # test for immutable boolean class

    sample_env = BaseEnvironment({"sample_key": True}, validators={"sample_key": SecretDataType()})
    env = PyAppEnv("TEST", {"TEST": sample_env}, make_secured_values_mutable=False, print_logs=False)
    assert env.TEST["sample_key"] == True

    # check if doing any operation on the secret value is returning the class "SecureValue" again.
    # Checking for multiple types of primitive and non primitive data types including custom class.

    class CustomClass:
        def __init__(self, test_value):
            self.test_value = test_value

        def __len__(self):
            return len(self.test_value)

        def __add__(self, value):
            return self.test_value + value.test_value

        def __radd__(self, value):
            return self.test_value + value.test_value

    for value in ["secret", 1, 4 / 3, True, False, [1], {1: 1}, None, CustomClass([10]), json.dumps]:
        sample_env = BaseEnvironment({"sample_key": value}, validators={"sample_key": SecretDataType()})
        env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)

        if isinstance(value, str):
            new_var = env.TEST["sample_key"] + "123"
            assert isinstance(new_var.unmasked, str)
            assert (new_var == value + "123").unmasked
            assert new_var.unmasked == value + "123"
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, bool):
            new_var = env.TEST["sample_key"] + True
            assert (new_var == value + True).unmasked
            assert isinstance(new_var.unmasked, int)
            assert new_var.unmasked == value + True
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, int):
            new_var = env.TEST["sample_key"] + 123
            assert (new_var == value + 123).unmasked
            assert isinstance(new_var.unmasked, int)
            assert new_var.unmasked == value + 123
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, float):
            new_var = env.TEST["sample_key"] + 123.345
            assert (new_var == value + 123.345).unmasked
            assert isinstance(new_var.unmasked, float)
            assert new_var.unmasked == value + 123.345
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, list):
            new_var = env.TEST["sample_key"] + [1, 2, 3]
            assert (new_var == value + [1, 2, 3]).unmasked
            assert isinstance(new_var.unmasked, list)
            assert new_var.unmasked == value + [1, 2, 3]
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, dict):
            env.TEST["sample_key"].update({1: 2, 3: 4})
            new_var = env.TEST["sample_key"]
            assert (new_var == {**value, **{1: 2, 3: 4}}).unmasked
            assert isinstance(new_var.unmasked, dict)
            assert new_var.unmasked == {**value, **{1: 2, 3: 4}}
            assert type(new_var).__name__ == "SecureValue"

        elif value == None:
            new_var = env.TEST["sample_key"]
            assert new_var == None

        elif isinstance(value, CustomClass):
            new_var = env.TEST["sample_key"] + CustomClass([1, 2, 3])
            assert isinstance(new_var, list)
            assert new_var.unmasked == [10, 1, 2, 3]
            assert type(new_var).__name__ == "SecureValue"

        elif isinstance(value, json.JSONEncoder):
            val = env.TEST["sample_key"]
            assert type(val).__name__ == "SecureValue"
            assert val.unmasked == value


def test_strong_password_datatype(): 
    check_datatype_user_method({"sample_key": "Abc@2265"}, StrongPasswordDataType, "sample_key")
    min_lenght = 8
    max_length = 16
    test_passwords = {
        "Abc@1234": "Password should not contain common patterns or sequences.",
        "weakpassword": "Password must contain at least one uppercase letter.",
        "Abcde1234": "Password must contain at least one special character.",
        "abc@1234": "Password must contain at least one uppercase letter.",
        "ABC@1234": "Password must contain at least one lowercase letter.",
        "Abc@abcd": "Password must contain at least one digit.",
        "DEF@123456": "Password must contain at least one lowercase letter.",
        "Abc@1234!": "Password should not contain common patterns or sequences.",
        "Abc@1234#": "Password should not contain common patterns or sequences.",
        "Abces@123456894555678445": f"Password must be at most {max_length} characters long.",
        "Abc@14": f"Password must be at least {min_lenght} characters long.",
    }

    for password, error_message in test_passwords.items():
        sample_env = BaseEnvironment(
            {"sample_key": password},
            validators={"sample_key": StrongPasswordDataType(max_length=max_length, min_length=min_lenght)},
        )
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert error_message in str(exc_info.value)


def test_email_datatype():
    check_datatype_user_method({"sample_key": "sample.email@gmail.com"}, EmailDataType, "sample_key")

    for email in ["abc", "abc@", "abc@abc", "abc@abc.", "abc@abc.c", 'abc@abc"c.com']:
        sample_env = BaseEnvironment({"sample_key": email}, validators={"sample_key": EmailDataType()})
        with pytest.raises(ValueError) as exc_info:
            env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
        assert isinstance(exc_info.value, ValueError)
        assert f"Value '{email}' is not a valid email address." in str(exc_info.value)

    # ensure + is allowed in email
    sample_env = BaseEnvironment({"sample_key": "rahul+kumar@gmail.com"}, validators={"sample_key": EmailDataType()})
    env = PyAppEnv("TEST", {"TEST": sample_env}, print_logs=False)
    assert env.TEST["sample_key"] == "rahul+kumar@gmail.com"