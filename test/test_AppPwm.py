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
    assert ab.duty      == 77
    assert ab.frequency == 50
    assert ab.pwm_pin   == AppPwm.machine.Pin(4,AppPwm.machine.Pin.OUT)

    mock_machine.PWM.assert_called_with(ab.pwm_pin,freq=50,duty=77)
    
    # base app subscription
    assert ab.subscribe_cmnd_version_msg == b'contX/pwm/0/cmnd/version'
    # commands
    assert ab.topic_cmnd_set_duty_msg      == b'contX/pwm/0/cmnd/setduty'
    assert ab.topic_cmnd_get_duty_msg      == b'contX/pwm/0/cmnd/getduty'
    assert ab.topic_cmnd_set_frequency_msg == b'contX/pwm/0/cmnd/setfrequency'
    assert ab.topic_cmnd_get_frequency_msg == b'contX/pwm/0/cmnd/getfrequency'
    assert ab.topic_cmnd_duty_sweep_msg    == b'contX/pwm/0/cmnd/dutysweep'
    # publishing topics
    assert ab.topic_duty_msg               == b'contX/pwm/0/duty'
    assert ab.topic_frequency_msg          == b'contX/pwm/0/frequency'

@patch("time.sleep")
@patch("AppBase.network.WLAN")
@patch("AppPwm.umqtt.simple.MQTTClient")
@patch("AppPwm.machine.PWM")
def test_pwm_subscribe_cb(mock_machine,mock_umqtt,mock_network,mock_time_sleep):
    ab = AppPwm.CAppPwm(app_device)
    ab.begin()
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setduty",'0')
    mock_machine.return_value.duty.assert_called_with(0)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setduty",'50')
    mock_machine.return_value.duty.assert_called_with(50)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/getduty",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/duty",b'50')
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setduty",'100')
    mock_machine.return_value.duty.assert_called_with(100)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/getduty",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/duty",b'100')
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/setfrequency",'1000')
    mock_machine.return_value.freq.assert_called_with(1000)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/getfrequency",'')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/frequency",b'1000')
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/dutysweep",b'110,120,500')
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/dutysweep",b'120,110,500')
    duty_calls = [
                    call(0),
                    call(50),
                    call(100),
                    call(110),
                    call(111),
                    call(112),
                    call(113),
                    call(114),
                    call(115),
                    call(116),
                    call(117),
                    call(118),
                    call(119),
                    call(120),
                    call(120),
                    call(119),
                    call(118),
                    call(117),
                    call(116),
                    call(115),
                    call(114),
                    call(113),
                    call(112),
                    call(111),
                    call(110)
                    ]
    mock_machine.return_value.duty.assert_has_calls(duty_calls)
    ab.mqtt_pwm_subscribe_cb(b"contX/pwm/1/cmnd/dutysweep",'120,120')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/pwm/1/error",b'[E] Invalid dutysweep data: 120,120')

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
                        call(b'contX/pwm/1/cmnd/memalloc'),
                        call(b'contX/pwm/1/cmnd/reboot'),
                        call(b'contX/pwm/1/cmnd/getip'),
                        call(b'contX/pwm/1/cmnd/setduty'),
                        call(b'contX/pwm/1/cmnd/getduty'),
                        call(b'contX/pwm/1/cmnd/setfrequency'),
                        call(b'contX/pwm/1/cmnd/getfrequency'),
                        call(b'contX/pwm/1/cmnd/dutysweep')
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
