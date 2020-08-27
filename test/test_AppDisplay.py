import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppDisplay

app_device = "display"

def test_appdisplay():
    """
    testing of constructor init data
    """
    ab = AppDisplay.CAppDisplay(app_device)
    assert ab.device == app_device
    assert ab.bdevice == b"display"
    assert ab.client_id == "contXdisplay0"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.subscribe_cmnd_version_msg == b'contX/display/0/cmnd/version'
    assert ab.topic_cmnd_settext_msg     == b'contX/display/0/cmnd/settext'
    assert ab.topic_cmnd_fill_msg        == b'contX/display/0/cmnd/fill'
    assert ab.topic_cmnd_gettext_msg     == b'contX/display/0/cmnd/gettext'
    # replies
    assert ab.topic_text_msg             == b'contX/display/0/text'

    assert ab.dspl_onoff_state           == 1

@patch("AppDisplay.machine.I2C")
@patch("AppDisplay.machine")
def test_create_display(mock_machine_pin,mock_machine_i2c):
    """
    """
    ab = AppDisplay.CAppDisplay(app_device)
    ab.create_display()
    machine_calls = [
                        call.Pin(16,AppDisplay.machine.Pin.OUT),
                        call.Pin().value(1),
                        call.Pin(15),
                        call.Pin(4)
                      ]
    mock_machine_pin.assert_has_calls(machine_calls)

    #mock_machine_pin.assert_called_with(AppDisplay.CAppDisplay.GPIO16,AppDisplay.machine.Pin.OUT)
    mock_machine_i2c.assert_called_with(-1,scl=AppDisplay.machine.Pin(AppDisplay.CAppDisplay.GPIO15),sda=AppDisplay.machine.Pin(AppDisplay.CAppDisplay.GPIO4))

@patch("AppDisplay.ssd1306.SSD1306_I2C")
@patch("AppBase.network.WLAN")
@patch("AppDisplay.umqtt.simple.MQTTClient")
@patch("AppDisplay.machine.Pin")
def test_display_subscribe_cb(mock_machine,mock_umqtt,mock_network,mock_ssd1306):
    ab = AppDisplay.CAppDisplay(app_device)
    ab.begin()

    # test request display fill
    mock_umqtt.reset_mock()
    mock_machine.reset_mock()
    ab.mqtt_display_subscribe_cb(b"contX/display/1/cmnd/fill",b'0')
    mock_ssd1306.return_value.fill.assert_called_with(0)
    ab.mqtt_display_subscribe_cb(b"contX/display/1/cmnd/fill",b'1')
    mock_ssd1306.return_value.fill.assert_called_with(1)

    # test request set text
    mock_umqtt.reset_mock()
    mock_machine.reset_mock()
    ab.mqtt_display_subscribe_cb(b"contX/display/1/cmnd/settext",b"hello world,0,5")
    mock_ssd1306.return_value.text.assert_called_with('hello world',0,5)

    # test request set text with invalid text
    mock_umqtt.reset_mock()
    mock_ssd1306.reset_mock()
    ab.mqtt_display_subscribe_cb(b"contX/display/1/cmnd/settext",b"hello world")
    mock_ssd1306.return_value.text.assert_not_called()
    mock_umqtt.return_value.publish.assert_called_with(b"contX/display/1/error", b"[E] invalid displaytext: b'hello world'")


@patch("AppDisplay.umqtt.simple.MQTTClient.subscribe")
@patch("AppBase.network.WLAN")
@patch("AppBase.machine.Pin")
def test_begin(mock_machine,mock_network,mock_umqtt):
    """
    testing of start of led application
    """
    ab = AppDisplay.CAppDisplay(app_device)
    ab.begin()
    # checking subscribes
    subscribe_calls = [
                        call(b'contX/display/1/cmnd/version'),
                        call(b'contX/display/1/cmnd/repoversion'),
                        call(b'contX/display/1/cmnd/download'),
                        call(b'contX/display/1/cmnd/install'),
                        call(b'contX/display/1/cmnd/memfree'),
                        call(b'contX/display/1/cmnd/reboot'),
                        call(b'contX/display/1/cmnd/settext'),
                        call(b'contX/display/1/cmnd/gettext'),
                        call(b'contX/display/1/cmnd/fill')
                      ]
    mock_umqtt.assert_has_calls(subscribe_calls)

@patch("AppBase.network.WLAN")
@patch("AppBase.machine.Pin")
@patch("AppBase.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_machine,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppDisplay.main()
