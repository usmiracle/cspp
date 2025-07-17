using Models.Requests;
using Models.Responses;
using static Tests.Mailosaur.Mailosaur;

namespace Tests.API.AdminInfo;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    @"DataProviders\{env}env.json",
    @"DataProviders\Tokens\{env}.json",
    @"DataProviders\{env}{browser}\users.json")]
[EmailConfiguration(@"Configurations/email.json")]

public sealed class Admin_Subscriptions_Trial : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/user/subscriptions/trial";

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    public void POST_Admin_Subscriptions_Trial_ExternalUser_403_126379()
    {
        var token = Get<Token>(Tokens.TokenClientAPI);

        List<string> emails = new()
        {
            "Anyuser@somewhere.com"
        };

        Send(
            Post(emails).To(Endpoint) with
            { Authorization = Bearer(token.AccessToken) });

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Only admins allowed to create trial subscriptions for users.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    [EmailTest]
    public void POST_Admin_Subscriptions_Trial_Admin_200_126381()
    {
#if !MAILOSAUR
        Assert.Ignore("Mailosaur service disabled. Emails cannot be tested.");
#endif
        var token = Get<Token>(Tokens.TokenAdminAPI);

        UserRegistrationModel toRegister = UserGenerator.New;

        //AND a registration link with no attached Share
        RegistrationLinkRequestModel linkRequest = new()
        {
            Email = toRegister.Email,
            PricingTypeId = 1,
        };

        Send(
            Post(linkRequest).To($"{GlobalLabShare}/gl-share/api/Registration")
        );

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text), "Successful response message").Succintly.Is("Registration request successfully created, please check for the link in the provided email.");
        Wait.For(AccountVerificationTo(linkRequest.Email));
        Verify(EmailMessage).IsNot(null);
        var registrationLink = GetRegistrationLink(EmailMessage)[^36..];

        Send(
           Post(toRegister).To($"{GlobalLabShare}/gl-share/api/Registration/{registrationLink}/register")
        );

        //THEN get a 200 response back
        Verify(Response.StatusCode).Is(OK);

        List<string> emails = new()
        {
            toRegister.Email
        };

        Send(
            Post(emails).To(Endpoint) with
            { Authorization = Bearer(token.AccessToken) })
        .Take(out SubscriptionsTrialResponse response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.UsersFailed.Count).Is(0);
        var addedTrialUser = response.UsersTrialCreated.Single();
        Verify(addedTrialUser.UserId).IsNot(null);
        Verify(addedTrialUser.FullName).Is($"{toRegister.FirstName} {toRegister.LastName}");
        Verify(addedTrialUser.EmailAddress).Is(toRegister.Email);
        Verify(addedTrialUser?.IsInternalUser).Is(false);
        Verify(response.Message).Is("Successfully created trial subscriptions for all users");
    }
}
