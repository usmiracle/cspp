using Models.Requests;
using Models.Responses;

namespace Tests.API.Share;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/Tokens/{env}.json",
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/fileConfig.json",
    "DataProviders/personalShares.json"
)]
public sealed class Share_shareLink : APITest
{
    // GET SECTION
    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void GET_Share_ShareLink_Private_Auth_200_49231()
    {
        //GIVEN a private share linkID that has not expired
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);
        var share = shareGroup.Share;
        var user = shareGroup.Token.User;

        //AND send a Get request to api/Download/archive/{linkID} with auth
        Send(
            Get(ShareAPI + "/" + share.Id + APIVersion) with
            { Authorization = Bearer(shareGroup.Token.AccessToken) }
        ).Take(out ShareResponse getResponse);

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //AND THEN we receive back a body containing information about the share
        Verify(getResponse.Id).Is(share.Id);
        Verify(getResponse.Username).Is(user.Email);
        Verify(getResponse.Files).Is(share.Files.Select(e => e with { LocalPath = null }).ToList());
        Verify(getResponse.Recipients).Is(null);
        Verify(getResponse.Source).Is(share.Source);
        Verify(getResponse.Notes).Is(share.Notes);
        Verify(getResponse.FullName).Is($"{user.FirstName} {user.LastName}");
        Verify(getResponse.IsPublic).Is(share.IsPublic);
        var expectedCreation = DateTime.SpecifyKind(getResponse.CreateDate.Value, DateTimeKind.Utc);
        Verify(expectedCreation).IsWithin(TimeSpan.FromMinutes(1));
        TimeSpan expectedExpiration = getResponse.Expiration.Value.Subtract(expectedCreation);
        Verify(expectedExpiration.Days).Is(1);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void GET_Share_ShareLink_Private_NoAuth_403_49233()
    {
        //GIVEN a private share linkID that has not expired

        //AND send a Get request to api/Download/archive/{linkID} without auth
        Send(Get(ShareAPI + "/" + Get<ShareGroup>(Shares.BeeNoMessagePrivate).Share.Id + APIVersion));

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(Forbidden);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void GET_Share_ShareLink_Private_BadAuth_403_49383()
    {
        //GIVEN a private share linkID that has not expired
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);

        //AND send a Get request to api/Download/archive/{linkID} without auth
        Send(Get(ShareAPI + "/" + shareGroup.Share.Id + APIVersion) with
        { Authorization = Bearer(shareGroup.Token.AccessToken[..^1]) });

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(Forbidden);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    [Category("Unused"), Ignore("Obsolete - API Version test")]
    public void GET_Share_ShareLink_Private_NoApiVersion_400_49389()
    {
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);
        //GIVEN a private share linkID that has not expired

        //AND send a Get request to api/Download/archive/{linkID} without auth
        Send(
            Get(ShareAPI + "/" + shareGroup.Share.Id) with
            { Authorization = Bearer(shareGroup.Token.AccessToken) }
        ).Take(out BadHttpResponse response);

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(response).IsNot(null);
        Verify(response.Error?.Code).Is("ApiVersionUnspecified");
        Verify(response.Error?.Message).Is("An API version is required, but was not specified.");
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    [Category("Unused"), Ignore("Obsolete - API Version test")]
    public void GET_Share_ShareLink_Private_UnsupportedApiVersion_403_49390()
    {
        //GIVEN a private share linkID that has not expired
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);
        var downloadLink = shareGroup.Share.Id;

        //AND send a Get request to api/Download/archive/{linkID} without auth
        Send(
            Get(ShareAPI + "/" + downloadLink + APIVersion + "1") with
            { Authorization = Bearer(shareGroup.Token.AccessToken) }
        ).Take(out BadHttpResponse response);

        //THEN get a 403 response back
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(response).IsNot(null);
        Verify(response.Error?.Code).Is("UnsupportedApiVersion");
        Verify(response.Error?.Message).Is($"The HTTP resource that matches the request URI 'http://{GlobalLabShareNoHTTPS}/gl-share/api/Share/{downloadLink}' does not support the API version '11'.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    public void GET_Share_ShareLink_PrivateExpiredAuth_410_49230()
    {
        //GIVEN a private share linkID that has not expired

        //AND send a Get request to api/Download/archive/{linkID} with auth
        var token = Get<Token>(Tokens.TokenClientAPI);
        Send(
            Get(ShareAPI + "/" + ExpiredPrivateLink + APIVersion) with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out BadHttpResponse response);

        //THEN get a 410 response back
        Verify(Response.StatusCode).Is(Gone);
        Verify(response).IsNot(null);
        Verify(response.Status).Is("410");
        Verify(response.TraceId).Matches(TraceIdRegex);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePublic)]
    public void GET_Share_ShareLink_Public_200_49172()
    {
        //GIVEN a public share linkID that has not expired
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePublic);
        var share = shareGroup.Share;
        var token = shareGroup.Token;

        //AND send a Get request to api/Download/archive/{linkID}
        Send(Get(ShareAPI + "/" + share.Id + APIVersion))
            .Take(out ShareResponse getResponse);

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        //AND THEN we receive back a body containing information about the share
        Verify(getResponse.Id).Is(share.Id);
        Verify(getResponse.Username).Is(token.User.Email);
        Verify(getResponse.Files).Is(share.Files.Select(e => e with { LocalPath = null }).ToList());
        Verify(getResponse.Recipients).Is(null);
        Verify(getResponse.Source).Is(share.Source);
        Verify(getResponse.Notes).Is(share.Notes);
        Verify(getResponse.FullName).Is($"{token.User.FirstName} {token.User.LastName}");
        Verify(getResponse.IsPublic).Is(share.IsPublic);
        var expectedCreation = DateTime.SpecifyKind(getResponse.CreateDate.Value, DateTimeKind.Utc);
        Verify(expectedCreation).IsWithin(TimeSpan.FromMinutes(1));
        TimeSpan expectedExpiration = getResponse.Expiration.Value.Subtract(expectedCreation);
        Verify(expectedExpiration.Days).Is(1);
    }

    [Test]
    public void GET_Share_ShareLink_PublicExpired_410_48979()
    {
        //GIVEN a public share linkID that is expired

        //AND send a Get request to /api/Share/{shareLink}
        Send(Get(ShareAPI + "/" + ExpiredPublicLink + APIVersion)).
            Take(out BadHttpResponse response);

        //THEN get a 410 response back
        Verify(Response.StatusCode).Is(Gone);
        Verify(response).IsNot(null);
        Verify(response.Status).Is("410");
        Verify(response.TraceId).Matches(TraceIdRegex);
    }

    [Test]
    public void GET_Share_ShareLink_DoesNotExist_49304()
    {
        Send(Get(ShareAPI + "/" + Get<string>("expiredLinkIDNotExist") + APIVersion)).
            Take(out BadHttpResponse response);

        Verify(Response.StatusCode).Is(NotFound);
        Verify(response).IsNot(null);
        Verify(response.Type).Is("https://tools.ietf.org/html/rfc9110#section-15.5.5");
        Verify(response.Title).Is("Not Found");
        Verify(response.Status).Is("404");
        Verify(response.TraceId).Matches(TraceIdRegex);
    }

    [Test]
    [Data.SetUp(Shares.NoFiles)]
    public void GET_Share_ShareLink_NoFiles_49411()
    {
        var callSuccessCode = Get<ShareGroup>(Shares.NoFiles).SuccessCode;
        Verify(callSuccessCode).Is(BadRequest);
    }

    [Test]
    [Data.SetUp(PersonalShares.AdminToClient_KKomrade)]
    public void GET_Share_ShareLink_PersonalShare_Creator_403_128871()
    {
        var share = Get<PersonalShare>(PersonalShares.AdminToClient_KKomrade);
        var response = new { IsPersonalShare = (bool?)null };

        Send(Get(ShareAPI + "/" + share.Id) with
        { Authorization = Bearer(share.Sender.AccessToken) })
        .Take(out response);

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(response.IsPersonalShare);
    }

    [Test]
    [Data.SetUp(Users.AdminUser, PersonalShares.AdminToClient_KKomrade)]
    public void GET_Share_ShareLink_PersonalShare_Recipient_200_128873()
    {
        var share = Get<PersonalShare>(PersonalShares.AdminToClient_KKomrade);
        Models.User creator = Get<Models.User>(Users.AdminUser);
        var recipient = Get<Token>(Tokens.TokenClientAPI);

        Send(Get(ShareAPI + "/" + share.Id) with
        { Authorization = Bearer(share.Recipient.AccessToken) })
        .Take(out ShareResponse response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.Id).Is(share.Id);
        Verify(response.Username).Is(creator.Email);
        Verify(response.Files.Count).Is(1);
        Verify(response.Files.Select(f => f.Path).First(), "Share's file path").EndsWith("KKomrade.jpg");
        Verify(response.Recipients).Is(null);
        Verify(response.Source).Is("glshare");
        Verify(response.Notes).Is("Here's that KKomrade file");
        Verify(response.FullName).Is(creator.FullName);
        Verify(response.IsPublic).Is(false);
        var expectedCreation = DateTime.SpecifyKind(response.CreateDate.Value, DateTimeKind.Utc);
        Verify(expectedCreation).IsWithin(TimeSpan.FromMinutes(1));
        TimeSpan expectedExpiration = response.Expiration.Value.Subtract(expectedCreation);
        Verify(expectedExpiration.Days).Is(14);
        Verify(response.IsRestrictedToOwner).Is(false);
        Verify(response.ProjectAInformation?.Any(), "Project A Info is empty").Succintly.Is(false);
        Verify(response.StorageLocation).Is("US");
        Verify(response.IsEmailSentToRecipients).Is(true);
        Verify(response.PendingApprovalLinks).Is(null);
        Verify(response.CanRecipientsGrantAccess).Is(null);
        Verify(response.IsPersonalShare).Is(true);
    }

    [Test, Data.SetUp(PersonalShares.AdminToMailosaur1_KKomrade)]
    public void GET_Share_ShareLink_AnonymousUserCreatesPersonalShare_400_143915()
    {
        var original = Get<PersonalShare>(PersonalShares.AdminToMailosaur1_KKomrade);

        InitiatePersonalShareModel toCreate = new()
        {
            Files = [.. original.Files],
            PersonalShareUsername = original.Recipient.User.PersonalShareUsername,
            StorageLocation = "US",
            Notes = "Here's an anonymous personal share for you",
            CreatorEmailAddress = Get<Models.User>(Users.BasicTierUser).Email
        };
        var response = new { type = "", message = "" };
        Send(
            Post(toCreate).To($"{GlobalLabShare}/gl-share/api/PersonalShare")
        //no auth -- share is created anonymously 
        ).Take(out response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.type).Is("MetadataId");
        Verify(response.message, "Metadata ID matches valid format").Succintly.Matches(ShareLinkNoSRegex);

        Send(
            Get(ShareAPI + "/" + SQL.GetShareLinkIdFromMetadata(response.message)) with
            { Authorization = Bearer(original.Recipient.AccessToken) });

        Verify(Response.StatusCode).Is(BadRequest);
    }

    // OPTIONS section

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void OPTIONS_Share_ShareLink_Private_Auth_403_49470()
    {
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);

        Send(
            Options(ShareAPI + "/" + shareGroup.Share.Id + APIVersion) with
            { Authorization = Bearer(shareGroup.Token.AccessToken) }
         );

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void OPTIONS_Share_ShareLink_Private_NoAuth_403_49471()
    {
        Send(Options(ShareAPI + "/" + Get<ShareGroup>(Shares.BeeNoMessagePrivate).Share.Id + APIVersion));

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    public void OPTIONS_Share_ShareLink_Private_BadAuth_403_49472()
    {
        var shareGroup = Get<ShareGroup>(Shares.BeeNoMessagePrivate);

        Send(Options(ShareAPI + "/" + shareGroup.Share.Id + APIVersion) with
        { Authorization = Bearer(shareGroup.Token.AccessToken[..^1]) });

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    [Category("Unused"), Ignore("Obsolete - API Version test")]
    public void OPTIONS_Share_ShareLink_Private_NoApiVersion_400_49473()
    {
        Send(Options(ShareAPI + "/" + Get<ShareGroup>(Shares.BeeNoMessagePrivate).Share.Id)).
            Take(out BadHttpResponse response);

        Verify(Response.StatusCode).Is(BadRequest);
        Verify(response).IsNot(null);
        Verify(response.Error?.Code).Is("ApiVersionUnspecified");
        Verify(response.Error?.Message).Is("An API version is required, but was not specified.");
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePrivate)]
    [Category("Unused"), Ignore("Obsolete - API Version test")]
    public void OPTIONS_Share_ShareLink_Private_UnsupportedApiVersion_400_49475()
    {
        var downloadLink = Get<ShareGroup>(Shares.BeeNoMessagePrivate).Share.Id;

        Send(Options(ShareAPI + "/" + downloadLink + APIVersionBad)).
            Take(out BadHttpResponse response);

        Verify(Response.StatusCode).Is(BadRequest);
        Verify(response).IsNot(null);
        Verify(response.Error?.Code).Is("UnsupportedApiVersion");
        Verify(response.Error?.Message).Is($"The HTTP resource that matches the request URI 'http://{GlobalLabShareNoHTTPS}/gl-share/api/Share/{downloadLink}' does not support the API version '{APIVersionBad[^1]}'.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    public void OPTIONS_Share_ShareLink_PrivateExpiredAuth_403_49478()
    {
        Token token = Get<Token>(Tokens.TokenClientAPI);

        Send(Options(ShareAPI + "/" + ExpiredLinkIDPrivate_AllAccess + APIVersion)
            with
        { Authorization = Bearer(token.AccessToken) });

        Verify(Response.StatusCode).Is(Forbidden);
    }

    [Test]
    public void OPTIONS_Share_ShareLink_PrivateExpiredNoAuth_403_49479()
    {
        Send(Options(ShareAPI + "/" + ExpiredLinkIDPrivate_NoAccess + APIVersion));

        Verify(Response.StatusCode).Is(Forbidden);
    }

    [Test]
    [Data.SetUp(Shares.BeeNoMessagePublic)]
    public void OPTIONS_Share_ShareLink_Public_200_49480()
    {
        Send(Options(ShareAPI + "/" + Get<ShareGroup>(Shares.BeeNoMessagePublic).Share.Id + APIVersion));

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    public void OPTIONS_Share_ShareLink_PublicExpired_200_49481()
    {
        Send(Options(ShareAPI + "/" + ExpiredPublicLink + APIVersion));

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content).Is(string.Empty);
    }

    [Test]
    public void OPTIONS_Share_ShareLink_DoesNotExist_403_49482()
    {
        Send(Options(ShareAPI + "/" + Get<string>("expiredLinkIDNotExist") + APIVersion));

        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content).Is("It looks like you entered an invalid shareLinkId");
    }

    [Test]
    [Data.SetUp(Shares.NoFiles)]
    public void OPTIONS_Share_ShareLink_NoFiles_49484()
    {
        var callSuccessCode = Get<ShareGroup>(Shares.NoFiles).SuccessCode;
        Verify(callSuccessCode).Is(BadRequest);
    }
}
