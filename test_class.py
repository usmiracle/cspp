from cs import CSFile, CSClass, CSMethod
from Environment import Environment
from Interpreter import Interpreter
from helper import create_globals, globals, paths
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
        assert(endpoint_method_call_val.strip("\"") == expected_endpoint.strip("\'"))


        endpoint_with_share_link_method = c.environment.get_method("EndpointWithShareLink")
        assert(endpoint_with_share_link_method is not None)
        assert(isinstance(endpoint_with_share_link_method, Types.ExpressionBioledMethod))
        assert(endpoint_with_share_link_method.arity == 1)
        interpreter = Interpreter(c.environment)
        share_link = "1234567890"
        endpoint_with_share_link_method_call_val = endpoint_with_share_link_method.call(interpreter, [share_link])
        expected_endpoint_with_share_link = f"{gloabllabshare}/gl-share/api/Admin/share/{share_link}"
        assert(endpoint_with_share_link_method_call_val.strip("\"") == expected_endpoint_with_share_link.strip("\'"))


        assert(c.attributes == ["[Parallelizable]"])


        assert(len(c.environment.callables) == 3)


    assert(classes_seen == total_classes)


def test_method_environment():
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
                if s.line_number == 18:
                    pass
                    #assert(s.endpoint )
    assert(methods_seen == total_methods)


test_global_environment(global_env)
test_class_environment()
test_method_environment()