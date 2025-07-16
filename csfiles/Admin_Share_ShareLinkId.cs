using Models.Responses;

namespace Tests.API.ApprovalLinks;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/fileConfig.json",
    "DataProviders/Tokens/{env}.json"
)]

public sealed class Admin_Share_ShareLinkId : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/share";

    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Shares.KkomradeNoMessage)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void GET_AdminShare_DisabledShare_200_141460()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var shareGroup = Get<ShareGroup>(Shares.KkomradeNoMessage);

        Send(
            Get($"{EndpointWithShareLink(shareGroup.Share.Id)}") with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out AdminShareResponse adminShareResponse);

        Verify(Response.StatusCode).Is(OK);
        Verify(adminShareResponse.Id).Is(shareGroup.Share.Id);
        Verify(adminShareResponse.IsDisabled).Is(false);

        Send(
             Patch(new { }.As(SerializationFormat.Json))
             .To($"{EndpointWithShareLink(shareGroup.Share.Id)}/disability") with
             { Authorization = Bearer(token.AccessToken) }
         );

        Send(
            Get($"{EndpointWithShareLink(shareGroup.Share.Id)}") with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out AdminShareResponse adminShareResponseDisabled);

        Verify(Response.StatusCode).Is(OK);
        Verify(adminShareResponseDisabled.Id).Is(shareGroup.Share.Id);
        Verify(adminShareResponseDisabled.IsDisabled).Is(true);
        Verify(adminShareResponse with { IsDisabled = true }, "All other share details match").Succintly.Is(adminShareResponseDisabled);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void GET_AdminShare_ExpiredShare_410_141477()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        Send(
            Get($"{EndpointWithShareLink(ExpiredPrivateLink)}") with
            { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Gone);
    }
}
