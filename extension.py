import re
from cs import CSFile
from Environment import Environment
from main import create_globals, globals

class CSharpTestAutomation:
    """
    Automates the process of adding Swagger attributes to test methods.
    """
    
    def __init__(self):
        self.path_to_var = {
            # Placeholder dictionary - keys are paths, values are strings
            # This would be populated with actual path mappings
            "gl-share/api/Admin/share": "AdminShare",
            "gl-share/api/Admin/share/{shareLink}/recipients": "AdminShareRecipients",
            "api/users": "Users",
            "api/users/123": "UsersById",
            "api/users/456": "UsersDelete",
            "api/users/789": "UsersPatch"
        }
    
    def get_swagger_attribute(self, send_obj):
        """
        Generate Swagger attribute based on Send object.
        Format: [Swagger(Path=Paths.{path_to_var[path]}, Operation=OperationType.{request_type})]
        """
        path = send_obj.get_evaluated_path()
        request_type = send_obj.get_request_type()
        
        # Get the path variable name from the dictionary
        path_var = self.path_to_var.get(path, "Unknown")
        
        return f'[Swagger(Path = Paths.{path_var}, Operation = OperationType.{request_type})]'
    
    def has_swagger_attribute(self, method_attributes):
        """
        Check if method already has a Swagger attribute.
        """
        for attr in method_attributes:
            if 'Swagger(' in attr:
                return True
        return False
    
    def is_test_method(self, method_attributes):
        """
        Check if method has Test attribute.
        """
        for attr in method_attributes:
            if '[Test]' in attr:
                return True
        return False
    
    def is_api_test_class(self, class_attributes, class_name):
        """
        Check if class inherits from APITest.
        """
        # Check if class name ends with APITest or has APITest in base class
        return class_name.endswith('APITest') or 'APITest' in str(class_attributes)
    
    def process_file(self, source_code: str) -> str:
        """
        Process a C# file and return the updated source code with Swagger attributes added.
        """
        # Create environment and parse the file
        env = create_globals(globals)
        environment = Environment(env)
        cs_file = CSFile(source_code, environment)
        
        # Get the source lines for modification
        lines = source_code.split('\n')
        
        # Track changes to make
        changes = []
        
        # Process each class
        for csharp_class in cs_file.get_classes():
            class_env = csharp_class.get_class_environment()
            
            # Check if this is an APITest class
            if not self.is_api_test_class(csharp_class.attributes, csharp_class.name):
                continue
            
            # Process each method in the class
            for method_name, method in class_env.callables.items():
                if not hasattr(method, 'attributes'):
                    continue
                
                # Check if it's a test method
                if not self.is_test_method(method.attributes):
                    continue
                
                # Check if it already has Swagger attribute
                if self.has_swagger_attribute(method.attributes):
                    continue
                
                # Find Send functions in the method
                if hasattr(method, 'send_functions') and method.send_functions:
                    # Use the first Send function to generate Swagger attribute
                    send_obj = method.send_functions[0]
                    swagger_attr = self.get_swagger_attribute(send_obj)
                    
                    # Find the method declaration line
                    method_line = self.find_method_declaration_line(lines, method_name)
                    if method_line is not None:
                        changes.append((method_line, swagger_attr))
        
        # Apply changes in reverse order to maintain line numbers
        changes.sort(reverse=True)
        for line_num, swagger_attr in changes:
            lines.insert(line_num, swagger_attr)
        
        return '\n'.join(lines)
    
    def find_method_declaration_line(self, lines, method_name):
        """
        Find the line number where the method declaration starts.
        """
        for i, line in enumerate(lines):
            if f'public void {method_name}(' in line or f'public async Task {method_name}(' in line:
                return i
        return None

def main():
    """
    Main function to test the automation with test1.cs
    """
    automation = CSharpTestAutomation()
    
    file_name = 'test2.cs'
    # Read test2.cs
    with open(file_name, 'r') as f:
        source_code = f.read()
    
    # Process the file
    updated_source = automation.process_file(source_code)
    
    # Write the updated file
    with open('updated_test2.cs', 'w') as f:
        f.write(updated_source)
    
    print("Processing complete!")
    print(f"Original file: {file_name}")
    print("Updated file: updated_test2.cs")
    
    # Test the output by parsing the updated file
    print("\nTesting the updated file...")
    env = create_globals(globals)
    environment = Environment(env)
    updated_cs_file = CSFile(updated_source, environment)
    
    print("\nUpdated file analysis:")
    for csharp_class in updated_cs_file.get_classes():
        print(f"\nClass: {csharp_class.name}")
        class_env = csharp_class.get_class_environment()
        print(f"  Variables: {class_env.values}")
        print(f"  Methods:")
        for method_name, method in class_env.callables.items():
            if hasattr(method, 'attributes'):
                print(f"    {method_name}: {method.attributes}")
                if hasattr(method, 'send_functions') and method.send_functions:
                    print(f"      Send functions: {method.send_functions}")

if __name__ == "__main__":
    main() 