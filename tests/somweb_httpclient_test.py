from somweb.httpclient import HttpClient
import unittest
import requests
import requests_mock

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

#class TestSomwebClient2(AioHTTPTestCase):

# class TestSomwebClient2(AioHTTPTestCase):
#     """
#     Test http client
#     """

#     @unittest_run_loop
#     async def test(self):



# @requests_mock.Mocker()
# class TestSomwebClient(unittest.TestCase):
#     """
#     Test all SOMweb integrations
#     """

@requests_mock.Mocker()
class HttpClientTest(unittest.TestCase):
    """
    Test all SOMweb integrations
    """

    @unittest_run_loop
    async def test_get_returns_response(self, req, loop):
        req.get("https://12345678.somweb.world/fakeuri.html", text = "body_data")
        response = await HttpClient(12345678).get("/fakeuri.html")
        self.assertEqual(response, "body_data")

if __name__ == "__main__":
    unittest.main()
