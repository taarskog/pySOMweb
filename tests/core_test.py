from logging import error
from somweb.core import DoorActionType, DoorStatus
from typing import Type
import unittest
import requests_mock
from somweb import Door, DoorStatusType, SomwebClient as Client

@requests_mock.Mocker()
class TestSomwebClient(unittest.TestCase):
    """
    Test all SOMweb integrations
    """

    def test_udi_prop_should_hold_cover_id(self, req):
        self.assertEqual(12345678, Client(12345678, "user", "password").udi)

    def test_udi_prop_should_not_be_settable(self, req):
        with self.assertRaises(BaseException):
            Client(12345678, "user", "password").udi = 87654321

    def test_udi_prop_should_not_be_deletable(self, req):
        with self.assertRaises(BaseException):
            del Client(12345678, "user", "password").udi

    def test_authenticate_sets_web_token_on_success(self, req):
        expected = "55MyToken66"
        req.post("https://12345678.somweb.world/index.php", text='BLAHBLAH\r\nBLAH<input id="webtoken" type="hidden" value="55MyToken66"/>\r\nBLAHBLAHBLAHBLAH')
        client = Client(12345678, "user", "password")
        self.assertTrue(client.authenticate())
        self.assertEqual(expected, client._SomwebClient__currentToken)

    def test_authenticate_fails_on_missing_web_token(self, req):
        expected = "55MyToken66"
        req.post("https://12345678.somweb.world/index.php", text='BLAHBLAH\r\nBLAH\r\nBLAHBLAHBLAHBLAH')
        client = Client(12345678, "user", "password")
        self.assertFalse(client.authenticate())

    def test_authenticate_fails_on_invalid_url(self, req):
        req.post("https://12345678.somweb.world/index.php", reason='Not Found', status_code=404)
        client = Client(12345678, "user", "password")
        self.assertFalse(client.authenticate())
        self.assertFalse(client._SomwebClient__currentToken)

    def test_getDoorStatus_returns_unknown_for_doors_not_available(self, req):
        req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "NOPE")
        client = Client(12345678, "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Unknown, uri)

    def test_getDoorStatus_returns_open(self, req):
        req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "FAIL")
        client = Client(12345678, "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Open, uri)

    def test_getDoorStatus_returns_closed(self, req):
        req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "OK")
        client = Client(12345678, "user", "password")
        uri = client.getDoorStatus(2)
        self.assertEqual(DoorStatusType.Closed, uri)

    def test_getDoors_returns_all_known_doors(self, req):
        expected = [Door("2", "Door2"), Door("4", "Door4")]
        client = Client(12345678, "user", "password")
        client._SomwebClient__somWebPageContent = 'BLAHBLAH\r\n<input type="submit" class="tab-door tab-door-close tab-selected" name="tab-door2" id="tab-door2" value="Door2">\r\n<input type="submit" class="tab-door tab-door-close tab-selected" name="tab-door4" id="tab-door4" value="Door4">\r\nBLAHBLAHBLAHBLAH'
        actual = client.getDoors()

        self.assertEqual(len(expected), len(actual))
        for i in range(len(actual)):
            self.assertEqual(expected[i].id, actual[i].id)
            self.assertEqual(expected[i].name, actual[i].name)

    def test_getDoors_returns_empty_list_if_no_doors_found(self, req):
        client = Client(12345678, "user", "password")
        client._SomwebClient__somWebPageContent = 'BLAHBLAH\r\nBLAHBLAHBLAHBLAH'
        self.assertEqual(0, len(client.getDoors()))

    def test_getAllDoorStatuses_returns_list_with_status_of_all_known_doors_and_updates_token(self, req):
        expected = [DoorStatus("2", DoorStatusType.Closed), DoorStatus("4", DoorStatusType.Open)]
        req.get("https://12345678.somweb.world/isg/statusDoorAll.php?webtoken=token1", text = '{"1":1,"2":"0","3":1,"4":1,"5":1,"6":1,"7":1,"8":1,"9":1,"10":1,"11":"token2"}')
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        client._SomwebClient__doors = [Door("2", "Door2"), Door("4", "Door4")]

        actual = client.getAllDoorStatuses()

        self.assertEqual("token2", client._SomwebClient__currentToken)
        self.assertEqual(len(expected), len(actual))
        for i in range(len(actual)):
            self.assertEqual(expected[i].id, actual[i].id)
            self.assertEqual(expected[i].status, actual[i].status)

    def test_toogleDoorPosition_returns_true_when_successful(self, req):
        req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        actual = client.toogleDoorPosition(2)
        self.assertTrue(actual)

    def test_toogleDoorPosition_returns_false_when_failing(self, req):
        req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "FAIL")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertFalse(client.toogleDoorPosition(2))

    def test_toogleDoorPosition_returns_false_on_invalid_url(self, req):
        req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", reason='Not Found', status_code=404)
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertFalse(client.toogleDoorPosition(2))

    def test_doorAction_returns_true_when_closing_open_door_successful(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "FAIL") # OPEN
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.doorAction(2, DoorActionType.Close))
        self.assertTrue(statusReq.called_once)
        self.assertTrue(openReq.called_once)

    def test_doorAction_returns_true_when_opening_closed_door_successful(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "OK") # CLOSED
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.doorAction(2, DoorActionType.Open))
        self.assertTrue(statusReq.called_once)
        self.assertTrue(openReq.called_once)

    def test_doorAction_returns_true_when_opening_already_open_door(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "FAIL") # OPEN
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.doorAction(2, DoorActionType.Open))
        self.assertTrue(statusReq.called_once)
        self.assertFalse(openReq.called_once)

    def test_doorAction_returns_true_when_closing_already_closed_door(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "OK") # CLOSED
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.doorAction(2, DoorActionType.Close))
        self.assertTrue(statusReq.called_once)
        self.assertFalse(openReq.called_once)

    def test_openDoor_calls_doorAction_to_open(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "OK") # CLOSED
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.openDoor(2))
        self.assertTrue(statusReq.called_once)
        self.assertTrue(openReq.called_once)

    def test_closeDoor_calls_doorAction_to_close(self, req):
        statusReq = req.get("https://12345678.somweb.world/isg/statusDoor.php?numdoor=2&status=1&bit=0", text = "FAIL") # OPEN
        openReq = req.get("https://12345678.somweb.world/isg/opendoor.php?numdoor=2&status=0&webtoken=token1", text = "OK")
        client = Client(12345678, "user", "password")
        client._SomwebClient__currentToken = 'token1'
        self.assertTrue(client.closeDoor(2))
        self.assertTrue(statusReq.called_once)
        self.assertTrue(openReq.called_once)


if __name__ == "__main__":
    unittest.main()
