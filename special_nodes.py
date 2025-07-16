from tree_sitter import Node
from typing import Optional

import re
from Interpreter import Interpreter

class Send:
    """
    A class that represents a C# Send function call.
    Parses Send(Post(...).To(...)) or Send(Put(...).To(...)) or Send(Get().To(...))
    and extracts the REQUEST_TYPE and PATH.
    """
    
    def __init__(self, node: Node, source_bytes: bytes, environment=None):
        self.node = node
        self.source_bytes = source_bytes
        self.environment = environment
        self.request_type = None  # POST, PUT, GET
        self.path = None  # The argument to To()
        self.evaluated_path = None  # The evaluated path using the environment
        self.raw_text = None  # Store the raw text for debugging
        self.line_number = node.start_point[0] + 1  # 1-based line number
        # Parse the Send function
        self._parse_send_function()
    
    def _parse_send_function(self):
        """Parse the Send function to extract REQUEST_TYPE and PATH"""
        try:
            # Get the text of the Send function call
            self.raw_text = self.source_bytes[self.node.start_byte:self.node.end_byte].decode()
            print(f"Debug: Parsing Send function: {self.raw_text} (line {self.line_number})")
            
            # Extract the argument inside Send(...)
            # Match Send(...) and extract the inner content
            send_match = re.match(r'Send\s*\(\s*(.+)\s*\)', self.raw_text, re.DOTALL)
            if not send_match:
                print(f"Debug: Could not parse Send function: {self.raw_text}")
                return
            
            inner_content = send_match.group(1).strip()
            print(f"Debug: Inner content: {inner_content}")
            
            # Parse the request type (Post/Put/Get)
            self._parse_request_type(inner_content)
            
            # Parse the path from To()
            self._parse_path(inner_content)
            # Evaluate the path if possible
            if self.path and self.environment is not None:
                try:
                    # Use Interpreter.evaluate to resolve the path
                    self.evaluated_path = Interpreter.evaluate(None, self.path, self.environment)
                    # Strip quotes if present
                    if (isinstance(self.evaluated_path, str) and self.evaluated_path.startswith('"') and self.evaluated_path.endswith('"')):
                        self.evaluated_path = self.evaluated_path[1:-1]
                    print(f"Debug: Final evaluated path: {self.evaluated_path}")
                except Exception as e:
                    print(f"Debug: Error evaluating path: {e}")
                    self.evaluated_path = self.path
        except Exception as e:
            print(f"Debug: Error parsing Send function: {e}")
    
    def _parse_request_type(self, content: str):
        """Extract the request type (Post/Put/Get) from the content"""
        try:
            # Look for Post(...), Put(...), or Get(...)
            # Handle both single-line and multi-line patterns
            request_match = re.match(r'(Post|Put|Get|Delete|Patch)\s*\(', content, re.IGNORECASE)
            if request_match:
                self.request_type = request_match.group(1).upper()
                print(f"Debug: Found request type: {self.request_type}")
            else:
                print(f"Debug: Could not find request type in: {content}")
        except Exception as e:
            print(f"Debug: Error parsing request type: {e}")
    
    def _parse_path(self, content: str):
        """Extract the path from To() argument"""
        try:
            # Look for .To(...) and extract the argument
            # Handle multi-line patterns and complex arguments
            to_match = re.search(r'\.\s*To\s*\(\s*([^)]+(?:\([^)]*\)[^)]*)*)\s*\)', content, re.DOTALL)
            if to_match:
                path_arg = to_match.group(1).strip()
                # Clean up the path argument (remove extra whitespace, newlines)
                path_arg = re.sub(r'\s+', ' ', path_arg)
                self.path = path_arg
                print(f"Debug: Found path: {self.path}")
            else:
                print(f"Debug: Could not find To() argument in: {content}")
        except Exception as e:
            print(f"Debug: Error parsing path: {e}")
    
    def get_request_type(self) -> Optional[str]:
        """Get the request type (POST, PUT, GET, DELETE, PATCH)"""
        return self.request_type
    
    def get_path(self) -> Optional[str]:
        """Get the path argument from To()"""
        return self.path
    def get_evaluated_path(self) -> Optional[str]:
        """Get the evaluated path argument from To()"""
        return self.evaluated_path
    def get_line_number(self) -> int:
        """Get the 1-based line number where the Send call appears."""
        return self.line_number
    
    def get_raw_text(self) -> Optional[str]:
        """Get the raw text of the Send function call"""
        return self.raw_text
    
    def is_valid(self) -> bool:
        """Check if the Send function was parsed successfully"""
        return self.request_type is not None and self.path is not None
    
    def __str__(self):
        if self.is_valid():
            return f"Send({self.request_type} -> {self.path} | evaluated: {self.evaluated_path} | line: {self.line_number})"
        else:
            return f"Send(INVALID -> {self.raw_text} | line: {self.line_number})"
    
    def __repr__(self):
        return f"Send(request_type='{self.request_type}', path='{self.path}', evaluated_path='{self.evaluated_path}', line={self.line_number}, raw_text='{self.raw_text}')" 