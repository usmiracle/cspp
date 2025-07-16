from __future__ import annotations
from typing import Any

class Variable:
    def __init__(self, name: str, _type: str):
        # name is the name of the variable
        # _type could be a string, int, float, bool, or any other type
        self.name = name
        self._type = _type

class Callable(Variable):
    def __init__(self, name: str, _type: str, arity: int):
        # arity is the number of arguments the method takes
        # _type could be method
        super().__init__(name, _type)
        self.arity = arity

    def call(self, interpreter: Any, arguments: list[Any]):
        from Interpreter import Interpreter
        assert(isinstance(interpreter, Interpreter))

        # Base implementation - subclasses should override this
        raise NotImplementedError(f"Call method not implemented for {self.__class__.__name__}")


class ExpressionBioledMethod(Callable):
    def __init__(self, name: str, _type: str, arity: int, expression_body: str, parameter_names: list[str]):
        super().__init__(name, _type, arity)
        self.expression_body = expression_body
        self.parameter_names = parameter_names

    def call(self, interpreter: Any, arguments: list[Any]):
        from Interpreter import Interpreter
        from Environment import Environment
        assert(isinstance(interpreter, Interpreter))

        # Create a temporary environment for this method call
        # This allows us to bind the arguments to parameter names
        temp_environment = Environment(interpreter.environment)
        
        # Bind arguments to parameter names
        for i, param_name in enumerate(self.parameter_names):
            if i < len(arguments):
                temp_environment.define_variable(param_name, arguments[i])
        
        # Evaluate the expression body in the temporary environment
        result = Interpreter.evaluate(None, self.expression_body, temp_environment)
        
        return result

    pass