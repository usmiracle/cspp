using Models.Requests;
using Models.Responses;

namespace Tests.API.AdminInfo;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/Tokens/{env}.json"
)]
public sealed class Admin_Users_Pricing_List : APITest
{
    public static int DefaultPageNumber { get; set; } = 1;
    public static int DefaultPageSize { get; set; } = 50;
    private string Endpoint => $"{EndpointWithParameters(DefaultPageNumber, DefaultPageSize)}";
    private string EndpointWithParameters(int pageNumber, int pageSize) => $"{GlobalLabShare}/gl-share/api/Admin/users/pricing/{pageNumber}/{pageSize}";

    [Test]
    [Data.SetUp(Tokens.TokenClientAPI)]
    [Recycle(Recycled.TokenClientAPI)]
    public void POST_Admin_Users_Pricing_ExternalUser_403_115203()
    {
        var token = Get<Token>(Tokens.TokenClientAPI);
        RecipientQuery query = new()
        {
            Query = "John Smith"
        };

        Send(
           Post(query).To(Endpoint)
           with
           { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Forbidden);
        Verify(Response.Content).Is("Only admins allowed to pull this list.");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_Admin_Users_Pricing_ExternalUser_QueryForName_200_233246()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        RecipientQuery query = new()
        {
            Query = "John Smith"
        };

        Send(
           Post(query).To(Endpoint)
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<UserPricingResponseModel> response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");

        Send(
           Post(query).To($"{EndpointWithParameters(1, 32)}")
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");

        Send(
           Post(query).To($"{EndpointWithParameters(3, 15)}")
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out response);

        Verify(Response.StatusCode).Is(OK);
        Verify(response.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI)]
    [Recycle(Recycled.TokenAdminAPI)]
    public void POST_Admin_Users_Pricing_ExternalUser_PageNumberPageSize_200_233247()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        RecipientQuery query = new()
        {
            Query = "John Smith"
        };

        Send(
           Post(query).To($"{EndpointWithParameters(1, 50)}")
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<UserPricingResponseModel> fullSizeResponse);

        Verify(Response.StatusCode).Is(OK);
        Verify(fullSizeResponse.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");
        Verify(fullSizeResponse.Count, "Response count matches page size").Succintly.Is(50);

        Send(
           Post(query).To($"{EndpointWithParameters(1, 10)}")
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<UserPricingResponseModel> responsePage1);

        Verify(Response.StatusCode).Is(OK);
        Verify(responsePage1.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");
        Verify(responsePage1).Is(fullSizeResponse.Take(10));

        Send(
           Post(query).To($"{EndpointWithParameters(4, 5)}")
           with
           { Authorization = Bearer(token.AccessToken) }
        ).Take(out List<UserPricingResponseModel> responsePage2);

        Verify(Response.StatusCode).Is(OK);
        Verify(responsePage2.All(u => u.FullName.Contains("John") || u.FullName.Contains("Smith")), "All users match query");
        Verify(responsePage2).Is(fullSizeResponse.Skip(15).Take(5));
    }
}
