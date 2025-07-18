from Environment import Environment
import re

# from newvars.txt
# plain path, and path with var

paths = """
        public const string AdminBlackList = "/api/Admin/blacklist-organizations";
        public const string ApprovalLinks = "/api/ApprovalLinks";
        public const string ApprovalLinksApprovalKey = "/api/ApprovalLinks/{approvalKey}";
        public const string AdminExternalPricing = "/api/Admin/user/external/pricing";
        public const string AdminInfo = "/api/Admin/info";
        public const string AdminShareSharelinkid = "/api/Admin/share/{shareLinkId}";
        public const string AdminShareSharelinkidDisability = "/api/Admin/share/{shareLinkId}/disability";
        public const string AdminShareSharelinkidRecipients = "/api/Admin/share/{shareLinkId}/recipients";
        public const string AdminServiceRegistration = "/api/Admin/service/registration";
        public const string AdminUsersPricingPagenumberPagesize = "/api/Admin/users/pricing/{pageNumber}/{pageSize}";
        public const string AdminUserInternalPricing = "/api/Admin/user/internal/pricing";
        public const string AdminUserSubscriptionsTrial = "/api/Admin/user/subscriptions/trial";
        public const string AdminUserPricing = "/api/Admin/user/pricing";
        public const string AuditlogSharelinkid = "/api/AuditLog/{shareLinkId}";
        public const string BlacklistorganizationsVerify_user_orgEmail = "/api/BlacklistOrganizations/verify-user-org/{email}";
        public const string Config = "/api/Config";
        public const string DownloadSigned_keySharelinkid = "/api/Download/signed-key/{shareLinkId}";
        public const string EulaLatest = "/api/EULA/latest";
        public const string FilesA2aFile_types = "/api/Files/a2a/file-types";
        public const string FilesA2aFile_preview_info = "/api/Files/a2a/file-preview-info";
        public const string FilesA2aSharelinkidA2afileidPage_count = "/api/Files/a2a/{shareLinkId}/{A2AFileId}/page-count";
        public const string FilesFilepath = "/api/Files/{filePath}";
        public const string FilesA2aStatusSharelinkidA2aoperationid = "/api/Files/a2a/status/{shareLinkId}/{A2AOperationId}";
        public const string FilesFolder_contentSharelinkidFolderpath = "/api/Files/folder-content/{shareLinkId}/{folderPath}";
        public const string FilesA2aShare_key = "/api/Files/a2a/share-key";
        public const string FilesA2aConvert = "/api/Files/a2a/convert";
        public const string FilesCarfsAnon_share_key = "/api/Files/carfs/anon-share-key";
        public const string FilesSharelinkidFilepathA2a_file_metadata = "/api/Files/{shareLinkId}/{filePath}/a2a-file-metadata";
        public const string FilesCopy_file = "/api/Files/copy-file";
        public const string GeolocationStorage_region = "/api/GeoLocation/storage-region";
        public const string GeolocationIpaddress = "/api/GeoLocation/ipAddress";
        public const string Log = "/api/Log";
        public const string MobileappRegister = "/api/MobileApp/register";
        public const string Personalshare = "/api/PersonalShare";
        public const string PersonalshareShare_personal_link_email = "/api/PersonalShare/share-personal-link-email";
        public const string PersonalshareSharelinkidVerify_email = "/api/PersonalShare/{shareLinkId}/verify-email";
        public const string PersonalshareMetadataidEmail = "/api/PersonalShare/{metadataId}/email";
        public const string PersonalshareUserPersonalshareusername = "/api/PersonalShare/user/{personalShareUsername}";
        public const string PersonalshareSetupPersonalshareusername = "/api/PersonalShare/setup/{personalShareUsername}";
        public const string Recipients = "/api/Recipients";
        public const string RecipientsRecent = "/api/Recipients/recent";
        public const string RecipientsSearch_emails = "/api/Recipients/search-emails";
        public const string RecipientsSearch_query = "/api/Recipients/search-query";
        public const string RecipientsVerify_user_existsEmail = "/api/Recipients/verify-user-exists/{email}";
        public const string Registration = "/api/Registration";
        public const string RegistrationRegistrationlinkid = "/api/Registration/{registrationLinkId}";
        public const string RegistrationRegistrationlinkidRegister = "/api/Registration/{registrationLinkId}/register";
        public const string RegistrationPassword_policies = "/api/Registration/password-policies";
        public const string Reports = "/api/Reports";
        public const string ReportsShareSharelinkid = "/api/Reports/share/{shareLinkId}";
        public const string ShareSetup = "/api/Share/setup";
        public const string ShareSharelinkid = "/api/Share/{shareLinkId}";
        public const string Share = "/api/Share";
        public const string ShareSharelinkidCreate_share_emails = "/api/Share/{shareLinkId}/create-share-emails";
        public const string ShareDetailsSharelinkid = "/api/Share/details/{shareLinkId}";
        public const string ShareSharelinkidFiles = "/api/Share/{shareLinkId}/files";
        public const string ShareSummary = "/api/Share/summary";
        public const string ShareReceivedSummary = "/api/Share/received/summary";
        public const string ShareForward_share_email = "/api/Share/forward-share-email";
        public const string ShareEdit_share = "/api/Share/edit-share";
        public const string ShareactivityShareSharelinkid = "/api/ShareActivity/share/{shareLinkId}";
        public const string ShareactivityAdd_shareactivitySharelinkid = "/api/ShareActivity/add-shareactivity/{shareLinkId}";
        public const string UserUsersPagenumberPagesize = "/api/User/users/{pageNumber}/{pageSize}";
        public const string UserAdd_users = "/api/User/add-users";
        public const string UserPreferences = "/api/User/preferences";
        public const string UserPreferencesKeyid = "/api/User/preferences/{keyId}";
        public const string UserMe = "/api/User/me";
        public const string UserExpired_trial = "/api/User/expired-trial";
        public const string UserAccept_terms = "/api/User/accept-terms";
        public const string UserSubscriptionWebhook = "/api/User/subscription/webhook";
        public const string UserGet_started_product_email = "/api/User/get-started-product-email";
        public const string Version = "/api/Version";
"""

globals = """ 
DownloadAPI=/api/Download
DownloadSignedKeyAPI=/api/Download/signed-key
RecipientsAPI=/api/Recipients
RecipientsRecentAPI=/api/Recipients/recent
RecipientsSearchEmailsAPI=/api/Recipients/search-emails
RecipientsSearchQueryAPI=/api/Recipients/search-query
ReportsAPI=/api/Reports
ShareAPI=/api/Share
ShareAPIv2=/api/v2/Shares
ShareActivityAPI=/api/ShareActivity
HealthAPI=/healthz
AuditLogAPI=/api/AuditLog
GeoLocation=/api/GeoLocation
UserPreferencesAPI=/api/User/preferences
UserPermissionAPI=/api/User/me
AdminBlackListAPI=/api/Admin/blacklist-organizations
DatabaseHealthAPI=/database
ServiceHealthAPI=/services
# 
SQL=Tests.SQL.SQLContext
GlobalLabShare=https://qa-share.transperfect.com
GlobalLabShareNoHTTPS=qa-share.transperfect.com
DownloadAPI=https://qa-share.transperfect.com/gl-share/api/Download
DownloadSignedKeyAPI=https://qa-share.transperfect.com/gl-share/api/Download/signed-key
RecipientsAPI=https://qa-share.transperfect.com/gl-share/api/Recipients
RecipientsRecentAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/recent
RecipientsSearchEmailsAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/search-emails
RecipientsSearchQueryAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/search-query
ReportsAPI=https://qa-share.transperfect.com/gl-share/api/Reports
ShareAPI=https://qa-share.transperfect.com/gl-share/api/Share
ShareAPIv2=https://qa-share.transperfect.com/gl-share/api/v2/Shares
ShareActivityAPI=https://qa-share.transperfect.com/gl-share/api/ShareActivity
HealthAPI=https://qa-share.transperfect.com/gl-share/healthz
AuditLogAPI=https://qa-share.transperfect.com/gl-share/api/AuditLog
GeoLocation=https://qa-share.transperfect.com/gl-share/api/GeoLocation
UserPreferencesAPI=https://qa-share.transperfect.com/gl-share/api/User/preferences
UserPermissionAPI=https://qa-share.transperfect.com/gl-share/api/User/me
AdminBlackListAPI=https://qa-share.transperfect.com/gl-share/api/Admin/blacklist-organizations
DatabaseHealthAPI=https://qa-share.transperfect.com/gl-share/database
ServiceHealthAPI=https://qa-share.transperfect.com/gl-share/services
APIVersion=?api-version=1
APIVersionBad=?api-version=0
CaRFSArchive=https://fs-qa.transperfect.com/Archives
ExpiredAuth=eyJhbGciOiJSUzI1NiIsImtpZCI6IkU4MTY2QjA0RDlBQTI5RTlFRURDNkU2QTk1RUNGNzgxMzMyQzcwNTAiLCJ0eXAiOiJKV1QiLCJ4NXQiOiI2QlpyQk5tcUtlbnUzRzVxbGV6M2dUTXNjRkEifQ.eyJuYmYiOjE2Mjg2MjI4NDUsImV4cCI6MTYyODYyNjQ0NSwiaXNzIjoiaHR0cHM6Ly9zc28tc3RnLnRyYW5zcGVyZmVjdC5jb20iLCJhdWQiOlsiaHR0cHM6Ly9zc28tc3RnLnRyYW5zcGVyZmVjdC5jb20vcmVzb3VyY2VzIiwiR0xTaGFyZUFwaSIsIkNhckZTQXBpIl0sImNsaWVudF9pZCI6IlhQOENlUnlOOUFHZ0c4bk5oQWVQY3o2Yjc3cEFnZGg5Iiwic3ViIjoiYmVzYXk1NzY1N0BiaW9ob3J0YS5jb20iLCJhdXRoX3RpbWUiOjE2Mjg2MjI4NDUsImlkcCI6IlRyYW5zUGVyZmVjdEF1dGgiLCJzY29wZSI6WyJvcGVuaWQiLCJwcm9maWxlIiwiZW1haWwiLCJ1c2VybmFtZSIsImRpcmVjdG9yeSIsIkdMU2hhcmVBcGkiLCJDYXJGU0FwaSJdLCJhbXIiOlsiZXh0ZXJuYWwiXX0.ABSYw2kPXw7Qk0aiecJBKKh7yfUsN9jpAqm4-GuXxECOSsHSj-XmBbJdQwWGR7ENXb5Hj2-uLYg1gmb5MsX_7MXnOFmUynkklt8JnhvSVF0xsAxM2tv-VYjeuXT_ZsbDiU69_dpf-PpzWB--Ph3DiTy0C6HGCMeDxcY_oA01zmidP4HUhtzUVsSIuU91_QooMXina41hNl4pfjKfcpRtggHdd9-LcfKRxSrST6SefLTxOE77dz1dOX_uk08SNuhUz8cgxmiBL4xSj9V58_uVtRE1MnM_Y4MHTPXL2Kw7FjU60BDviI-TDQqk09uTERhBeWr1EM-VJqS5H4o1YZzxBQ
ExpiredPublicLink=1a76a046-ece8-4a2d-9a5a-00b09b86e1ec
ExpiredPrivateLink=0de9b25a-6708-4e92-81a3-85a32de6315d
ExpiredLinkIDPrivate_NoAccess=0227194f-b6d6-4ed6-93de-455d6bcb4cff
ExpiredLinkIDPrivate_AllAccess=b209c2e1-cbc6-4054-b22f-af70db8cec8c
BasicRegistrationLink=FBD4BF72-E519-47EB-E04A-08DC3275B90F
ProRegistrationLink=27C32AB8-9389-4E1D-E04B-08DC3275B90F
ExpiredRegistrationLink_NoShare=C5F6E2E3-F238-406A-7278-08DC4E814562
ExpiredRegistrationLink_ExpiredShare=523C11E3-58D6-4ECF-727A-08DC4E814562
ExpiredRegistrationLink_RegisteredUser=EDF97450-EE54-4D2E-727B-08DC4E814562
PatentsShareID=967bb8c2-c8f3-46c9-99cc-9e9d520a0f64
Session=System.Net.CookieContainer
Wait=TransPerfect.Automation.Framework.Wait
Second=Seconds
Millisecond=Milliseconds
Minute=Minutes
Hour=Hours
Seconds=Seconds
Milliseconds=Milliseconds
Minutes=Minutes
Hours=Hours
"""

def create_globals(globals_str: str) -> Environment:
    """
    Parse a string of assignments (one per line) and return an Environment with those variables defined.
    Example input:
        a="foo"
        b="bar"
    """
    env = Environment()
    for line in globals_str.split('\n'):
        line = line.strip()
        if not line or '=' not in line:
            continue
        var_name, value = line.split('=', 1)
        var_name = var_name.strip()
        value = value.strip()
        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        # If value contains '/api/', only keep from '/api/' onwards
        if '/api/' in value:
            value = value[value.index('/api/'):]
        env.define_variable(var_name, value)
    return env

def get_path_to_var(globals_str: str) -> dict:
    """
    Parse the globals string up to the line containing '# end of paths'.
    Return a dict where keys are the values on the right of '=', and values are the variable names (left of '='), for all lines before '# end of paths'.
    """
    path_map = {}
    for line in globals_str.split('\n'):
        line = line.strip()
        if line == '# end of paths':
            break
        if not line or '=' not in line or line.startswith('#'):
            continue
        var_name, value = line.split('=', 1)
        var_name = var_name.strip()
        value = value.strip().rstrip(';').strip().strip('"')

        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        var_name = var_name.split(" ")[3].strip()
        path_map[value.lower()] = var_name
    return path_map

class PathResolver:
    def __init__(self, paths_str: str):
        self.paths = {'plain': {}, 'formatted': {}}
        for line in paths_str.split('\n'):
            line = line.strip()
            if not line or not line.startswith('public const string'):
                continue
            # Example: public const string AdminBlackList = "/api/Admin/blacklist-organizations";
            m = re.match(r'public const string (\w+) = "([^"]+)";', line)
            if not m:
                continue
            var_name, path = m.group(1), m.group(2)
            path_lc = path.lower()
            if '{' in path and '}' in path:
                self.paths['formatted'][path_lc] = var_name
            else:
                self.paths['plain'][path_lc] = var_name

    def get_var_for_path(self, path: str):
        path_lc = path.lower()

        # If path starts with http or https, strip to portion starting from /api
        if path_lc.startswith('http://') or path_lc.startswith('https://'):
            idx = path_lc.find('/api')
            if idx != -1:
                path_lc = path_lc[idx:]
        
        # remove the query params
        idx = path_lc.find('?')
        if idx != -1:
            path_lc = path_lc[:idx]

        # 1. Check plain paths
        if path_lc in self.paths['plain']:
            return self.paths['plain'][path_lc]
        # 2. Check formatted paths
        for template, var_name in self.paths['formatted'].items():
            # Convert template to regex: replace {var} with [^/]+, escape the rest
            regex = re.sub(r'\{[^}]+\}', r'[^/]+', re.escape(template).replace(r'\{', '{').replace(r'\}', '}'))
            regex = '^' + regex + '$'
            if re.match(regex, path_lc):
                return var_name
        return None
