from tree_sitter import Node
from typing import Optional, Any

import re
from Interpreter import Interpreter

def extract_send_content(text):
    start = text.find('Send(')
    if start == -1:
        return None
    i = start + len('Send(')
    depth = 1
    content = []
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                break
        content.append(text[i])
        i += 1
    return ''.join(content).strip() if depth == 0 else None

def extract_method_argument(content: str, method_name: str) -> Optional[str]:
    """
    Extract the argument from a method call using balanced parentheses parsing.
    Handles nested parentheses correctly.
    
    Args:
        content: The content to search in
        method_name: The method name (e.g., 'Get', 'Post', etc.)
    
    Returns:
        The argument string if found, None otherwise
    """
    try:
        # Find the method name
        method_pattern = rf'\b{re.escape(method_name)}\s*'
        match = re.search(method_pattern, content, re.IGNORECASE)
        if not match:
            return None
        
        # Find the opening parenthesis after the method name
        start_pos = match.end()
        while start_pos < len(content) and content[start_pos].isspace():
            start_pos += 1
        
        # Check for generic type parameters
        if start_pos < len(content) and content[start_pos] == '<':
            # Skip generic type parameters
            depth = 1
            start_pos += 1
            while start_pos < len(content) and depth > 0:
                if content[start_pos] == '<':
                    depth += 1
                elif content[start_pos] == '>':
                    depth -= 1
                start_pos += 1
            # Skip whitespace after generic type
            while start_pos < len(content) and content[start_pos].isspace():
                start_pos += 1
        
        # Check for opening parenthesis
        if start_pos >= len(content) or content[start_pos] != '(':
            return None
        
        # Extract argument using balanced parentheses
        start_pos += 1  # Skip opening parenthesis
        depth = 1
        arg_start = start_pos
        arg_content = []
        
        while start_pos < len(content) and depth > 0:
            if content[start_pos] == '(':
                depth += 1
            elif content[start_pos] == ')':
                depth -= 1
                if depth == 0:
                    break
            arg_content.append(content[start_pos])
            start_pos += 1
        
        if depth == 0:
            return ''.join(arg_content).strip()
        else:
            return None
            
    except Exception as e:
        print(f"Debug: Error extracting method argument: {e}")
        return None

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
        self.verify_count_after = 0  # Number of Verify statements after this Send
        self.expected_code: Any = None  # Expected response code after this Send
        # Parse the Send function
        self._parse_send_function()
    
    def _parse_send_function(self):
        """Parse the Send function to extract REQUEST_TYPE and PATH, handling 'with { ... }' blocks."""
        try:
            # Get the text of the Send function call
            self.raw_text = self.source_bytes[self.node.start_byte:self.node.end_byte].decode()
            
            # Remove any trailing 'with { ... }' block for parsing
            cleaned_text = re.sub(r'with\s*\{[^}]*\}\s*;?$', '', self.raw_text, flags=re.DOTALL).strip()
            
            # Extract the argument inside Send(...)
            inner_content = extract_send_content(cleaned_text)
            if not inner_content:
                return
            # Remove any trailing 'with { ... }' block from the inner_content
            cleaned_inner_content = re.sub(r'with\s*\{[^}]*\}\s*$', '', inner_content, flags=re.DOTALL).strip()
            
            # Try new style first: Get(path), Post(obj).To(path), etc.
            if self._parse_new_style(cleaned_inner_content):
                pass
            else:
                # Fallback to old style
                self._parse_request_type(cleaned_inner_content)
                self._parse_path(cleaned_inner_content)

            # Evaluate the path if possible
            if self.path and self.environment is not None:
                try:
                    # Use Interpreter.evaluate to resolve the path
                    self.evaluated_path = Interpreter.evaluate(None, self.path, self.environment)
                    # Strip quotes if present
                    if (isinstance(self.evaluated_path, str) and self.evaluated_path.startswith('"') and self.evaluated_path.endswith('"')):
                        self.evaluated_path = self.evaluated_path[1:-1]
                except Exception as e:
                    self.evaluated_path = self.path
        except Exception as e:
            print(f"Debug: Error parsing Send function: {e}")

    def _parse_new_style(self, content: str) -> bool:
        """Try to parse new style: Get(path), Post(obj).To(path), etc. Returns True if successful."""
        try:
            # Try to match HTTP methods: Get, Post, Put, Delete, Patch
            method_names = ['Get', 'Post', 'Put', 'Delete', 'Patch']
            
            for method_name in method_names:
                # First, check if this method exists in the content
                if re.search(rf'\b{re.escape(method_name)}\s*[<(]', content, re.IGNORECASE):
                    # Extract the argument using balanced parentheses parser
                    arg = extract_method_argument(content, method_name)
                    if arg is not None:
                        self.request_type = method_name.upper()
                        
                        # Remove any trailing 'with { ... }' block from the argument
                        cleaned_arg = re.sub(r'with\s*\{[^}]*\}\s*$', '', arg, flags=re.DOTALL).strip()
                        
                        # For Get(path), path is the argument
                        if self.request_type == 'GET':
                            self.path = cleaned_arg
                            return True
                        
                        # For Delete(path), Patch(data), etc., check if .To(path) is present
                        # If .To(path) is present, use old style
                        if re.search(r'\.To\s*\(', content):
                            return False
                        
                        # For Post(obj), Put(obj), Patch(data), etc., path may not be present directly
                        # But for new style, if argument looks like a path, use it
                        if self.request_type in ['DELETE', 'PATCH', 'PUT', 'POST']:
                            self.path = cleaned_arg
                            return True
            
            return False
        except Exception as e:
            print(f"Debug: Error parsing new style: {e}")
            return False
    
    def _parse_request_type(self, content: str):
        """Extract the request type (Post/Put/Get) from the content"""
        try:
            # Look for Post(...), Put(...), or Get(...)
            # Handle both single-line and multi-line patterns
            # Also handle generic types like Post<List<Recipient>>
            # Use a simpler approach - just look for the HTTP method name
            request_match = re.match(r'(Post|Put|Get|Delete|Patch)', content.strip(), re.IGNORECASE)
            if request_match:
                self.request_type = request_match.group(1).upper()
            else:
                pass
                # print(f"Debug: Could not find request type in: {content}")
        except Exception as e:
            print(f"Debug: Error parsing request type: {e}")
    
    def _parse_path(self, content: str):
        """Extract the path from To() argument"""
        try:
            # Look for .To(...) and extract the argument using balanced parentheses parsing
            to_start = content.find('.To(')
            if to_start != -1:
                start_pos = to_start + 4
                depth = 1
                path_content = []
                
                while start_pos < len(content) and depth > 0:
                    if content[start_pos] == '(':
                        depth += 1
                    elif content[start_pos] == ')':
                        depth -= 1
                        if depth == 0:
                            break
                    path_content.append(content[start_pos])
                    start_pos += 1
                
                if depth == 0:
                    path_arg = ''.join(path_content).strip()
                    # Clean up the path argument (remove extra whitespace, newlines)
                    path_arg = re.sub(r'\s+', ' ', path_arg)
                    self.path = path_arg
                    return
            
            # Fallback to regex for simpler cases
            to_match = re.search(r'\.\s*To\s*\(\s*([^)]+(?:\([^)]*\)[^)]*)*)\s*\)', content, re.DOTALL)
            if to_match:
                path_arg = to_match.group(1).strip()
                # Clean up the path argument (remove extra whitespace, newlines)
                path_arg = re.sub(r'\s+', ' ', path_arg)
                self.path = path_arg
            else:
                pass
                # print(f"Debug: Could not find To() argument in: {content}")
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