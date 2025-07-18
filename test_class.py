from cs import CSFile, CSClass, CSMethod
from Environment import Environment
from Interpreter import Interpreter
from helper import create_globals, globals, paths, get_path_to_var, PathResolver
import Types

global_env : Environment = create_globals(globals)

def test_global_environment(env: Environment):
    assert(env.get_variable("GlobalLabShare") == "https://qa-share.transperfect.com")
    assert(env.get_variable("GlobalLabShareNoHTTPS") == "qa-share.transperfect.com")
    assert(env.get_variable("DownloadAPI") == "/api/Download")
    assert(env.get_variable("DownloadSignedKeyAPI") == "/api/Download/signed-key")
    assert(env.get_variable("RecipientsAPI") == "/api/Recipients")
    assert(env.get_variable("RecipientsRecentAPI") == "/api/Recipients/recent")
    assert(env.get_variable("RecipientsSearchEmailsAPI") == "/api/Recipients/search-emails")
    assert(env.get_variable("RecipientsSearchQueryAPI") == "/api/Recipients/search-query")

cs_file: CSFile | None= None
cs_classes: list[CSClass] = []
def test_class_environment():
    total_classes = 1
    with open("testfile.cs", "r") as file:
        cs_file_content = file.read()

    cs_file_content = cs_file_content.replace(" { get; set; } ", " ")
    cs_file_content = cs_file_content.replace("{ get; set; }", "")
    cs_file_content = cs_file_content.replace("{get;set}", "")
    cs_file_content = cs_file_content.replace("{get;set; }", "")
    cs_file_content = cs_file_content.replace("{get;set;}", "")
    cs_file_content = cs_file_content.replace("{get;set; }", "")

    cs_file = CSFile(cs_file_content, global_env)
    classes_seen = 0

    test_global_environment(global_env)
    for c in cs_file.get_classes():
        classes_seen += 1
        cs_classes.append(c)

        assert(c.name == "Admin_Share_ShareLinkId")
        gloabllabshare = c.environment.get_variable("GlobalLabShare")
        assert(gloabllabshare == "https://qa-share.transperfect.com")

        assert(c.super_class_name == "APITest")


        endpoint_method = c.environment.get_method("Endpoint")
        assert(endpoint_method is not None)
        assert(isinstance(endpoint_method, Types.ExpressionBioledMethod))

        interpreter = Interpreter(c.environment)
        endpoint_method_call_val = endpoint_method.call(interpreter, [])
        expected_endpoint = f"{gloabllabshare}/gl-share/api/Admin/share"
        assert(endpoint_method_call_val == expected_endpoint)


        endpoint_with_share_link_method = c.environment.get_method("EndpointWithShareLink")
        assert(endpoint_with_share_link_method is not None)
        assert(isinstance(endpoint_with_share_link_method, Types.ExpressionBioledMethod))
        assert(endpoint_with_share_link_method.arity == 1)
        interpreter = Interpreter(c.environment)
        share_link = "1234567890"
        endpoint_with_share_link_method_call_val = endpoint_with_share_link_method.call(interpreter, [share_link])
        expected_endpoint_with_share_link = f"{gloabllabshare}/gl-share/api/Admin/share/{share_link}"
        # check if the interpreter can work with something like $"lsdkfj{}" + sdlfk

        assert(endpoint_with_share_link_method_call_val == expected_endpoint_with_share_link)


        assert(c.attributes == ["[Parallelizable]"])


        assert(len(c.environment.callables) == 4)
        endpoint_with_params = c.environment.get_method("EndpointWithParameters")
        assert(endpoint_with_params is not None)
        assert(isinstance(endpoint_with_params, Types.ExpressionBioledMethod))
        assert(endpoint_with_params.arity == 2)
        interpreter = Interpreter(c.environment)
        endpoint_with_parameters_method_call_val = endpoint_with_params.call(interpreter, [1, 2])
        expected_endpoint_with_parameters = f"{gloabllabshare}/gl-share/api/Admin/users/pricing/1/2"
        assert(endpoint_with_parameters_method_call_val == expected_endpoint_with_parameters)


    assert(classes_seen == total_classes)


def test_method_environment():
    test_global_environment(global_env)
    total_methods = 1
    methods_seen = 0
    for c in cs_classes:
        if c.name == "Admin_Share_ShareLinkId":
            for m in c.get_test_methods():
                methods_seen += 1


                is_test = False
                for attr in m.attributes:
                    if "Test" in attr:
                        is_test = True
                        break
                assert(is_test)


            endpoint = m.environment.get_variable("Endpoint")
            for s in m.send_functions:
                # for line 11, it should be 3, line 27 should be 0, and line 33 should be 4
                if s.line_number == 27:
                    sharelink = f"{endpoint}/shareGroup.Share.Id/disability"
                    assert(s.evaluated_path == sharelink)
                    assert(s.request_type is not None)
                    assert(s.request_type.capitalize() == "Patch")
                    assert(s.expected_code == None)

                    assert(s.verify_count_after == 0)

                if s.line_number == 11:
                    assert(s.expected_code == "200")
                    assert(s.verify_count_after == 3)

                if s.line_number == 33:
                    assert(s.expected_code == "200")
                    assert(s.verify_count_after == 4)

            
    assert(methods_seen == total_methods)


path_to_var = get_path_to_var(paths)
def test_path_to_var():
    assert(path_to_var["/api/Admin/blacklist-organizations".lower()] == "AdminBlackList")


path_resolver = PathResolver(paths)
def test_path_resolver():
    assert(path_resolver.get_var_for_path("/api/Admin/blacklist-organizations") == "AdminBlackList")
    assert(path_resolver.get_var_for_path("/api/ApprovalLinks/approval.Key") == "ApprovalLinksApprovalKey")
    assert(path_resolver.get_var_for_path("/api/Admin/share/1234567890") == "AdminShareSharelinkid")
    assert(path_resolver.get_var_for_path("/api/Admin/share/shareGroup.Share.Id/disability") == "AdminShareSharelinkidDisability")


def test_select_best_send():
    from extension import SwaggerAdder
    print("Starting test_select_best_send")

    swagger_adder = SwaggerAdder("testfile.cs")

    gloabllabshare = cs_classes[0].environment.get_variable("GlobalLabShare")
    endpoint = cs_classes[0].environment.get_variable("Endpoint")

    test_method = cs_classes[0].environment.get_method("GET_AdminShare_DisabledShare_200_141460")
    assert(test_method is not None)
    assert(test_method.name == "GET_AdminShare_DisabledShare_200_141460")

    assert(isinstance(test_method, CSMethod))
    send_obj = swagger_adder.select_best_send(test_method, test_method.name)

    assert(send_obj is not None)
    assert(send_obj.expected_code == "200")
    assert(send_obj.request_type is not None)
    assert(send_obj.request_type.capitalize() == "Get")
    assert(send_obj.evaluated_path == f"{endpoint}/shareGroup.Share.Id")
    assert(send_obj.verify_count_after is not None)
    
    path_resolver = PathResolver(paths)
    path_var = path_resolver.get_var_for_path(str(send_obj.evaluated_path))
    assert(path_var == "AdminShareSharelinkid")
    
    print("ending test_select_best_send")


def test_method_environment_2():
    test_global_environment(global_env)
    gloabllabshare = cs_classes[0].environment.get_variable("GlobalLabShare")


    for c in cs_classes:
        default_page_number = c.environment.get_variable("DefaultPageNumber")
        default_page_size = c.environment.get_variable("DefaultPageSize")
        assert(default_page_number == "1")
        assert(default_page_size == "50")

            
        endpointwithparams = c.environment.get_method("EndpointWithParameters")
        assert(endpointwithparams is not None)
        assert(endpointwithparams.arity == 2)
        interpreter = Interpreter(c.environment)
        endpoint_with_parameters_method_call_val = endpointwithparams.call(interpreter, [1, 2])
        expected_endpoint_with_parameters = f"{gloabllabshare}/gl-share/api/Admin/users/pricing/1/2"
        assert(endpoint_with_parameters_method_call_val == expected_endpoint_with_parameters)


test_global_environment(global_env)
# test_class_environment()
# test_method_environment()
# test_path_to_var()
# test_path_resolver()
# test_select_best_send()
# test_method_environment_2()


def test_failing():
    with open("failing.cs", "r") as file:
        cs_file_content = file.read()

    cs_file = CSFile(cs_file_content, global_env)
    for c in cs_file.get_classes():
        for m in c.get_test_methods():
            for s in m.send_functions:
                print(s.evaluated_path)
                print(s.request_type)
                print(s.line_number)
                print(s.raw_text)
                break
        break


def test_interpreter():
    source_code = """
    public sealed class Admin: APITest
    {
        var endpoint = $"{GlobalLabShare}/gl-share/api/Admin/share" + "sdlfk";
        [Test]
        public void Test()
        {
        }
    }
    """

    cs_file = CSFile(source_code, global_env)
    for c in cs_file.get_classes():
        for m in c.get_test_methods():
            # check endpoint is evaluated correctly
            interpreter = Interpreter(c.environment)
            endpoint = m.environment.get_variable("endpoint")
            print(endpoint)
            assert(endpoint == "https://qa-share.transperfect.com/gl-share/api/Admin/sharesdlfk")

test_interpreter()