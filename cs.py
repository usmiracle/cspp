import tree_sitter_c_sharp as tscs

from Interpreter import Interpreter
from Types import Callable
from collections.abc import Iterator
from tree_sitter import Language, Parser, Tree, Node
from Environment import Environment
from special_nodes import Send


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
        self.send_functions = []  # Store Send function objects
        
        # Extract attributes
        self._extract_attributes()
        # Parse variables from statements
        self._parse_method_variables()
        # Parse Send function calls
        self._parse_send_functions()
    
    def _extract_attributes(self):
        """Extract attribute_list nodes from the method declaration"""
        for child in self.node.children:
            if child.type == "attribute_list":
                attr_text = self.source[child.start_byte:child.end_byte].decode()
                self.attributes.append(attr_text)
                print(f"Debug: Found method attribute: {attr_text}")
    
    def _parse_send_functions(self):
        """Parse Send function calls from statement nodes and create Send objects."""
        for stmt_node in self.iterate_statements():
            # Look for invocation_expression nodes that might be Send calls
            self._find_send_calls_in_node(stmt_node)
    
    def _find_send_calls_in_node(self, node: Node):
        """Recursively search for Send function calls in a node and its children."""
        # Check if this node is a Send call
        if self._is_send_call(node):
            try:
                send_obj = Send(node, self.source, self.method_environment)
                self.send_functions.append(send_obj)
                print(f"Debug: Found Send function: {send_obj}")
            except Exception as e:
                print(f"Debug: Error parsing Send function: {e}")
        
        # Recursively check children
        for child in node.children:
            self._find_send_calls_in_node(child)
    
    def _is_send_call(self, node: Node) -> bool:
        """Check if a node represents a Send function call."""
        if node.type != "invocation_expression":
            return False
        
        # Get the text of the node
        node_text = self.source[node.start_byte:node.end_byte].decode()
        
        # Check if it starts with "Send("
        return node_text.strip().startswith("Send(")
    
    def _parse_method_variables(self):
        """Parse variable declarations from statement nodes and store in method environment if evaluable."""
        for stmt_node in self.iterate_statements():
            # Only process local_declaration_statement nodes
            if stmt_node.type == "local_declaration_statement":
                print(f"Debug: local_declaration_statement children: {[child.type for child in stmt_node.children]}")
                for child in stmt_node.children:
                    if child.type == "variable_declaration":
                        print(f"Debug: variable_declaration children: {[c.type for c in child.children]}")
                        var_type = None
                        for decl_child in child.children:
                            if decl_child.type == "predefined_type":
                                var_type = self.source[decl_child.start_byte:decl_child.end_byte].decode().strip()
                            elif decl_child.type == "implicit_type":
                                var_type = self.source[decl_child.start_byte:decl_child.end_byte].decode().strip()
                            elif decl_child.type == "variable_declarator":
                                print(f"Debug: variable_declarator children: {[c.type for c in decl_child.children]}")
                                var_name = None
                                var_value = ""
                                children = list(decl_child.children)
                                i = 0
                                while i < len(children):
                                    item = children[i]
                                    if item.type == "identifier":
                                        var_name = self.source[item.start_byte:item.end_byte].decode()
                                        i += 1
                                    elif item.type == "=":
                                        # The next child is the value node
                                        if i + 1 < len(children):
                                            value_node = children[i + 1]
                                            value_text = self.source[value_node.start_byte:value_node.end_byte].decode().strip()
                                            try:
                                                evaluated = Interpreter.evaluate(value_node, value_text, self.method_environment)
                                                var_value = evaluated
                                            except Exception:
                                                var_value = value_text
                                            i += 2
                                            continue
                                        else:
                                            i += 1
                                    else:
                                        i += 1
                                if var_name and var_value:
                                    self.method_environment.define_variable(var_name, var_value)
        # Debug output: show what is stored in the method environment after parsing
        print(f"Debug: Method environment after variable parsing: {self.method_environment.values}")

    def iterate_statements(self) -> Iterator[Node]:
        """
        Iterator that yields statement nodes from the method body one at a time.
        Each element is a node representing an entire statement.
        """
        # Find the block node (method body)
        block_node = None
        for child in self.node.children:
            if child.type == "block":
                block_node = child
                break
        if not block_node:
            return  # No method body found
        # In the C# grammar, statements are direct children of the block node
        for child in block_node.children:
            # Skip the opening and closing braces
            if child.type == '{' or child.type == '}':
                continue
            print(f"Debug: Statement node type: {child.type}, text: {self.source[child.start_byte:child.end_byte].decode().strip()}")
            yield child
    
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
    [Recycle(Recycle.TokenAdminAPI)]
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

    [Test]
    public void Test_Multiple_HTTP_Methods()
    {
        // Test GET request
        Send(Get().To("api/users"));
        
        // Test PUT request
        Send(Put(userData).To("api/users/123"));
        
        // Test DELETE request
        Send(Delete().To("api/users/456"));
        
        // Test PATCH request
        Send(Patch(updateData).To("api/users/789"));
    }

}
"""

    small_test_code = """
    class TestClass : APITest {
        [Test]
        public void Test_Multiple_HTTP_Methods()
        {
            var startpath = "api/users";
            var path = "api/users";

            // Test GET request
            Send(Get().To(path)); // this should be evaluated to get api/users/api/users
        
            // Test PUT request
            Send(Put(userData).To($"{startpath}/123")); // this should be evaluated to get api/users/api/users/123
        
            // Test DELETE request
            Send(Delete().To(startpath + path)); // this should be evaluated to get api/users/api/users
        
            // Test PATCH request
            Send(Patch(updateData).To("api/users/789")); // this should be evaluated to get api/users/789
        }
    }
    """

    environment = Environment(env)
    cs = CSFile(small_test_code, environment)
    
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
                print(f"      Method variables: {method.get_method_environment().values}")
                print(f"      Send functions: {method.send_functions}")
            else:
                print(f"    {method_name}: []")