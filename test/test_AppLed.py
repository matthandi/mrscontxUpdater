import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppLed

app_device = "led"

def test_appled():
    """
    testing of constructor init data
    """
    ab = AppLed.CAppLed(app_device)
    assert ab.device == app_device
    assert ab.bdevice == b"led"
    assert ab.client_id == "contXled"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.subscribe_cmnd_version_msg == b'contX/led/cmnd/version'
    assert ab.topic_cmnd_set_msg == b'contX/led/cmnd/set'
    assert ab.topic_cmnd_state_msg == b'contX/led/cmnd/state'
    assert ab.led_pin == AppLed.CAppLed.D4
    assert ab.last_state == 0

@patch("AppLed.machine.Pin")
def test_create_led(mock_machine):
    """
    """
    ab = AppLed.CAppLed(app_device)
    ab.create_led()
    mock_machine.assert_called_with(AppLed.CAppLed.D4,AppLed.machine.Pin.OUT)

@patch("AppBase.network.WLAN")
@patch("AppLed.machine.Pin")
def test_set_led(mock_machine,mock_network):
    """
    test handling of check button:
    * only on state change a mqtt message is send
    """
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    ab.set_led(1)
    mock_machine.return_value.value.assert_called_with(1)

@patch("AppBase.network.WLAN")
@patch("AppLed.umqtt.simple.MQTTClient")
@patch("AppLed.machine.Pin")
def test_publish_led_state(mock_machine,mock_umqtt,mock_network):
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    ab.last_state = 1
    ab.publish_led_state()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/state",'1')

@patch("AppBase.network.WLAN")
@patch("AppLed.umqtt.simple.MQTTClient")
@patch("AppLed.machine.Pin")
def test_led_subscribe_cb(mock_machine,mock_umqtt,mock_network):
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    ab.set_led(1)
    ab.mqtt_led_subscribe_cb(b"contX/led/cmnd/state",'0')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/state",'1')
    ab.set_led(0)
    ab.mqtt_led_subscribe_cb(b"contX/led/cmnd/state",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/state",'0')
    ab.mqtt_led_subscribe_cb(b"contX/led/cmnd/set",'0')
    mock_machine.return_value.value.assert_called_with(0)
    ab.mqtt_led_subscribe_cb(b"contX/led/cmnd/set",'1')
    mock_machine.return_value.value.assert_called_with(1)


@patch("AppBase.network.WLAN")
@patch("AppLed.machine.Pin")
def test_begin(mock_machine,mock_network):
    """
    testing of start of led application
    """
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    mock_machine.assert_called_with(AppLed.CAppLed.D4,AppLed.machine.Pin.OUT)

@patch("AppBase.network.WLAN")
@patch("AppLed.machine.Pin")
@patch("AppLed.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_machine,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppLed.main()
