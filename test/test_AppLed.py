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
    assert ab.client_id == "contXled0"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.subscribe_cmnd_version_msg == b'contX/led/0/cmnd/version'
    assert ab.led_pin == AppLed.CAppLed.GPIO4
    assert ab.last_state == 0

    assert ab.r_led_pin == AppLed.CAppLed.GPIO25
    assert ab.y_led_pin == AppLed.CAppLed.GPIO26
    assert ab.g_led_pin == AppLed.CAppLed.GPIO27

    assert ab.r_last_state == 0
    assert ab.y_last_state == 0
    assert ab.g_last_state == 0

    # led commands
    assert ab.topic_cmnd_set_msg == b'contX/led/0/cmnd/set'
    assert ab.topic_cmnd_state_msg == b'contX/led/0/cmnd/state'
    assert ab.topic_cmnd_ryg_set_msg == b'contX/led/0/cmnd/rygset'
    assert ab.topic_cmnd_ryg_state_msg == b'contX/led/0/cmnd/rygstate'
    assert ab.topic_cmnd_ryg_sweep_msg == b'contX/led/0/cmnd/rygsweep'

    # led responses
    assert ab.topic_state_msg == b'contX/led/0/state'
    assert ab.topic_ryg_state_msg == b'contX/led/0/rygstate'

@patch("AppLed.machine.Pin")
def test_create_led(mock_machine):
    """
    """
    ab = AppLed.CAppLed(app_device)
    ab.create_led()
    # checking subscribes
    pin_calls = [
                        call(AppLed.CAppLed.GPIO4,AppLed.machine.Pin.OUT),
                        call(AppLed.CAppLed.GPIO25,AppLed.machine.Pin.OUT),
                        call(AppLed.CAppLed.GPIO26,AppLed.machine.Pin.OUT),
                        call(AppLed.CAppLed.GPIO27,AppLed.machine.Pin.OUT)
                ]
    mock_machine.assert_has_calls(pin_calls)
#    mock_machine.assert_called_with(AppLed.CAppLed.GPIO4,AppLed.machine.Pin.OUT)

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
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/state",'1')

@patch("time.sleep")
@patch("AppBase.network.WLAN")
@patch("AppLed.umqtt.simple.MQTTClient")
@patch("AppLed.machine.Pin")
def test_led_subscribe_cb(mock_machine,mock_umqtt,mock_network,mock_time_sleep):
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    ab.set_led(1)
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/state",'0')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/state",'1')
    ab.set_led(0)
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/state",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/state",'0')
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/set",'0')
    mock_machine.return_value.value.assert_called_with(0)
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/set",'1')
    mock_machine.return_value.value.assert_called_with(1)

    mock_machine.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygset",b'0,0,0')
    ryg_calls = [
                    call().call(0),
                    call().call(0),
                    call().call(0)
                ]
    mock_machine.return_value.value.assert_has_calls(ryg_calls)

    mock_machine.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygset",b'1,1,1')
    ryg_calls = [
                    call().call(1),
                    call().call(1),
                    call().call(1)
                ]
    mock_machine.return_value.value.assert_has_calls(ryg_calls)

    mock_umqtt.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygset",b'1,1;;x')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/error",b'[E] Invalid rygset data: 1,1;;x')

    mock_umqtt.reset_mock()
    ab.r_last_state = 1
    ab.y_last_state = 1
    ab.g_last_state = 0
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygstate",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/rygstate",b'1,1,0')

    mock_machine.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygsweep",b'ryg,1000')
    ryg_calls = [
                    call(1),
                    call(0),
                    call(0),
                    call(1),
                    call(1),
                    call(0),
                    call(0),
                    call(0),
                    call(1)
                ]
    mock_machine.return_value.value.assert_has_calls(ryg_calls)

    mock_machine.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygsweep",b'gyr,1000')
    ryg_calls = [
                    call(0),
                    call(0),
                    call(1),
                    call(0),
                    call(1),
                    call(0),
                    call(1),
                    call(0),
                    call(0)
                ]
    mock_machine.return_value.value.assert_has_calls(ryg_calls)

    mock_umqtt.reset_mock()
    ab.mqtt_led_subscribe_cb(b"contX/led/1/cmnd/rygsweep",b'gyr;20')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/led/1/error",b'[E] Invalid rygsweep data: gyr;20')


@patch("AppLed.umqtt.simple.MQTTClient")
@patch("AppBase.network.WLAN")
@patch("AppLed.machine.Pin")
def test_begin(mock_machine,mock_network,mock_umqtt):
    """
    testing of start of led application
    """
    ab = AppLed.CAppLed(app_device)
    ab.begin()
    mock_umqtt.return_value.set_callback.assert_called_with(ab.mqtt_led_subscribe_cb)


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
