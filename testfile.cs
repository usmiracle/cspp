using TransPerfect.Automation.Framework;

[Parallelizable]
public sealed class Admin_Share_ShareLinkId : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/share";
    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}";
    private string EndpointWithParameters(int pageNumber, int pageSize) => $"{GlobalLabShare}/gl-share/api/Admin/users/pricing/{pageNumber}/{pageSize}";

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
} 