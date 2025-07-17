using Models.Responses;

namespace Tests.API.AdminInfo;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/Tokens/{env}.json"
)]
public sealed class Admin_User_Pricing : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/user/pricing";

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    public void GET_Admin_User_Pricing_ExternalUser_403_115206()
    {
        var token = Get<Token>(Tokens.TokenClientAPI);

        Send(
            Get(Endpoint)
            with
            { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is("Only admins allowed to retrieve the list");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void GET_Admin_User_Pricing_InternalUser_200_113687()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);

        Send(
            Get(Endpoint)
            with
            { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<PricingTypeModel> response);

        Verify(Response.StatusCode).Is(OK);

        List<PricingType> disabledTiers = new()
        {
            PricingType.ExternalPlus
        };

        for (var i = 0; i < response.Count; ++i)
        {
            Verify(response[i].Id).Is(i + 1); //IDs start at 1
            Verify(response[i].Name).Is(Enum.GetNames<PricingType>()[i]);
            var tierIsEnabled = !disabledTiers.Contains((PricingType)response[i].Id);
            Verify(response[i].IsEnabled == tierIsEnabled, $"Tier is {(tierIsEnabled ? "enabled" : "disabled")}");
        }
    }
}
