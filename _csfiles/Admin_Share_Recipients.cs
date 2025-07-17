namespace Tests.API.ApprovalLinks;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/fileConfig.json",
    "DataProviders/Tokens/{env}.json"
)]

public sealed class Admin_Share_Recipients : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/share";

    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}/recipients";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenBasicUserAPI, Shares.KkomradeNoMessage)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_AdminShareRecipients_AddRecipient_200_141306()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var shareGroup = Get<ShareGroup>(Shares.KkomradeNoMessage);
        Models.User toAdd = Get<Models.User>(Users.BasicTierUser);
        Recipient recipient = (Recipient)toAdd with
        {
            UserWhoAddedRecipient = token.User.Email,
            SendEmail = false,
        };

        var shareResponseBeforeAdd = shareGroup.GetShareResponse();

        Verify(shareResponseBeforeAdd?.Recipients.Any(r => r.EmailAddress == toAdd.Email), "Share does not contain recipient").Succintly.Is(false);

        Send(
            Post<List<Recipient>>([recipient]).To(EndpointWithShareLink(shareGroup.Share.Id)) with
            { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"Recipients have been added to {shareGroup.Share.Id}.");

        var shareResponseAfterAdd = shareGroup.GetShareResponse();

        Verify(shareResponseAfterAdd?.Recipients.Any(r => r.EmailAddress == toAdd.Email), "Share contains added recipient").Succintly.Is(true);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenBasicUserAPI, Shares.MaxRecipientsBeeFromProPaid)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_AdminShareRecipients_AddRecipientToMaxShare_400_141309()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var shareGroup = Get<ShareGroup>(Shares.MaxRecipientsBeeFromProPaid);
        Models.User toAdd = Get<Models.User>(Users.BasicTierUser);
        Recipient recipient = (Recipient)toAdd with
        {
            UserWhoAddedRecipient = token.User.Email,
            SendEmail = false,
        };

        var shareResponseBeforeAdd = shareGroup.GetShareResponse();
        Verify(shareResponseBeforeAdd.Recipients.Count).Is(50);
        Verify(shareResponseBeforeAdd?.Recipients.Any(r => r.UserResponse?.EmailAddress == toAdd.Email), "Share does not contain recipient").Succintly.Is(false);

        Send(
            Post<List<Recipient>>([recipient]).To(EndpointWithShareLink(shareGroup.Share.Id)) with
            { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"It looks like you added too many recipients, this Restricted share has 50 recipients and can only have 0 more added.");

        var shareResponseAfterAdd = shareGroup.GetShareResponse();
        Verify(shareResponseAfterAdd.Recipients.Count).Is(50);
        Verify(shareResponseAfterAdd?.Recipients.Any(r => r.UserResponse?.EmailAddress == toAdd.Email), "Share does not contain recipient").Succintly.Is(false);
    }
}
