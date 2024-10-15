from abc import ABC, abstractmethod

class SampleGlobalLogger(ABC):
    @abstractmethod
    def log(self, message):
        ...

    @abstractmethod
    def error(self, message):
        ...
    
    @abstractmethod
    def debug(self, message):
        ...

    @abstractmethod
    def info(self, message):
        ...

    @abstractmethod
    def warning(self, message):
        ...

    @abstractmethod
    def critical(self, message):
        ...

class ShowSecuredValues:
    def __init__(self, value):
        self.value = value
    
    def __bool__(self):
        return self.value
    

class MakeSecuredValuesMutable:
    def __init__(self, value):
        self.value = value
    
    def __bool__(self):
        return self.value

LoggerType = SampleGlobalLogger
show_secured_values = ShowSecuredValues(True)
make_secured_values_mutable = MakeSecuredValuesMutable(False)