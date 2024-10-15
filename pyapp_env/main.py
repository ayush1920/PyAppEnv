import os
import sys
import builtins
from dotenv import load_dotenv

from . import exceptions
from .classes import (
    BaseEnvironment as _BaseEnvironment,
    DefaultLogger as _DefaultLogger,
    NoLogger as _NoLogger,
    BaseDataType as _BaseDataType,
    AnyDataType as _AnyDataType,
    ConfigValue as _ConfigValue,
    EnvConfig as _EnvConfig,
)


from .global_vars import (
    LoggerType,
    show_secured_values as glb_show_secured_values,
    make_secured_values_mutable as glb_make_secured_values_mutable,
)

pyappenv_logger: LoggerType


class PyAppEnv:
    __LOG_LEVELS = ["info", "error", "warning", "debug"]
    __DOTENV_FILE_CONFIGS = {}
    _show_secured_values = False
    _make_secured_values_mutable = True

    def __init__(
        self,
        env_name=None,
        env_configs=None,
        default_env=None,
        application_env_available=False,
        override_from_application_env=False,
        logger=None,
        log_levels=None,
        dotenv_file=None,
        print_logs=True,
        log_exceptions=True,
        show_secured_values=False,
        make_secured_values_mutable=True,
        use_validators_for_env=True,
    ):
        log_levels = log_levels or self.__LOG_LEVELS
        self.load_logger(logger, print_logs, log_levels, log_exceptions)

        self.dotenv_file = dotenv_file
        self.application_env_available = application_env_available
        self.use_validators_for_env = use_validators_for_env
        self.set_secured_values(show_secured_values)
        self.set_secured_mutable(make_secured_values_mutable)
        self.override_from_application_env = override_from_application_env

        self.__env_name = env_name
        self.load_env_from_dotfile()
        self.default_env = default_env or self.__env_name
        self.env_configs = env_configs
        self.env = None

        self.env_name = self.set_env()
        self.load_all_env()

    def load_env_from_dotfile(self):
        if not self.dotenv_file:
            return

        if isinstance(self.dotenv_file, str) and not os.path.exists(self.dotenv_file):
            raise FileNotFoundError(f"Environment file not found: {self.dotenv_file}")

        # make a copy of the current environment variables
        env_copy = os.environ.copy()
        load_dotenv(dotenv_path=self.dotenv_file)

        # get the new environment variables
        new_env = {}

        for key, value in os.environ.items():
            if key not in env_copy or env_copy[key] != value:
                new_env[key] = value

        # restore the original environment variables
        os.environ.clear()
        os.environ.update(env_copy)

        self.__DOTENV_FILE_CONFIGS = new_env
        # load the environment variables into the config file.
        self.logger.info(f"Environment loaded from file: {self.dotenv_file}")

    def set_env(self):
        # validate env is a sting
        env = self.__env_name
        if not env:
            env = self.default_env

        if not self.env_configs:
            self.env_configs = {}

        if env and not isinstance(env, str):
            raise exceptions.InvalidEnvironmentConfigError("Environment must be a string.")

        # check if env_configs is of type dict
        if self.env_configs and not isinstance(self.env_configs, dict):
            raise exceptions.InvalidEnvironmentConfigError("Environment configs must be a dictionary.")

        # check env is available in env_configs
        if self.env_configs and env not in self.env_configs:
            temp_list = map(lambda x: '"{}"'.format(x), list(self.env_configs.keys()))
            raise exceptions.InvalidEnvironmentConfigError(
                f"Environment '{env}' not available in env_configs. Please select from available environment :- {', '.join(temp_list)}."
            )

        if env:
            self.logger.info("Config loaded from application code.")
            return env

        env = os.getenv("ENV", None)
        if env:
            self.logger.info("Config loaded from environment file.")
            return env

        env = os.getenv("ENV", None)

        if env:
            self.logger.info("Config loaded from environment file.")
            return env

        self.logger.warning("Environment not defined in application. Falling back to default application setting.")
        env = self.default_env
        self.logger.info(f"Default environment: {self.default_env} will be used.")

        if not env:
            raise exceptions.InvalidEnvironmentConfigError("Environment not defined in application or code.")
        return env

    def load_logger(self, logger, print_logs, log_levels, log_exceptions):
        if not logger:
            if print_logs:
                self.logger = _DefaultLogger()
            else:
                self.logger = _NoLogger()

        # make logger as a global variable
        builtins.pyappenv_logger = self.logger

        # check if logger is an object and has the required methods which defines various log levels.
        for log_level in log_levels:
            if not (hasattr(self.logger, log_level) and callable(getattr(self.logger, log_level))):
                raise exceptions.InvalidEnvironmentConfigError(
                    f'Logger must have a method called "{log_level}" or pass the log_levels parameter.'
                )

        self.override_exceptions_for_logging(log_exceptions)

    def load_all_env(self):
        """Load all the environment values from the environment config"""
        self.validate_parameters()
        self.load_dotenv_values()
        self.load_config()

    def validate_parameters(self):

        if self.env_configs and not isinstance(self.env_configs, dict):
            raise exceptions.InvalidEnvironmentConfigError("Environment configs must be a dictionary.")

        if (self.default_env and not isinstance(self.default_env, str)) or (
            self.env_configs and self.default_env not in self.env_configs
        ):
            raise exceptions.InvalidEnvironmentConfigError(
                'Default environment must be a string and available in "env_configs".'
            )

        for env_name, env_obj in self.env_configs.items():
            obj_type = "dict" if isinstance(env_obj, dict) else None
            obj_type = "class" if callable(env_obj) else obj_type
            obj_type = "instance" if isinstance(env_obj, _BaseEnvironment) else obj_type

            if obj_type is None:
                raise exceptions.InvalidEnvironmentConfigError(
                    f"Environment config for '{env_name}' must be a dictionary, class or an instance of BaseEnvironment. Import from classes.py"
                )

            # validate if is a class, and is derived from BaseEnvironment
            elif obj_type == "class" and not _BaseEnvironment in env_obj.__bases__:
                raise exceptions.InvalidEnvironmentConfigError(
                    f"Environment config for '{env_name}' must be a subclass of BaseEnvironment. Import from classes.py"
                )

            # validate if is an instance of BaseEnvironment
            elif obj_type == "instance" and not isinstance(env_obj, _BaseEnvironment):
                raise exceptions.InvalidEnvironmentConfigError(
                    f"Environment config for '{env_name}' must be an instance of BaseEnvironment. Import from classes.py"
                )

            # initalize the class if obj_type with default values
            elif obj_type == "class":
                env_obj = env_obj()

            # obj_type is dict, convert to BaseEnvironment
            elif obj_type == "dict":
                # assert all the keys of dictionary are immutable objects
                for key in env_obj.keys():
                    if not isinstance(key, str):
                        raise exceptions.InvalidEnvironmentConfigError(
                            f"Error in config for '{env_name}' with key '{key}' of type '{type(key)}'. Keys must be of type string."
                        )
                
                env_obj = _BaseEnvironment(env_obj)
            self.env_configs[env_name] = env_obj

    def load_config(self):
        for env_name, env_obj in self.env_configs.items():
            # check for forbidden keys in the environment config
            try:
                getattr(self, env_name)
                raise exceptions.InvalidEnvironmentConfigError(
                    f"Environment config name '{env_name}' is a forbidden key. Please use a different key."
                )
            except Exception as ex:
                if isinstance(ex, exceptions.InvalidEnvironmentConfigError):
                    raise ex
                pass
            
            # convert all values to ConfigValue
            env_obj._init_from_PyEnv()
            self.env_configs[env_name] = env_obj
            setattr(self, env_name, env_obj.config)

        self.env = self.env_configs[self.env_name].config
        self.logger.info(f"Environment config for {self.env_name} is available in PyAppEnv.")



    def load_dotenv_values(self):
        # get dotenv values
        environ_values = self.__DOTENV_FILE_CONFIGS

        # get the os environment values
        os_env = {}
        if self.application_env_available:
            os_env = os.environ

        # let the values be overridden from the application environment
        if self.override_from_application_env:
            environ_values = {**os.environ, **environ_values}

        for env_name in self.env_configs:
            updated_env_values = {}
            default_validators = None if self.use_validators_for_env else _AnyDataType()

            for env_key, env_value in environ_values.items():
                if env_key in self.env_configs[env_name]:
                    old_value = self.env_configs[env_name][env_key].value
                    self.update_config(env_name, env_key, env_value, default_validators)
                    if old_value != env_value:
                        updated_env_values[env_key] = env_value

            if updated_env_values:
                self.logger.info(f"Environment values updated from shell or '.env' file.")
                for key, value in updated_env_values.items():
                    self.logger.info(
                        f" - Using {value} instead of {self.env_configs[env_name][key].value} for {key} in Environment {env_name}."
                    )

    def update_config(self, env_name, key, value, validator=None):
        validator = (
            validator
            or (self.env[key].value_validator if (hasattr(self.env.get(key, None), "value_validator")) else None)
            or _AnyDataType()
        )

        if not isinstance(validator, _BaseDataType):
            raise exceptions.InvalidEnvironmentConfigError(
                f"Environment validator for {key} must be a subclass of BaseDataType.\nImport from classes.py"
            )

        try:
            validator.__set_value__(value)
        except Exception as e:
            raise Exception(f"Error setting value for {key}. {e}")
        self.env_configs[env_name].config[key] = value
        self.env_configs[env_name].validator[key] = validator


    def override_exceptions_for_logging(self, log_exceptions):
        if not log_exceptions:
            return

        def handle_exception(exc_type, exc_value, exc_traceback):
            if pyappenv_logger and isinstance(pyappenv_logger, object):
                pyappenv_logger.error(f"{exc_type.__name__} Error: {exc_value}")
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Set the global exception hook
        sys.excepthook = handle_exception

    @property
    def show_secured_values(self):
        return self._show_secured_values

    @show_secured_values.setter
    def show_secured_values(self, value):
        if hasattr(self, "_show_secured_values") and self._show_secured_values is not None:
            raise exceptions.ImmutableError("show_secured_values can only be initalized once.")

        if not isinstance(value, bool):
            raise TypeError("show_secured_values must be a boolean.")

        self.set_secured_values(value)

    def set_secured_values(self, value):
        self._show_secured_values = value
        glb_show_secured_values.value = value

    @property
    def make_secured_values_mutable(self):
        return self._make_secured_values_mutable

    @make_secured_values_mutable.setter
    def make_secured_values_mutable(self, value):
        if hasattr(self, "_make_secured_values_mutable") and self._make_secured_values_mutable is not None:
            raise exceptions.ImmutableError("make_secured_values_mutable can only be initalized once.")

        if not isinstance(value, bool):
            raise TypeError("make_secured_values_mutable must be a boolean.")

        self.set_secured_mutable(value)

    def set_secured_mutable(self, value):
        self._make_secured_values_mutable = value
        glb_make_secured_values_mutable.value = value