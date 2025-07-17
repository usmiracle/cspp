using Microsoft.OpenApi.Models;
using Models.Requests;
using Models.Responses;
using TransPerfect.Automation.Framework.Swagger;

namespace Tests.API.AdminInfo;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    @"DataProviders\{env}env.json",
    @"DataProviders\Tokens\{env}.json",
    @"DataProviders\{env}{browser}\users.json")]
public sealed class Admin_BlackList : APITest
{
    [Test]
    public void GET_AdminBlacklist_NoAuth_401_106508()
    {
        //GET the users blacklist
        Send(
            Get(AdminBlackListAPI)
        );

        //THEN get a 401 response back, with no content
        Verify(Response.StatusCode).Is(Unauthorized);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    public void GET_UserBlacklist_NotAdminAuth_403_106509()
    {
        var token = Get<Token>(Tokens.TokenClientAPI);

        //GET the users blacklist
        Send(
             Get(AdminBlackListAPI) with
             { Authorization = Bearer(token.AccessToken) });

        //THEN get a 403 response back, with a message
        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is("Only admins allowed to retrieve the list");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void GET_AdminBlacklist_Admin_200_106510()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        //GET the users blacklist
        Send(
            Get(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<BlacklistOrgsResponseModel> blacklistOrgs);

        //THEN get a 200 response back, with BlacklistOrgs
        Verify(Response.StatusCode).Is(OK);
        Verify(blacklistOrgs).IsNot(null);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_AddAndDelete_AdminBlacklist_Admin_200_106515()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        string organizationName = DateTime.Now.ToString() + "Valid";

        //POST to add new organization to blacklist
        Send(
        Post(new BlacklistOrgsRequestModel(organizationName, false)).To(AdminBlackListAPI) with
        { Authorization = Bearer(token.AccessToken) }
    ).Take(out BlacklistOrgsResponseModel blacklistOrg);

        Verify(blacklistOrg.Organization).Is(organizationName);

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //GET the blacklist
        Send(
            Get(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<BlacklistOrgsResponseModel> blacklistOrgs);

        //THEN get a 200 response back and verify that a new organization in a list
        Verify(Response.StatusCode).Is(OK);
        Verify(blacklistOrgs.Select(e => e.Organization), "List of organization names").Contains(organizationName);

        //POST to delete organization from blacklist
        Send(
        Post(new BlacklistOrgsRequestModel(organizationName, true)).To(AdminBlackListAPI) with
        { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //GET the blacklist
        Send(
            Get(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out blacklistOrgs);

        //THEN get a 200 response back and verify that the organization is not in a list
        Verify(Response.StatusCode).Is(OK);
        Verify(blacklistOrgs.Select(e => e.Organization), "List of organization names").DoesNotContain(organizationName);
    }

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 403)]
    public void POST_AdminBlacklist_NotAdmin_403_106518()
    {
        var token = Get<Token>(Tokens.TokenClientAPI);
        string organizationName = DateTime.Now.ToString();

        //POST to add new organization to blacklist
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, false)).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is("Only admins allowed to update this list");

        //POST to delete organization from blacklist
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, true)).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is("Only admins allowed to update this list");
    }

    [Test]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 401)]
    public void POST_AdminBlacklist_NoAuth_401_106519()
    {
        string organizationName = DateTime.Now.ToString();

        //POST to add new organization to blacklist
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, false)).To(AdminBlackListAPI));

        //THEN get a 401 response back
        Verify(Response.StatusCode).Is(Unauthorized);
        Verify(Response.Content).Is(string.Empty);

        //POST to delete organization from blacklist
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, true)).To(AdminBlackListAPI));

        //THEN get a 401 response back
        Verify(Response.StatusCode).Is(Unauthorized);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 400)]
    public void POST_AdminBlacklist_InvalidParams_400_106526()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        //POST to add new organization to blacklist (no organization)
        Send(
            Post(new { isDelete = false }).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 400 response back
        Verify(Response.StatusCode).Is(BadRequest);

        //POST to delete organization from blacklist (no organization)
        Send(
            Post(new { isDelete = true }).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 400 response back
        Verify(Response.StatusCode).Is(BadRequest);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 400)]
    public void POST_AdminBlacklist_NoBodyParams_400_106524()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        //POST to delete organization from blacklist (no body)
        Send(
        Post(string.Empty).To(AdminBlackListAPI) with
        { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 401 response back
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content, "Error Message").Contains("A non-empty request body is required.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 404)]
    public void POST_Delete_AdminBlacklist_NotExistingOrganization_404_106521()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        string organizationName = DateTime.Now.ToString() + "NotExisting";


        //POST to delete organization from blacklist (not existing)
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, true)).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 400 response back
        Verify(Response.StatusCode).Is(NotFound);
        Verify(Response.ReasonPhrase).Is("Not Found");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 400)]
    public void POST_Add_AdminBlacklist_ExistingOrganization_400_106523()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        string organizationName = DateTime.Now.ToString() + "Existing";

        //POST to add new organization to blacklist
        Send(
           Post(new BlacklistOrgsRequestModel(organizationName, false)).To(AdminBlackListAPI) with
           { Authorization = Bearer(token.AccessToken) }
       );

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //POST to add same organization to blacklist
        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, false)).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 400 response back
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.ReasonPhrase).Is("Bad Request");

        Send(
            Post(new BlacklistOrgsRequestModel(organizationName, true)).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.AdminBlackList, Operation = OperationType.Post, ResponseCode = 200)]
    public void POST_AdminBlacklist_NoIsDeleteParam_200_106630()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var organization = DateTime.Now.ToString();

        //POST to add new organization to blacklist (no delete parameter)
        Send(
            Post(new { organizationName = organization }).To(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out BlacklistOrgsResponseModel blacklistOrg);

        // Verify response has organization name
        Verify(blacklistOrg.Organization).Is(organization);

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //GET the blacklist
        Send(
            Get(AdminBlackListAPI) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<BlacklistOrgsResponseModel> blacklistOrgs);

        //THEN get a 200 response back and verify that a new organization in a list
        Verify(Response.StatusCode).Is(OK);
        Verify(blacklistOrgs.Select(e => e.Organization), "List of organization names").Contains(organization);

        //POST to delete organization from blacklist
        Send(
        Post(new BlacklistOrgsRequestModel(organization, true)).To(AdminBlackListAPI) with
        { Authorization = Bearer(token.AccessToken) }
        );

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);
    }
}
