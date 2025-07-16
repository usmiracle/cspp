import re

from Environment import Environment
from Types import Callable, ExpressionBioledMethod
from tree_sitter import Tree, Node

class Interpreter:
    """
    A class that interprets a C# file.
    Intakes a Environment object that contains the global variables and methods.
    Intakes a file path and parses the file into a tree.
    """
    def __init__(self, globals: Environment):
        self.globals = globals
        self.environment = globals

    @staticmethod
    def evaluate(node: Node | None, expression: str, environment: Environment) -> str:
        if not expression or not expression.strip():
            return ""
        
        expression = expression.strip()

        # Handle string interpolation: $"Hello {name}!"
        if expression.startswith('$"') and expression.endswith('"'):
            return Interpreter._resolve_string_interpolation(expression, environment)
        
        # Handle function/method call: Foo("bar") or Foo(a, "bar")
        func_call_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', expression)
        if func_call_match:
            method_name = func_call_match.group(1)
            args_string = func_call_match.group(2)
            
            # Parse and evaluate arguments
            args = Interpreter._parse_method_arguments(args_string, environment)
            
            # Get the method
            method = Interpreter._resolve_method_reference(method_name, environment)
            
            if method:
                # Call the method with evaluated arguments
                return Interpreter._call_method(method, args, environment)
            else:
                # If method not found, return the original expression
                return expression

        # Handle string concatenation: "abc" + "def" or a + "def"
        if '+' in expression:
            return Interpreter._resolve_string_concatenation(expression, environment)
        
        # Handle simple variable reference: a
        if Interpreter._is_simple_identifier(expression):
            return Interpreter._resolve_variable_reference(expression, environment)
        
        # Handle string literals: "Hello"
        if expression.startswith('"') and expression.endswith('"'):
            return expression
        
        # Handle numeric literals: 123
        if expression.isdigit():
            return expression
        
        # Handle boolean literals
        if expression.lower() in ['true', 'false']:
            return expression.lower()
        
        return expression

    @staticmethod
    def _parse_method_arguments(args_string: str, environment: Environment) -> list:
        """Parse method arguments string and evaluate each argument"""
        if not args_string.strip():
            return []
        
        args = []
        current_arg = ""
        paren_depth = 0
        quote_char = None
        
        for char in args_string:
            if char == '"' and quote_char != "'":
                if quote_char == '"':
                    quote_char = None
                else:
                    quote_char = '"'
                current_arg += char
            elif char == "'" and quote_char != '"':
                if quote_char == "'":
                    quote_char = None
                else:
                    quote_char = "'"
                current_arg += char
            elif char == '(' and not quote_char:
                paren_depth += 1
                current_arg += char
            elif char == ')' and not quote_char:
                paren_depth -= 1
                current_arg += char
            elif char == ',' and paren_depth == 0 and not quote_char:
                # End of argument
                arg_value = Interpreter.evaluate(None, current_arg.strip(), environment)
                args.append(arg_value)
                current_arg = ""
            else:
                current_arg += char
        
        # Add the last argument
        if current_arg.strip():
            arg_value = Interpreter.evaluate(None, current_arg.strip(), environment)
            args.append(arg_value)
        
        return args

    @staticmethod
    def _call_method(method: Callable, args: list, environment: Environment) -> str:
        """Call a method with the given arguments"""
        try:
            # Create a temporary interpreter instance for method calls
            temp_interpreter = Interpreter(environment)
            
            # Call the method
            result = method.call(temp_interpreter, args)
            return result
        except Exception as e:
            return f'"{method.name}({", ".join(args)})"'

    @staticmethod
    def _resolve_string_interpolation(expression: str, environment: Environment) -> str:
        """Resolve string interpolation like $"Hello {name}!" """
        # Remove the $ and outer quotes
        content = expression[2:-1]
        
        # Find all interpolation expressions {variable}
        pattern = r'\{([^}]+)\}'
        
        def replace_interpolation(match):
            expr = match.group(1).strip()
            value = Interpreter.evaluate(None, expr, environment)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
        
        result = re.sub(pattern, replace_interpolation, content)
        return f'"{result}"'
    
    @staticmethod
    def _resolve_string_concatenation(expression: str, environment: Environment) -> str:
        """Resolve string concatenation like "abc" + "def" or a + "def" """
        parts = expression.split('+')
        resolved_parts = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Resolve each part
            resolved_part = Interpreter.evaluate(None, part, environment)
            # Remove quotes if it's a string literal
            if resolved_part.startswith('"') and resolved_part.endswith('"'):
                resolved_part = resolved_part[1:-1]
            resolved_parts.append(resolved_part)
        
        # Join all parts and wrap in quotes
        result = ''.join(resolved_parts)
        return f'"{result}"'

    @staticmethod
    def _resolve_variable_reference(var_name: str, environment: Environment) -> str:
        """Resolve a variable reference to its value"""
        try:
            value = environment.get_variable(var_name)
            if value is not None:
                return str(value)
            return f'"{var_name}"'  # Return variable name in quotes if not found
        except:
            return f'"{var_name}"'  # Return variable name in quotes if error
        
    
    @staticmethod
    def _resolve_method_reference(method_name: str, environment: Environment) -> Callable:
        """Resolve a method reference to its value"""
        return environment.get_method(method_name)
    
    @staticmethod
    def _is_simple_identifier(expression: str) -> bool:
        """Check if expression is a simple identifier (variable name)"""
        # Simple check: no spaces, no special characters except underscore
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', expression))

    def interpret(self, tree: Tree):
        pass
