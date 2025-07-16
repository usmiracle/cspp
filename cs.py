import tree_sitter_c_sharp as tscs

from Interpreter import Interpreter
from Types import Callable
from collections.abc import Iterator
from tree_sitter import Language, Parser, Tree, Node
from Environment import Environment


class CSFile:
    """
    A class that represents a C# file.
    Intakes a file path and parses the file into a tree.
    Intakes a Environment object that contains the global variables and methods.
    Read the file and stores the variables and methodsin a Environment object. 
    """
    def __init__(self, source_code: str, environment: Environment):
        self.source = source_code.encode()
        self.language = Language(tscs.language())
        self.parser = Parser(self.language)
        self.tree = self.parser.parse(self.source)
        self.environment = environment
        self.using_directives = []  # Store using directives
        
        # Parse using directives first
        self._parse_using_directives()
        
        # Parse file level declarations
        self._parse_file_level_declarations()
    
    def get_classes(self) -> Iterator['CSClass']:
        """
        Yield all classes in the file, in the order they were added to the environment.
        """
        for value in self.environment.classes.values():
            assert(isinstance(value, CSClass))
            yield value

    def _parse_using_directives(self):
        """Parse using_directive nodes from the compilation unit"""
        root_node = self.tree.root_node
        for child in root_node.children:
            if child.type == "using_directive":
                using_text = self.source[child.start_byte:child.end_byte].decode()
                self.using_directives.append(using_text)
                print(f"Debug: Found using directive: {using_text}")

    def _parse_file_level_declarations(self):
        """
        Parse field_declaration and class_declaration nodes at the file level (compilation_unit) only.
        Do not traverse into class bodies.
        """
        # Only look at direct children of the compilation_unit (file level)
        root_node = self.tree.root_node
        for child in root_node.children:
            if child.type == "field_declaration":
                # File level variables
                self._parse_variable_declaration(child)
            elif child.type == "class_declaration":
                # File level classes
                self._parse_class_declaration(child)

    def _parse_variable_declaration(self, node: Node):
        # private string name = "value";
        # private string name;
        for child in node.children:
            if child.type == "variable_declaration":
                var_type = None
                for decl_child in child.children:
                    if decl_child.type == "predefined_type":
                        var_type = self.source[decl_child.start_byte:decl_child.end_byte].decode().strip()
                    elif decl_child.type == "variable_declarator":
                        var_name = None
                        var_value = ""
                        children = iter(decl_child.children)
                        for item in children:
                            item_text = self.source[item.start_byte:item.end_byte].decode()
                            if item.type == "identifier":
                                var_name = self.source[item.start_byte:item.end_byte].decode()
                            elif item.type == "=":
                                item = next(children)

                                # Get the value after '='
                                value_text = self.source[item.start_byte:item.end_byte].decode()
                                # Remove '=' and whitespace
                                value_text = value_text.lstrip('=').strip()

                                # Evaluate the value using CSEvaluator if needed
                                # private string new_name = "key" + name; // this should be evaluated to get keyvalue
                                # private string another_name = name; // this should be evaluated to get name
                                # private string yet_another_name = "another" + "name"; // this should be evaluated to get anothername
                                # private string yet_another_name_name = $"another{name}"; // this should be evaluated to get anothername
                                
                                # for now, store them as is
                                var_value = Interpreter.evaluate(item, value_text, self.environment)
                        if var_name:
                            # Store the variable in the environment
                            self.environment.define_variable(var_name, var_value)

    
    def _parse_class_declaration(self, node: Node):
        """
        Parse a class_declaration node and add variables to the environment.
        """
        def _extract_class_name(node: Node) -> str:
            for child in node.children:
                if child.type == "identifier" and child.text:
                    return child.text.decode()
            raise Exception(f"Class name not found in {node}")
        
        csharp_class = CSClass(_extract_class_name(node), node, self.source, self.environment)
        self.environment.define_class(csharp_class.name, csharp_class)


    def _traverse(self) -> Iterator[Node]:
        cursor = self.tree.walk()
        reached_root = False
        while not reached_root:
            if cursor.node:
                yield cursor.node

            if cursor.goto_first_child():
                continue

            if cursor.goto_next_sibling():
                continue

            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    retracing = False
                    reached_root = True

                if cursor.goto_next_sibling():
                    retracing = False


class CSClass(Callable):
    """
    A class that represents a C# class.
    Intakes a node, source, and environment.
    """
    def __init__(self, name: str, node: Node, source: bytes, environment: Environment):
        super().__init__(name, "class", 0)

        self.node = node
        self.source = source
        self.environment = environment
        self.class_environment = Environment(environment)  # Class-specific environment
        self.attributes = []  # Store class attributes
        
        # Extract attributes first
        self._extract_attributes()
        
        # Parse class members
        self._parse_class_members()
    
    def _extract_attributes(self):
        """Extract attribute_list nodes from the class declaration"""
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = self.source[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)
                print(f"Debug: Found attribute: {attr_text}")
    
    def _parse_class_members(self):
        """Parse all member_declaration nodes within the class"""
        # Find the class body (member_declaration nodes)
        print(f"Debug: Parsing class {self.name}")
        print(f"Debug: Class node children: {[child.type for child in self.node.children]}")
        
        for child in self.node.children:
            print(f"Debug: Processing child: {child.type}")
            if child.type == "declaration_list":
                print(f"Debug: Found declaration_list")
                self._parse_declaration_list(child)
            elif child.type == "member_declaration":
                print(f"Debug: Found member_declaration")
                self._parse_member_declaration(child)
            elif child.type == "field_declaration":
                print(f"Debug: Found field_declaration directly")
                self._parse_field_declaration(child)
            elif child.type == "method_declaration":
                print(f"Debug: Found method_declaration directly")
                self._parse_method_declaration(child)
    
    def _parse_declaration_list(self, node: Node):
        """Parse a declaration_list node containing member_declaration, field_declaration, method_declaration, etc."""
        print(f"Debug: declaration_list children: {[child.type for child in node.children]}")
        for child in node.children:
            if child.type == "member_declaration":
                print(f"Debug: Found member_declaration in declaration_list")
                self._parse_member_declaration(child)
            elif child.type == "field_declaration":
                print(f"Debug: Found field_declaration in declaration_list")
                self._parse_field_declaration(child)
            elif child.type == "method_declaration":
                print(f"Debug: Found method_declaration in declaration_list")
                self._parse_method_declaration(child)
    
    def _parse_member_declaration(self, node: Node):
        """Parse a member_declaration node"""
        for child in node.children:
            if child.type == "field_declaration":
                self._parse_field_declaration(child)
            elif child.type == "method_declaration":
                self._parse_method_declaration(child)
    
    def _parse_field_declaration(self, node: Node):
        """Parse a field_declaration node within the class"""
        # Similar to file-level variable parsing but store in class environment
        for child in node.children:
            if child.type == "variable_declaration":
                var_type = None
                for decl_child in child.children:
                    if decl_child.type == "predefined_type":
                        var_type = self.source[decl_child.start_byte:decl_child.end_byte].decode().strip()
                    elif decl_child.type == "variable_declarator":
                        var_name = None
                        var_value = ""
                        children = iter(decl_child.children)
                        for item in children:
                            item_text = self.source[item.start_byte:item.end_byte].decode()
                            if item.type == "identifier":
                                var_name = self.source[item.start_byte:item.end_byte].decode()
                            elif item.type == "=":
                                item = next(children)
                                # Get the value after '='
                                value_text = self.source[item.start_byte:item.end_byte].decode()
                                # Remove '=' and whitespace
                                value_text = value_text.lstrip('=').strip()
                                # Evaluate the value
                                var_value = Interpreter.evaluate(item, value_text, self.class_environment)
                        if var_name:
                            # Store the variable in the class environment
                            self.class_environment.define_variable(var_name, var_value)
    
    def _parse_method_declaration(self, node: Node):
        """Parse a method_declaration node"""
        method_name = None
        method_type = None
        parameter_list = []
        expression_body = None
        has_block = False
        
        # Parse method components
        for child in node.children:
            if child.type == "predefined_type":
                method_type = self.source[child.start_byte:child.end_byte].decode().strip()
            elif child.type == "identifier":
                method_name = self.source[child.start_byte:child.end_byte].decode()
            elif child.type == "parameter_list":
                parameter_list = self._parse_parameter_list(child)
            elif child.type == "arrow_expression_clause":
                # Expression-bodied method
                expression_text = self.source[child.start_byte:child.end_byte].decode()
                # Remove the '=>' and trim
                expression_body = expression_text.lstrip('=>').strip()
            elif child.type == "block":
                has_block = True
        
        if method_name:
            if expression_body:
                # Create ExpressionBioledMethod
                from Types import ExpressionBioledMethod
                param_names = [param['name'] for param in parameter_list]
                method = ExpressionBioledMethod(
                    method_name, 
                    method_type or "void", 
                    len(parameter_list), 
                    expression_body, 
                    param_names
                )
                self.class_environment.define_method(method_name, method)
            elif has_block:
                # Create CSMethod for regular methods
                method = CSMethod(method_name, method_type or "void", len(parameter_list), node, self.source, self.class_environment)
                self.class_environment.define_method(method_name, method)
    
    def _parse_parameter_list(self, node: Node) -> list:
        """Parse a parameter_list node and return list of parameter info"""
        parameters = []
        for child in node.children:
            if child.type == "parameter":
                param_info = self._parse_parameter(child)
                if param_info:
                    parameters.append(param_info)
        return parameters
    
    def _parse_parameter(self, node: Node) -> dict | None:
        """Parse a parameter node and return parameter info"""
        param_type = None
        param_name = None
        
        for child in node.children:
            if child.type == "predefined_type":
                param_type = self.source[child.start_byte:child.end_byte].decode().strip()
            elif child.type == "identifier":
                param_name = self.source[child.start_byte:child.end_byte].decode()
        
        if param_name:
            return {
                'name': param_name,
                'type': param_type or 'object'
            }
        return None

    def get_class_environment(self) -> Environment:
        """Get the class-specific environment containing variables and methods"""
        return self.class_environment


class CSMethod(Callable):
    """
    A class that represents a C# method with a block body.
    """
    def __init__(self, name: str, _type: str, arity: int, node: Node, source: bytes, environment: Environment):
        super().__init__(name, _type, arity)
        self.node = node
        self.source = source
        self.environment = environment
        self.attributes = []  # Store method attributes
        self.method_environment = Environment(environment)  # Method-specific environment
        
        # Extract attributes
        self._extract_attributes()
        # Parse variables from statements
        self._parse_method_variables()
    
    def _extract_attributes(self):
        """Extract attribute_list nodes from the method declaration"""
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = self.source[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)
                print(f"Debug: Found method attribute: {attr_text}")
    
    def _parse_method_variables(self):
        """Parse variable declarations from statements and store in method environment if evaluable."""
        import re
        for statement in self.iterate_statements():
            # Match C# variable declaration: type name = value;
            # e.g., int x = 5; string s = "hello";
            match = re.match(r'^(?:var|[a-zA-Z_][a-zA-Z0-9_<>]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+);$', statement)
            if match:
                var_name = match.group(1)
                var_value = match.group(2).strip()
                # Skip if value looks like a function call or complex expression
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\(', var_value):
                    continue
                # Try to evaluate the value using Interpreter
                try:
                    evaluated = Interpreter.evaluate(None, var_value, self.method_environment)
                    self.method_environment.define_variable(var_name, evaluated)
                except Exception as e:
                    continue
    
    def iterate_statements(self) -> Iterator[str]:
        """Iterator that yields statements from the method body one at a time"""
        # Find the block node (method body)
        block_node = None
        for child in self.node.children:
            if child.type == "block":
                block_node = child
                break
        
        if not block_node:
            return  # No method body found
        
        # Get the source text of the entire method
        method_text = self.source[block_node.start_byte:block_node.end_byte].decode()
        
        # Remove the outer braces
        method_text = method_text.strip()
        if method_text.startswith('{') and method_text.endswith('}'):
            method_text = method_text[1:-1].strip()
        
        # Split into lines and process each line
        lines = method_text.split('\n')
        current_statement = ""
        brace_count = 0
        in_string = False
        string_char = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
            
            # Process each character in the line
            for char in line:
                # Handle string literals
                if char in ['"', "'"] and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                
                # Only process braces and semicolons when not in a string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    elif char == ';' and brace_count == 0:
                        # End of statement
                        current_statement += char
                        statement = current_statement.strip()
                        if statement:  # Don't yield empty statements
                            yield statement
                        current_statement = ""
                        continue
                
                current_statement += char
            
            # Add newline if not at the end of a statement
            if current_statement.strip():
                current_statement += '\n'
        
        # Yield any remaining statement
        if current_statement.strip():
            yield current_statement.strip()
    
    def get_method_environment(self) -> Environment:
        """Get the method-specific environment containing variables"""
        return self.method_environment

# Test
if __name__ == "__main__":
    from main import create_globals, globals

    env = create_globals(globals)

    test_code = """
using System;
using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;

private string a = "hello";

[Parallizable]
public sealed class Admin_Share_Recipients : APITest
{
    private string abc = "gl-share/api/Admin/share";
    private string Endpoint = $"gl-share/api/Admin/share";

    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}/recipients";

    private string anothervar = $"{EndpointWithShareLink("somelink/ink")}";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenBasicUserAPI, Shares.KkomradeNoMessage)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.None, Operation = OperationType.Post, ResponseCode = 200)]
    public void POST_AdminShareRecipients_AddRecipient_200_141306()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var shareGroup = Get<ShareGroup>(Shares.KkomradeNoMessage);
        Models.User toAdd = Get<Models.User>(Users.BasicTierUser);
        Recipient recipient = (Recipient)toAdd with
        {
            UserWhoAddedRecipient = token.User.Email,

        };
    }
    
    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.AnyTierUserAPI)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.AnyTierUserAPI)]
    public void POST_Admin_External_Pricing_GiveNewTrial_201_133278()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.AnyTierUserAPI);
        subject.User.SetUserToken(subject);

        UpdateExternalUserPricingModel disableTrialRequest = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = false,
        };

        Send(
            Post(disableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        var userInfo = PollForExpectedTrialStatus(subject, false);
        Verify(userInfo?.IsTrialEnabled, "Trial disabled").Succintly.Is(false);

        var enableTrialRequest = disableTrialRequest with
        {
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = true,
        };

        Send(
            Post(enableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Created);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully added trial subscription for user on Subscriptions API. Status code: 201");

        userInfo = PollForExpectedTrialStatus(subject, true);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");
    }

}
"""

    environment = Environment(env)
    cs = CSFile(test_code, environment)
    
    print("Using directives:")
    print(cs.using_directives)
    
    print("\nFile-level variables:")
    print(cs.environment.values)
    
    print("\nClasses found:")
    for csharp_class in cs.get_classes():
        print(f"\nClass: {csharp_class.name}")
        print(f"  Attributes: {csharp_class.attributes}")
        class_env = csharp_class.get_class_environment()
        print(f"  Variables: {class_env.values}")
        print(f"  Methods:")
        for method_name, method in class_env.callables.items():
            if isinstance(method, CSMethod):
                print(f"    {method_name}: {method.attributes}")
                # Show statements and method environment for the first method with a body
                if method_name == "POST_AdminShareRecipients_AddRecipient_200_141306":
                    print(f"      Statements:")
                    for i, statement in enumerate(method.iterate_statements(), 1):
                        print(f"        {i}. {statement}")
                    print(f"      Method variables: {method.get_method_environment().values}")
            else:
                print(f"    {method_name}: []")