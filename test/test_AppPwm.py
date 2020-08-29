import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppPwm

app_device = "pwm"

@patch("AppPwm.machine")
def test_apppwm(mock_machine):
    """
    testing of constructor init data
    """
    ab = AppPwm.CAppPwm(app_device)
    assert ab.device == app_device
    assert ab.bdevice == b"pwm"
    assert ab.client_id == "contXpwm0"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}

    # internal values
    assert ab.position == 0
    assert ab.freqency == 50
    assert ab.pwm_pin == AppPwm.CAppPwm.GPIO4

    mock_machine.PWM.assert_called_with(4,freq=50,duty=0)
    
    # base app subscription
    assert ab.subscribe_cmnd_version_msg == b'contX/pwm/0/cmnd/version'
    # commands
    assert ab.topic_cmnd_set_pos_msg == b'contX/pwm/0/cmnd/setpos'
    assert ab.topic_cmnd_get_pos_msg == b'contX/pwm/0/cmnd/getpos'

    # publishing topics
    assert ab.topic_pos_msg == b'contX/pwm/0/pos'

@patch("AppBase.network.WLAN")
@patch("AppPwm.umqtt.simple.MQTTClient")
@patch("AppPwm.machine.PWM")
def test_pwm_subscribe_cb(mock_machine,mock_umqtt,mock_network):
    ab = AppPwm.CAppPwm(app_device)
    ab.begin()
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setpos",'0')
    mock_machine.return_value.duty.assert_called_with(0)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setpos",'50')
    mock_machine.return_value.duty.assert_called_with(512)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/getpos",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/pos",'512.0')
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setpos",'100')
    mock_machine.return_value.duty.assert_called_with(1024)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/getpos",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/pos",'1024.0')

@patch("AppPwm.umqtt.simple.MQTTClient.subscribe")
@patch("AppBase.network.WLAN")
@patch("AppLed.machine.Pin")
def test_begin(mock_machine,mock_network,mock_umqtt):
    """
    testing of start of led application
    """
    ab = AppPwm.CAppPwm(app_device)
    ab.begin()
    # checking subscribes
    subscribe_calls = [
                        call(b'contX/pwm/1/cmnd/version'),
                        call(b'contX/pwm/1/cmnd/repoversion'),
                        call(b'contX/pwm/1/cmnd/download'),
                        call(b'contX/pwm/1/cmnd/install'),
                        call(b'contX/pwm/1/cmnd/memfree'),
                        call(b'contX/pwm/1/cmnd/reboot'),
                        call(b'contX/pwm/1/cmnd/getip'),
                        call(b'contX/pwm/1/cmnd/setpos'),
                        call(b'contX/pwm/1/cmnd/getpos')
                      ]
    mock_umqtt.assert_has_calls(subscribe_calls)





@patch("AppBase.network.WLAN")
@patch("AppPwm.machine.Pin")
@patch("AppPwm.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_machine,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppPwm.main()
