using Models.Requests;
using Models.Responses;

namespace Tests.API.AdminInfo;

[NonParallelizable]
[ReadFrom(
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/{env}env.json",
    "DataProviders/Tokens/{env}.json"
)]
public sealed class Admin_Internal_Pricing_Update : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/user/internal/pricing";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_Admin_InternalPricing_ExternalUser_400_133203()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Models.User>(Users.BasicTierUser);

        List<PricingType> types = new()
        {
            PricingType.Free,
            PricingType.Pro,
            PricingType.InternalPlus
        };

        foreach (var type in types)
        {
            UpdateExternalUserPricingModel request = new()
            {
                UserId = int.Parse(subject.Id),
                PricingTypeId = (int)type
            };

            Send(
                Post(request).To(Endpoint)
                with
                { Authorization = Bearer(admin.AccessToken) }
            );

            Verify(Response.StatusCode).Is(BadRequest);
            Verify(Response.Content).Is("Invalid user passed for internal user pricing type updates. Only internal users are supported");
        }
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_Admin_InternalPricing_InternalUser_InvalidRequest_400_133202()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Models.User>(Users.InternalUser1);

        UpdateExternalUserPricingModel requestFree = new()
        {
            UserId = int.Parse(subject.Id),
            PricingTypeId = (int)PricingType.Free
        };
        var requestPro = requestFree with
        {
            PricingTypeId = (int)PricingType.Pro
        };
        var requestInternalPlus = requestFree with
        {
            PricingTypeId = (int)PricingType.InternalPlus
        };

        Send(
            Post(requestFree).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"Invalid pricing type passed for updating pricing type of user with email {subject.Email}. Internal users cannot be assigned the pricing type {requestFree.PricingTypeId}: {(PricingType)requestFree.PricingTypeId}");

        //Send twice in both cases to get "already assigned user" response
        Send(
           Post(requestPro).To(Endpoint)
           with
           { Authorization = Bearer(admin.AccessToken) }
        );
        if (Response.StatusCode == OK)
        {
            Send(
               Post(requestPro).To(Endpoint)
               with
               { Authorization = Bearer(admin.AccessToken) }
            );
        }
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"Pricing type {requestPro.PricingTypeId}: {(PricingType)requestPro.PricingTypeId} is already assigned to user.");


        Send(
           Post(requestInternalPlus).To(Endpoint)
           with
           { Authorization = Bearer(admin.AccessToken) }
        );
        if (Response.StatusCode == OK)
        {
            Send(
               Post(requestInternalPlus).To(Endpoint)
               with
               { Authorization = Bearer(admin.AccessToken) }
            );
        }
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"Pricing type {requestInternalPlus.PricingTypeId}: {(PricingType)requestInternalPlus.PricingTypeId} is already assigned to user.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_Admin_InternalPricing_InternalUser_200_133201()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var user = Get<Models.User>(Users.InternalUser2);

        UpdateExternalUserPricingModel request = new()
        {
            UserId = int.Parse(user.Id),
            PricingTypeId = (int)PricingType.InternalPlus,
        };

        //As setup, set user to InternalPlus
        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(token.AccessToken) }
        );

        request = request with
        {
            PricingTypeId = (int)PricingType.Pro,
        };

        Send(
           Post(request).To(Endpoint)
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out UserPricingResponseModel response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.PricingTypeId).Is((int)PricingType.Pro);
        Verify(response.PricingType.Id, "Pricing Type object ID").Is((int)PricingType.Pro);
        Verify(response.PricingType.Name).Is(PricingType.Pro.ToString());

        request = request with
        {
            PricingTypeId = (int)PricingType.InternalPlus,
        };

        Send(
           Post(request).To(Endpoint)
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.PricingTypeId).Is((int)PricingType.InternalPlus);
        Verify(response.PricingType.Id, "Pricing Type object ID").Is((int)PricingType.InternalPlus);
        Verify(response.PricingType.Name).Is(PricingType.InternalPlus.ToString());
    }
}
