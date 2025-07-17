import os
import re
import glob
from cs import CSFile, CSClass, CSMethod
from special_nodes import Send
from helper import create_globals, globals, PathResolver, paths
from Environment import Environment

class SwaggerAdder:
    def __init__(self, cs_dir: str):
        self.start_at = cs_dir
        self.path_resolver = PathResolver(paths)

    def process_all(self, start_at: str | None = None):
        if start_at is None:
            start_at = self.start_at

        if os.path.isfile(start_at):
            return self.process_file(start_at)
        
        for entry in os.listdir(start_at):
            self.process_all(os.path.join(self.start_at, entry))

    def process_file(self, file_path):
        print(f"Processing file: {file_path}")

        line_changes: list[list[str]] = []
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        env = create_globals(globals)
        environment = Environment(env)
        cs_file = CSFile(source, environment)
        lines = source.split('\n')
        changes = []
        for csharp_class in cs_file.get_classes():
            if not self.is_api_test_class(csharp_class):
                continue

            for method in csharp_class.get_test_methods():
                if self.has_swagger_attribute(method):
                    continue

                send_obj = self.select_best_send(method, method.name)
                if not send_obj:
                    print("NO SEND OBJECT FOUND FOR METHOD", method.name)                
                    continue
                    
                path_var = self.path_resolver.get_var_for_path(str(send_obj.evaluated_path))

                op_type = send_obj.get_request_type()
                resp_code = send_obj.expected_code
                swagger_attr = f"[Swagger(Path = Paths.{path_var}, Operation = OperationType.{op_type}, ResponseCode = {resp_code})]"
                # Insert above method declaration
                method_line = self.find_method_declaration_line(lines, method.name)

                assert(method_line is not None)
                # change this
                line_changes.append([method_line, swagger_attr])
                changes.append(f"{method.name}: {swagger_attr}")

        self.insert_swagger_attribute(file_path, line_changes)

        if changes:
            return ('\n'.join(lines), changes)
        return (None, [])


    def insert_swagger_attribute(self, filename: str, changes: list[list[str]]):
        with open(filename, 'r', encoding='utf-8') as f:
            file = f.read()

        for line, attr in changes:
            # Get leading whitespace from the original line
            m = re.match(r"^\s*", line)
            leading_ws = m.group(0) if m else ''
            file = file.replace(line, f"{leading_ws}{attr}\n{line}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(file)


    def is_api_test_class(self, csharp_class: CSClass):
        if 'APITest' in csharp_class.super_class_name:
            return True
        return False

    def is_test_method(self, method):
        return any('[Test]' in str(attr) for attr in getattr(method, 'attributes', []))

    def has_swagger_attribute(self, method):
        return any('Swagger(' in str(attr) for attr in getattr(method, 'attributes', []))

    def find_method_declaration_line(self, lines: list[str], method_name: str) -> str | None:
        for i, line in enumerate(lines):
            if f'public void {method_name}(' in line or f'public async Task {method_name}(' in line:
                return line
        return None

    def select_best_send(self, method: CSMethod, method_name: str) -> Send | None:
        sends = getattr(method, 'send_functions', [])
        if not sends:
            return None
        # Parse operation type and response code from method name
        op_type, resp_code = self.parse_method_name(method_name)
        # Filter sends by op_type and resp_code
        candidates = []
        for send in sends:
            if op_type and resp_code:
                if (send.get_request_type() or '').lower() == op_type.lower() and (str(send.expected_code) or '').lower() == resp_code.lower():
                    candidates.append(send)
            elif op_type:
                if (send.get_request_type() or '').lower() == op_type.lower():
                    candidates.append(send)
            elif resp_code:
                if (str(send.expected_code) or '').lower() == resp_code.lower():
                    candidates.append(send)
        if not candidates:
            candidates = sends
        # Pick the one with most verify_count_after, then latest line number
        candidates.sort(key=lambda s: (s.verify_count_after, s.line_number), reverse=True)
        return candidates[0]

    def parse_method_name(self, method_name):
        # Try to extract operation type and response code from method name
        # e.g. POST_AdminBlacklist_NoAuth_401_106508
        op_type = None
        resp_code = None
        parts = method_name.split('_')
        if parts:
            if parts[0].upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                op_type = parts[0].capitalize()
            # Look for a part that is a number or a known code
            for p in parts:
                if p.isdigit() and len(p) == 3:
                    resp_code = p
                elif p.upper() in ['OK', 'UNAUTHORIZED', 'FORBIDDEN', 'NOTFOUND', 'BADREQUEST', 'CREATED', 'GONE']:
                    resp_code = p.capitalize()
        return op_type, resp_code

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        # start_at = "testfile.cs"
        start_at = "csfiles"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        start_at = os.path.join(current_dir, start_at)
    else:
        start_at = sys.argv[1]
    
    swagger_adder = SwaggerAdder(start_at)

    swagger_adder.process_all()
    
