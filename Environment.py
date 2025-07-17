from __future__ import annotations
from typing import Any
from Types import Callable, ExpressionBioledMethod

class Environment:
    """
    A class that represents the environment of a C# file.
    Contains the global variables and methods.
    """
    def __init__(self, enclosing: Environment | None = None):
        self.enclosing = enclosing
        self.values: dict[str, Any] = {}
        self.callables: dict[str, Callable] = {}
        self.classes: dict[str, Callable] = {}

    def define_variable(self, name: str, value: Any):
        self.values[name] = value

    def assign_variable(self, name: str, value: Any):
        if name in self.values:
            self.values[name] = value
        elif self.enclosing is not None:
            self.enclosing.assign_variable(name, value)
        else:
            raise Exception(f"Variable {name} not found")
    
    def get_variable(self, name: str):
        if name in self.values:
            return self.values[name]
        elif self.enclosing is not None:
            return self.enclosing.get_variable(name)
        else:
            raise Exception(f"Variable {name} not found")
    
    def define_method(self, name: str, method: Callable):
        self.callables[name] = method
        if method.arity == 0 and isinstance(method, ExpressionBioledMethod):
            # if the method has no arguments, it is could be seen as a variable
            from Interpreter import Interpreter
            self.define_variable(name, method.call(Interpreter(self), []))

    def get_method(self, name: str):
        if name in self.callables:
            return self.callables[name]
        elif self.enclosing is not None:
            return self.enclosing.get_method(name)
        else:
            raise Exception(f"Method {name} not found")
    
    def define_class(self, name: str, _class: Callable):
        self.classes[name] = _class

    def get_class(self, name: str):
        if name in self.classes:
            return self.classes[name]
        elif self.enclosing is not None:
            return self.enclosing.get_class(name)
        else:
            raise Exception(f"Class {name} not found")