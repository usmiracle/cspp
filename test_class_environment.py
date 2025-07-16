from cs import CSFile
from Environment import Environment
from helper import create_globals, globals

def test_class_environment():
    with open('testfile.cs', 'r', encoding='utf-8') as f:
        source = f.read()
    env = create_globals(globals)
    environment = Environment(env)
    cs_file = CSFile(source, environment)
    classes = list(cs_file.get_classes())
    assert len(classes) == 1, f"Should find one class, found {len(classes)}"
    csharp_class = classes[0]
    class_env = csharp_class.get_class_environment()
    print("Class environment variables:", class_env.values.keys())
    assert 'Endpoint' in class_env.values, "Endpoint should be in class environment"
    assert 'EndpointWithShareLink' in class_env.values, "EndpointWithShareLink should be in class environment"
    print("Test passed: Endpoint and EndpointWithShareLink are in the class environment.")

if __name__ == "__main__":
    test_class_environment() 