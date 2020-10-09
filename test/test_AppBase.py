import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppBase

def test_appbase():
    """
    testing of constructor init data
    """
    ab = AppBase.CAppBase("base")
    assert ab.device == "base"
    assert ab.bdevice == b"base"
    assert ab.device_id == "0"
    assert ab.bdevice_id == b"0"
    assert ab.client_id == "contXbase0"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}
    assert ab.alive_led_pin == ab.GPIO2,"alive led pin must be set to GPIO2"

    # command messages
    assert ab.subscribe_cmnd_version_msg      == b'contX/base/0/cmnd/version'
    assert ab.subscribe_cmnd_repoversion_msg  == b'contX/base/0/cmnd/repoversion'
    assert ab.subscribe_cmnd_download_msg     == b'contX/base/0/cmnd/download'
    assert ab.subscribe_cmnd_install_msg      == b'contX/base/0/cmnd/install'
    assert ab.subscribe_cmnd_reboot_msg       == b'contX/base/0/cmnd/reboot'
    assert ab.subscribe_cmnd_mem_free_msg     == b'contX/base/0/cmnd/memfree'
    assert ab.subscribe_cmnd_mem_alloc_msg    == b'contX/base/0/cmnd/memalloc'
    assert ab.subscribe_cmnd_getip_msg        == b'contX/base/0/cmnd/getip'

    # publishing messages
    assert ab.topic_version_msg      == b'contX/base/0/version'
    assert ab.topic_repo_version_msg == b'contX/base/0/repoversion'
    assert ab.topic_mem_free_msg     == b'contX/base/0/memfree'
    assert ab.topic_mem_alloc_msg    == b'contX/base/0/memalloc'
    assert ab.topic_ip_msg           == b'contX/base/0/ip'
    assert ab.topic_info_msg         == b'contX/base/0/info'
    assert ab.topic_warning_msg      == b'contX/base/0/warning'
    assert ab.topic_error_msg        == b'contX/base/0/error'
    assert ab.topic_ip_msg           == b'contX/base/0/ip'

def test_read_config():
    """
    testing of correct reading of (dummy) config file
    and setting the right properties
    """
    ab = AppBase.CAppBase("base")
    assert ab.read_configfile("ssid-check.json") == True
    assert ab.ssid_wlan == "xxxxx"
    assert ab.key_wlan == "xxxx"
    assert ab.mqtt_server == "xxx.xxx.xxx.xxx"
    assert ab.mqtt_port   == "1883"
    assert ab.device == "check"
    assert ab.bdevice == b"check"
    assert ab.device_id == "1"
    assert ab.bdevice_id == b"1"
    assert ab.read_configfile("notexisting.json") == False

@patch("AppBase.network.WLAN")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_mqtt_init(mock_umqtt,mock_network):
    """
    testing of correct reading of (dummy) config file
    and setting the right properties
    """
    mock_network.return_value.isconnected.side_effect = [False,False,True]
    ab = AppBase.CAppBase("base")
    ab.read_configfile()
    ab.init_alive_led()
    ab.connect_mqtt()
    mock_umqtt.assert_called_with("contXbase1","xxx.xxx.xxx.xxx",port="1880")
    mock_umqtt.return_value.connect.assert_called()
    mock_umqtt.return_value.set_callback.assert_called_with(ab.mqtt_subscribe_cb)

@patch("AppBase.machine")
@patch("AppBase.network")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_begin(mock_umqtt,mock_network,mock_machine):
    ab = AppBase.CAppBase("base")
    ab.begin()
    subscribe_calls = [
                        call().subscribe(b'contX/base/1/cmnd/version'),
                        call().subscribe(b'contX/base/1/cmnd/repoversion'),
                        call().subscribe(b'contX/base/1/cmnd/download'),
                        call().subscribe(b'contX/base/1/cmnd/install'),
                        call().subscribe(b'contX/base/1/cmnd/memfree'),
                        call().subscribe(b'contX/base/1/cmnd/memalloc'),
                        call().subscribe(b'contX/base/1/cmnd/reboot'),
                        call().subscribe(b'contX/base/1/cmnd/getip')
                      ]
    mock_umqtt.assert_has_calls(subscribe_calls)
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/version",'0.0')

@patch("AppBase.network.WLAN")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_iwe_messages(mock_umqtt,mock_network):
    """
    test whether info (i), warning (w) and error (e) messages are available and work correct
    """
    ab = AppBase.CAppBase("base")
    ab.begin()
    ab.publish_info_message("Info message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/info",b'[I] Info message')
    ab.publish_warning_message("Warning message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/warning",b'[W] Warning message')
    ab.publish_error_message("Error message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/error",b'[E] Error message')

@patch("AppBase.machine")
@patch("AppBase.gc")
@patch("AppBase.network.WLAN")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.install_files")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.download_updates_if_available")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.get_latest_release_version")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_mqtt_subscribe_cb(mock_umqtt,mock_latest_release_version,mock_download_updates_if_available,mock_install_files,mock_network,mock_gc,mock_machine):
    """
    testing of the subscribe function:
    * it will be checked whether the callback is set correctly
    * reactions of subscribe function is tested
    """
    ab = AppBase.CAppBase("base")
    ab.begin()

    # test request version
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/version",'0.0')
    ab.mqtt_subscribe_cb(ab.subscribe_cmnd_version_msg,'1.0')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/version",'0.0')
    
    # test request repoversion
    mock_umqtt.reset_mock()
    mock_latest_release_version.return_value="1.1"
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/repoversion",b"")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/1/repoversion",'1.1')
    
    # test request download
    mock_umqtt.reset_mock()
    mock_download_updates_if_available.return_value = True
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/download",b"")
    mock_download_updates_if_available.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/info',b"[I] update successfully downloaded")
    mock_umqtt.reset_mock()
    mock_download_updates_if_available.return_value = False
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/download",b"")
    mock_download_updates_if_available.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/info',b"[I] no update available")

    # test request install
    mock_umqtt.reset_mock()
    mock_install_files.return_value = True
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/install",b"")
    mock_install_files.assert_called()
    mock_umqtt.return_value.publish.assert_not_called()
    mock_umqtt.reset_mock()
    mock_install_files.return_value = False
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/install",b"")
    mock_install_files.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/error',b"[E] Installation of files failed")

    # test request reboot
    mock_umqtt.reset_mock()
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/reboot",b"")
    mock_machine.reset.assert_called()

    # test request mem free
    mock_umqtt.reset_mock()
    mock_gc.mem_free.return_value = 1005
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/memfree",b"")
    mock_gc.mem_free.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/memfree',b'1005')

    # test request mem alloc
    mock_umqtt.reset_mock()
    mock_gc.mem_alloc.return_value = 2020
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/memalloc",b"")
    mock_gc.mem_alloc.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/memalloc',b"2020")

    # test request get ip
    mock_umqtt.reset_mock()
    mock_network.return_value.ifconfig.return_value = ('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8')
    ab.mqtt_subscribe_cb(b"contX/base/1/cmnd/getip",b"")
    mock_gc.mem_free.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/1/ip',b"192.168.4.1")


@patch("AppBase.machine")
def test_toggle_alive_led(mock_machine):
    """
    testing toggle of internal led
    """
    ab = AppBase.CAppBase("base")
    ab.init_alive_led()
    assert ab.alive_led_state == False
    ab.toggle_alive_led()
    assert ab.alive_led_state == True
    ab.toggle_alive_led()
    assert ab.alive_led_state == False

@patch("AppBase.machine.Timer")
@patch("AppBase.machine.Pin")
def test_init_alive_led(mock_machine_pin,mock_machine_timer):
    """
    inits and starts alive led with internal led
    """
    ab = AppBase.CAppBase("base")
    ab.init_alive_led()
    mock_machine_pin.assert_called_with(AppBase.CAppBase.GPIO2,AppBase.machine.Pin.OUT)
    mock_machine_timer.assert_called_with(1)
    #mock_machine_timer.return_value.init.assert_called_with(period=1000, mode=AppBase.machine.Timer.PERIODIC, callback=lambda t:AppBase.CAppBase.toggle_alive_led())


@patch("AppBase.network.WLAN")
@patch("AppBase.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppBase.main()

