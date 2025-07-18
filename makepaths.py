import json
import os
import re

current_dir = os.path.dirname(__file__)
swagger_path = os.path.join(current_dir, "swagger.json")
apitest_file = "C:\\Users\\sulabh.katila\\source\\repos\\glshare\\Tests\\API\\ApiTest.cs"

new_variables = ""
tab_space = "    "
path_prefix = "/api/"
existing_vars = [
    "/api/Admin/blacklist-organizations",
    "/api/ApprovalLinks",
    "/api/ApprovalLinks/{approvalKey}",
    "/api/Admin/user/external/pricing"
]

# Open and load the JSON file into a Python dictionary
with open(swagger_path, 'r') as f:
    swagger = json.load(f)

for path in swagger["paths"].keys():
    if path in existing_vars: continue

    var_parts = path[len(path_prefix)::].split(path_prefix[-1])
    new_var = ""
    for part in var_parts:
        newPart = part.replace("-", "_").replace("{", "").replace("}", "")
        new_var += newPart.capitalize()
    
    new_variables += 2 * tab_space
    new_variables += "public const string " + new_var + " = " + f"\"{path}\";" + "\n"

old_variable_declarations = """public static class Paths
    {
        public const string AdminBlackList = "/api/Admin/blacklist-organizations";
        public const string ApprovalLinks = "/api/ApprovalLinks";
        public const string ApprovalLinksApprovalKey = "/api/ApprovalLinks/{approvalKey}";
        public const string AdminExternalPricing = "/api/Admin/user/external/pricing";"""

# sed -i "s/${old_var}"/${old_var + new_variables}/" ${apitest_path}
replacement = old_variable_declarations + "\n" + new_variables

with open(apitest_file, 'r') as f:
    content = f.read()

updated_content = content.replace(old_variable_declarations, replacement, 1)

with open(apitest_file, 'w') as f:
    f.write(updated_content)
