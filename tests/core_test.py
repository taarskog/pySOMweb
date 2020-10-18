import unittest
import requests_mock
from somweb import DoorStatusType, SomwebClient as Client

@requests_mock.Mocker()
class TestSomwebClient(unittest.TestCase):
    """
    Test all SOMweb integrations
    """

    def test_authenticate_sets_web_token_on_success(self, req):
        expected = "55MyToken66"
        req.post("https://test.somweb.world/index.php", text='BLAHBLAH\r\nBLAH<input id="webtoken" type="hidden" value="55MyToken66"/>\r\nBLAHBLAHBLAHBLAH')
        client = Client("https://test.somweb.world", "user", "password")
        self.assertTrue(client.authenticate())
        self.assertEqual(expected, client._SomwebClient__token)

    def test_authenticate_fails_on_missing_web_token(self, req):
        expected = "55MyToken66"
        req.post("https://test.somweb.world/index.php", text='BLAHBLAH\r\nBLAH\r\nBLAHBLAHBLAHBLAH')
        client = Client("https://test.somweb.world", "user", "password")
        self.assertFalse(client.authenticate())

    def test_authenticate_fails_on_invalid_url(self, req):
        req.post("https://test.somweb.world/index.php", reason='Not Found', status_code=404)
        client = Client("https://test.somweb.world", "user", "password")
        self.assertFalse(client.authenticate())
        self.assertFalse(client._SomwebClient__token)

    def test_getDoorStatus_returns_unknown_for_doors_not_available(self, req):
        req.get("https://test.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "NOPE")
        client = Client("https://test.somweb.world", "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Unknown, uri)

    def test_getDoorStatus_returns_open(self, req):
        req.get("https://test.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "OK")
        client = Client("https://test.somweb.world", "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Open, uri)

    def test_getDoorStatus_returns_closed(self, req):
        req.get("https://test.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "FAIL")
        client = Client("https://test.somweb.world", "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Closed, uri)


if __name__ == "__main__":
    unittest.main()
