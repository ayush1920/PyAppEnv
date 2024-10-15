import types
import weakref
from copyreg import dispatch_table
from .global_vars import LoggerType

global_logger: LoggerType  # Global logger object to log the messages
compariosn_methods_with_type_error = ["__lt__", "__le__", "__gt__", "__ge__"]
compariosn_methods_with_return = ["__eq__", "__ne__"]
comparion_method_symbol = {
    "__eq__": "==",
    "__ne__": "!=",
    "__lt__": "<",
    "__le__": "<=",
    "__gt__": ">",
    "__ge__": ">=",
}


def check_inheritable_class(class_name):
    try:

        class Test(class_name):
            pass

    except TypeError:
        return False
    return True


def method_wrapper(method, ignored_class=None, ignored_methods=None):
    if not ignored_methods:
        ignored_methods = []

    def wrapped(self, *args, **kwargs):
        result = getattr(self._original_data, method.__name__)(*args, **kwargs)
        if (
            result is None
            or (ignored_class and isinstance(result, ignored_class))
            or method.__name__ in ignored_methods
        ):
            return result

        if isinstance(result, types.NotImplementedType) and method.__name__ in compariosn_methods_with_type_error:
            value = args[0]
            symbol = comparion_method_symbol[method.__name__]
            raise TypeError(
                f"'{symbol}' not supported between instances of '{self.__class__.__name__}' and '{value.__class__.__name__}'"
            )

        if isinstance(result, types.NotImplementedType) and method.__name__ in compariosn_methods_with_return:
            return False

        return CreateSecureValue(result, ignored_class=ignored_class, ignored_method=ignored_methods)

    return wrapped


def CreateSecureValue(value, is_mutable=True, ignored_class=None, ignored_method=None):
    if ignored_class and isinstance(value, ignored_class) or isinstance(value, types.NoneType):
        return value

    if not ignored_method:
        ignored_method = ["__len__"]

    def unmasked(self):
        return self._original_data

    methods = {}
    properties = {}
    exceptions = [
        "__str__",
        "__repr__",
        "__class__",
        "__getattribute__",
        "__new__",
        "__init__",
        f"__{value.__class__.__name__}__",
    ]

    value_class = value.__class__

    if isinstance(value, bool):
        value_class = int

    if not is_mutable:
        # create custom class for immutable objects
        if not check_inheritable_class(value_class):
            return value

        class SecureValue(value_class):
            def __init__(self, value):

                self._original_data = value

            def __str__(self):
                return "******"

            def __repr__(self):
                return "******"

            @property
            def unmasked(self):
                return self._original_data

        return SecureValue(value)

    for attr_name in dir(value):
        attr = getattr(value, attr_name)
        if isinstance(
            attr,
            (types.MethodType, types.BuiltinMethodType, types.MethodWrapperType),
        ):
            if attr_name in exceptions:
                continue
            wrapped_method = method_wrapper(attr, ignored_class=ignored_class, ignored_methods=ignored_method)
            methods[attr_name] = wrapped_method
        elif not isinstance(attr, type):
            properties[attr_name] = attr

    # test if class can be inherited
    if not check_inheritable_class(value_class):
        return value

    def temp_init_function(self, *args, **kwargs): ...

    temp_init = temp_init_function
    original_init = getattr(value_class, "__init__")

    if isinstance(value, object):
        base_class = value.__class__.mro()[-2]
    else:
        base_class = value.__class__
    base_class = type(value)
    value_class_is_immutable = base_class in [
        type(None),
        int,
        float,
        bool,
        complex,
        str,
        tuple,
        bytes,
        frozenset,
        type,
        range,
        slice,
        property,
        types.BuiltinFunctionType,
        type(Ellipsis),
        type(NotImplemented),
        types.FunctionType,
        weakref.ref,
    ]

    if value_class_is_immutable:
        temp_init = original_init

    SecureValue = type(
        "SecureValue",
        (value_class,),
        {
            "mask_value": True,
            "_original_data": value,
            "unmasked": property(unmasked),
            "__str__": lambda self: "******",
            "__repr__": lambda self: "******",
            **methods,
            "__init__": temp_init,
        },
    )

    instance = SecureValue.__new__(SecureValue)
    
    # Create an instance of the dynamic class
    SecureValue.__init__(instance, value)

    if not value_class_is_immutable:
        for key, property_value in properties.items():
            if key == "__doc__":
                continue
            try:
                setattr(instance, key, property_value)
            except:
                if (base_class in (dict, list) and key == "__hash__") or key == '__weakref__':
                    continue
                raise
            
    # restore original __init__ method
    setattr(SecureValue, "__init__", original_init)

    return instance
