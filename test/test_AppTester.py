import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppTester

app_device = "tester"

def test_apptester():
    """
    testing of constructor init data
    """
    ab = AppTester.CAppTester(app_device)
    assert ab.device == app_device
    assert ab.bdevice == b"tester"
    assert ab.client_id == "contXtester"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://api.github.com/repos/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.subscribe_cmnd_version_msg == b'contX/tester/cmnd/version'

    # multi pin command messages
    assert ab.topic_cmnd_setpinmode_msg == b'contX/tester/cmnd/setpinmode' #/Dx
    assert ab.topic_cmnd_getpinmode_msg == b'contX/tester/cmnd/getpinmode' #/Dx
    assert ab.topic_cmnd_setpin_msg == b'contX/tester/cmnd/setpin'         #/Dx
    assert ab.topic_cmnd_getpin_msg == b'contX/tester/cmnd/getpin'         #/Dx
    assert ab.topic_cmnd_publishpin_msg == b'contX/tester/cmnd/publishpin' #/Dx
    assert ab.topic_cmnd_statepin_msg == b'contX/tester/cmnd/statepin'     #/Dx

    assert ab.topic_statepin_msg == b'contX/tester/statepin'               #/Dx

@patch("AppTester.machine.Pin")
def test_set_pinmode(mock_machine):
    """
    """
    ab = AppTester.CAppTester(app_device)
    assert ab.set_pinmode("D4","IN") == True
    mock_machine.assert_called_with(AppTester.CAppTester.D4,ab.pinmode_in)
    assert ab.pin_map['D4']['Mode'] == "IN"
    assert ab.set_pinmode("D6","OUT",1) == True
    mock_machine.assert_called_with(AppTester.CAppTester.D6,ab.pinmode_out)
    assert ab.pin_map['D6']['Mode'] == "OUT"
    assert ab.pin_map['D6']['State'] == 1
    assert ab.set_pinmode("D8","OUT") == False
    assert ab.set_pinmode("D6","x") == False

@patch("AppBase.network.WLAN")
@patch("AppTester.umqtt.simple.MQTTClient")
@patch("AppTester.machine.Pin")
def test_publish_pin_state(mock_machine,mock_umqtt,mock_network):
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    assert ab.set_pinmode("D6","OUT",1) == True
    assert ab.publish_pin_state("D6") == True
    mock_umqtt.return_value.publish.assert_called_with(b"contX/tester/statepin/D6",'1')
    assert ab.publish_pin_state("Dx") == False


@patch("AppBase.network.WLAN")
@patch("AppTester.machine.Pin")
def test_set_pin(mock_machine,mock_network):
    """
    test handling of set pin:
    """
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    ab.set_pinmode("D6","OUT",0)
    assert ab.set_pin("D6",1) == True
    assert ab.set_pin("D4",1) == False
    assert ab.set_pin("Dx",1) == False

@patch("AppBase.network.WLAN")
@patch("AppTester.machine.Pin")
def test_get_pin(mock_machine,mock_network):
    """
    test handling of read pin:
    """
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    ab.set_pinmode("D6","OUT",0)
    ab.set_pinmode("D4","IN")
    mock_machine.return_value.value.return_value = 1
    assert ab.get_pin("D4") == [1,True]
    assert ab.pin_map["D4"]["State"] == 1
    mock_machine.return_value.value.return_value = 0
    assert ab.get_pin("D4") == [0,True]
    assert ab.get_pin("D6") == [-1,False]
    assert ab.get_pin("Dx") == [-1,False]
    mock_machine.return_value.value.assert_called()


@patch("AppBase.network.WLAN")
@patch("AppTester.umqtt.simple.MQTTClient")
@patch("AppTester.machine.Pin")
def test_publish_in_pins(mock_machine,mock_umqtt,mock_network):
    """
    tests publishing of pins with input mode on change of input
    """
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    mock_machine.return_value.value.return_value = 1
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/setpinmode/D6",b"IN")
    ab.publish_in_pins()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/tester/statepin/D6",'1')
    ab.publish_in_pins()
    mock_umqtt.reset_mock()
    mock_umqtt.return_value.publish.assert_not_called()
    mock_machine.return_value.value.return_value = 0
    ab.publish_in_pins()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/tester/statepin/D6",'0')


@patch("AppBase.network.WLAN")
@patch("AppTester.CAppTester.get_pin")
@patch("AppTester.CAppTester.set_pin")
@patch("AppTester.umqtt.simple.MQTTClient")
@patch("AppTester.machine.Pin")
def test_tester_subscribe_cb(mock_machine,mock_umqtt,mock_setpin,mock_getpin,mock_network):
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    # testing of setpinmode
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/setpinmode/D4",b"OUT")
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/setpin/D4",b'1')
    mock_setpin.assert_called_with("D4",'1')
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/setpin/D6",b'1')
    mock_setpin.assert_called_with("D6",'1')


@patch("AppBase.network.WLAN")
@patch("AppTester.umqtt.simple.MQTTClient")
@patch("AppTester.machine.Pin")
def test_tester_getpin_subscribe_cb(mock_machine,mock_umqtt,mock_network):
    # testing of getpin
    ab = AppTester.CAppTester(app_device)
    ab.begin()
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/setpinmode/D6",b"IN")
    mock_machine.return_value.value.return_value = 1
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/getpin/D6",b"")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/tester/statepin/D6",'1')
    mock_machine.return_value.value.return_value = 0
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/getpin/D6",b"")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/tester/statepin/D6",'0')
    mock_umqtt.reset_mock()
    ab.mqtt_tester_subscribe_cb(b"contX/tester/cmnd/getpin/D4",b"")
    mock_umqtt.return_value.publish.assert_not_called()

@patch("AppBase.network.WLAN")
@patch("AppTester.machine.Pin")
def test_begin(mock_machine,mock_network):
    """
    testing of start of led application
    """
    ab = AppTester.CAppTester(app_device)
    ab.begin()

@patch("AppBase.network.WLAN")
@patch("AppTester.machine.Pin")
@patch("AppTester.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_machine,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppTester.main()
