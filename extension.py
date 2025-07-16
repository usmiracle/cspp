import os
import re
import glob
from cs import CSFile, CSClass, CSMethod
from special_nodes import Send
from helper import create_globals, globals, PathResolver, paths
from Environment import Environment

class SwaggerAdder:
    def __init__(self, cs_dir):
        self.cs_dir = cs_dir
        self.path_resolver = PathResolver(paths)

    def process_all(self):
        cs_files = glob.glob(f"{self.cs_dir}/**/*.cs", recursive=True)
        summary = []
        for cs_file in cs_files:
            updated, changes = self.process_file(cs_file)
            if updated:
                with open(cs_file, 'w', encoding='utf-8') as f:
                    print(f"Writing to {cs_file}")
                    f.write(updated)
                summary.append((cs_file, changes))
        print("\nSwagger attribute insertion summary:")
        for fname, changes in summary:
            print(f"{fname}: {len(changes)} Swagger attributes added")
            for c in changes:
                print(f"  - {c}")

    def process_file(self, file_path):
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
            class_env = csharp_class.get_class_environment()
            for method_name, method in class_env.callables.items():
                if not isinstance(method, CSMethod):
                    continue
                if not self.is_test_method(method):
                    continue
                if self.has_swagger_attribute(method):
                    continue
                # Find best Send node for this method
                send_obj = self.select_best_send(method, method_name)
                if not send_obj:
                    continue
                # Build Swagger attribute
                path_var = self.path_resolver.get_var_for_path(str(send_obj.evaluated_path)) or "Unknown"
                op_type = send_obj.get_request_type() or "Unknown"
                resp_code = send_obj.expected_code or "Unknown"
                swagger_attr = f"[Swagger(Path = Paths.{path_var}, Operation = OperationType.{op_type}, ResponseCode = {resp_code})]"
                # Insert above method declaration
                method_line = self.find_method_declaration_line(lines, method_name)
                if method_line is not None:
                    lines.insert(method_line, swagger_attr)
                    changes.append(f"{method_name}: {swagger_attr}")
        if changes:
            return ('\n'.join(lines), changes)
        return (None, [])

    def is_api_test_class(self, csharp_class):
        return csharp_class.name.endswith('APITest') or 'APITest' in str(csharp_class.attributes)

    def is_test_method(self, method):
        return any('[Test]' in str(attr) for attr in getattr(method, 'attributes', []))

    def has_swagger_attribute(self, method):
        return any('Swagger(' in str(attr) for attr in getattr(method, 'attributes', []))

    def find_method_declaration_line(self, lines, method_name):
        for i, line in enumerate(lines):
            if f'public void {method_name}(' in line or f'public async Task {method_name}(' in line:
                return i
        return None

    def select_best_send(self, method, method_name):
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
        print("Usage: python extension.py <file_or_folder_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    if os.path.isfile(path):
        # Process single file
        swagger_adder = SwaggerAdder(os.path.dirname(path) or ".")
        updated, changes = swagger_adder.process_file(path)
        if updated:
            with open(path, 'w', encoding='utf-8') as f:
                print(f"Writing to {path}")
                f.write(updated)
            print(f"\nSwagger attribute insertion summary:")
            print(f"{path}: {len(changes)} Swagger attributes added")
            for c in changes:
                print(f"  - {c}")
        else:
            print(f"No changes needed for {path}")
    else:
        # Process directory
        SwaggerAdder(path).process_all()
    
