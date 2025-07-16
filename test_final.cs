using NUnit.Framework;
using System.Threading.Tasks;

[TestFixture]
public class TestClass : APITest
{
    private string Endpoint = "https://api.example.com";
    private string EndpointWithShareLink = "https://api.example.com/share";

    [Test]
    public async Task TestMethod()
    {
        var shareGroup = new { Share = new { Id = "123" } };
        
        Send(Get($"{EndpointWithShareLink(shareGroup.Share.Id)}"))
            .Verify(Response.StatusCode).Is(200);
    }
} 