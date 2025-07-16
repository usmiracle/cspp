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
    print(f"Global environment test passed")

cs_file: CSFile | None= None
def test_class_environment():
    total_classes = 1
    with open("testfile.cs", "r") as file:
        cs_file_content = file.read()

    cs_file = CSFile(cs_file_content, global_env)
    classes_seen = 0

    test_global_environment(global_env)
    for c in cs_file.get_classes():
        classes_seen += 1

        assert(c.name == "Admin_Share_ShareLinkId")
        gloabllabshare = c.environment.get_variable("GlobalLabShare")
        assert(gloabllabshare == "https://qa-share.transperfect.com")

        endpoint_method = c.environment.get_method("Endpoint")
        assert(endpoint_method is not None)
        assert(isinstance(endpoint_method, Types.ExpressionBioledMethod))
        from Interpreter import Interpreter
        interpreter = Interpreter(c.environment)
        endpoint_method_call_val = endpoint_method.call(interpreter, [])
        expected_endpoint = f"{gloabllabshare}/gl-share/api/Admin/share"
        assert(endpoint_method_call_val.strip("\"") == expected_endpoint.strip("\'"))


        assert(c.attributes == ["[Parallelizable]"])

        print(len(c.environment.callables.values()))
        assert(len(c.environment.callables) == 3)
        assert(c)

    assert(classes_seen == total_classes)


test_global_environment(global_env)
test_class_environment()