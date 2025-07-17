using Models.Responses;

namespace Tests.API.ApprovalLinks;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/fileConfig.json",
    "DataProviders/Tokens/{env}.json"
)]

public sealed class AdminInfo : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/info";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void GET_AdminInfo_ValidResponse_200_125388()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        Send(
          Get($"{Endpoint}") with
          { Authorization = Bearer(token.AccessToken) }
        ).Take(out AdminInfoResponse response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.BlacklistOrganizations).IsNot(null);
        Verify(response.UnsuccessfullyRegisteredUsers).IsNot(null);
    }
}
