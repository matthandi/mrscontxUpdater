import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppSwitch

app_device = "switch"

def test_appswitch():
    """
    testing of constructor init data
    """
    ab = AppSwitch.CAppSwitch(app_device)
    assert ab.device == app_device
    assert ab.bdevice == b"switch"
    assert ab.client_id == "contXswitch"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.subscribe_cmnd_version_msg == b'contX/switch/cmnd/version'
    assert ab.topic_cmnd_state_msg == b'contX/switch/cmnd/state'
    assert ab.topic_state_msg == b'contX/switch/state'
    assert ab.btn_pin == AppSwitch.CAppSwitch.GPIO26
    assert ab.last_state == 0

@patch("AppSwitch.machine.Pin")
def test_create_switch(mock_machine):
    """
    """
    ab = AppSwitch.CAppSwitch(app_device)
    ab.create_switch()
    mock_machine.assert_called_with(AppSwitch.CAppSwitch.GPIO26,AppSwitch.machine.Pin.IN)

@patch("AppBase.network.WLAN")
@patch("AppSwitch.machine.Pin")
@patch("AppSwitch.umqtt.simple.MQTTClient")
def test_check_switch(mock_umqtt,mock_machine,mock_network):
    """
    test handling of check button:
    * only on state change a mqtt message is send
    """
    ab = AppSwitch.CAppSwitch(app_device)
    ab.begin()

    mock_machine.return_value.value.return_value = 1
    ab.check_switch()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/switch/state",b'1')

    assert mock_umqtt.return_value.publish.call_count == 2
    ab.check_switch()
    assert mock_umqtt.return_value.publish.call_count == 2
    
    mock_machine.return_value.value.return_value = 0
    ab.check_switch()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/switch/state",b'0')

@patch("AppBase.network.WLAN")
@patch("AppSwitch.umqtt.simple.MQTTClient")
@patch("AppSwitch.machine.Pin")
def test_switch_subscribe_cb(mock_machine,mock_umqtt,mock_network):
    ab = AppSwitch.CAppSwitch(app_device)
    ab.begin()
    ab.last_state = 1
    ab.mqtt_switch_subscribe_cb(b"contX/switch/cmnd/state",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/switch/state",b'1')
    ab.last_state = 0
    ab.mqtt_switch_subscribe_cb(b"contX/switch/cmnd/state",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/switch/state",b'0')


@patch("AppBase.network.WLAN")
@patch("AppSwitch.machine.Pin")
def test_begin(mock_machine,mock_network):
    """
    testing of start of switch application
    """
    ab = AppSwitch.CAppSwitch(app_device)
    ab.begin()
    mock_machine.assert_called_with(AppSwitch.CAppSwitch.GPIO26,AppSwitch.machine.Pin.IN)

@patch("AppBase.network.WLAN")
@patch("AppSwitch.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppSwitch.main()
