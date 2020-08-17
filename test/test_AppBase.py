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
    assert ab.client_id == "contXbase"
    assert ab.topic == b'contX'
    assert ab.github_repo == "https://github.com/matthandi/mrscontxUpdater"
    assert ab.main_dir == "main"
    assert ab.module == ""
    assert ab.user_agent == {'User-Agent':'contX-app'}

    # command messages
    assert ab.subscribe_cmnd_version_msg      == b'contX/base/cmnd/version'
    assert ab.subscribe_cmnd_repoversion_msg  == b'contX/base/cmnd/repoversion'
    assert ab.subscribe_cmnd_download_msg     == b'contX/base/cmnd/download'
    assert ab.subscribe_cmnd_install_msg      == b'contX/base/cmnd/install'
    assert ab.subscribe_cmnd_setdevice_msg    == b'contX/base/cmnd/setdevice'

    # publishing messages
    assert ab.topic_version_msg      == b'contX/base/version'
    assert ab.topic_repo_version_msg == b'contX/base/repoversion'
    assert ab.topic_info_msg         == b'contX/base/info'
    assert ab.topic_warning_msg      == b'contX/base/warning'
    assert ab.topic_error_msg        == b'contX/base/error'

def test_read_config():
    """
    testing of correct reading of (dummy) config file
    and setting the right properties
    """
    ab = AppBase.CAppBase("base")
    ab.read_configfile()
    assert ab.ssid_wlan == "xxxxx"
    assert ab.key_wlan == "xxxx"
    assert ab.mqtt_server == "xxx.xxx.xxx.xxx"

@patch("AppBase.network.WLAN")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_mqtt_init(mock_umqtt,mock_network):
    """
    testing of correct reading of (dummy) config file
    and setting the right properties
    """
    ab = AppBase.CAppBase("base")
    ab.read_configfile()
    ab.connect_mqtt()
    mock_umqtt.assert_called_with("contXbase","xxx.xxx.xxx.xxx")
    mock_umqtt.return_value.connect.assert_called()
    mock_umqtt.return_value.set_callback.assert_called_with(ab.mqtt_subscribe_cb)

@patch("AppBase.network.WLAN")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_begin(mock_umqtt,mock_network):
    ab = AppBase.CAppBase("base")
    ab.begin()
    subscribe_calls = [
                        call().subscribe(b'contX/base/cmnd/version'),
                        call().subscribe(b'contX/base/cmnd/repoversion'),
                        call().subscribe(b'contX/base/cmnd/download'),
                        call().subscribe(b'contX/base/cmnd/install')
                      ]
    mock_umqtt.assert_has_calls(subscribe_calls)
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/version",'0.0')

@patch("AppBase.network.WLAN")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_iwe_messages(mock_umqtt,mock_network):
    """
    test whether info (i), warning (w) and error (e) messages are available and work correct
    """
    ab = AppBase.CAppBase("base")
    ab.begin()
    ab.publish_info_message("Info message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/info",b'[I] Info message')
    ab.publish_warning_message("Warning message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/warning",b'[W] Warning message')
    ab.publish_error_message("Error message")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/error",b'[E] Error message')

@patch("AppBase.network.WLAN")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.install_files")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.download_updates_if_available")
@patch("AppBase.AppOtaUpd.CAppOtaUpd.get_latest_release_version")
@patch("AppBase.umqtt.simple.MQTTClient")
def test_mqtt_subscribe_cb(mock_umqtt,mock_latest_release_version,mock_download_updates_if_available,mock_install_files,mock_network):
    """
    testing of the subscribe function:
    * it will be checked whether the callback is set correctly
    * reactions of subscribe function is tested
    """
    ab = AppBase.CAppBase("base")
    ab.begin()

    # test request version
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/version",'0.0')
    ab.mqtt_subscribe_cb(ab.subscribe_cmnd_version_msg,'1.0')
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/version",'0.0')
    
    # test request repoversion
    mock_umqtt.reset_mock()
    mock_latest_release_version.return_value="1.1"
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/repoversion",b"")
    mock_umqtt.return_value.publish.assert_called_with(b"contX/base/repoversion",'1.1')
    
    # test request download
    mock_umqtt.reset_mock()
    mock_download_updates_if_available.return_value = True
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/download",b"")
    mock_download_updates_if_available.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/info',b"[I] update successfully downloaded")
    mock_umqtt.reset_mock()
    mock_download_updates_if_available.return_value = False
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/download",b"")
    mock_download_updates_if_available.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/info',b"[I] no update available")

    # test request install
    mock_umqtt.reset_mock()
    mock_install_files.return_value = True
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/install",b"")
    mock_install_files.assert_called()
    mock_umqtt.return_value.publish.assert_not_called()
    mock_umqtt.reset_mock()
    mock_install_files.return_value = False
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/install",b"")
    mock_install_files.assert_called()
    mock_umqtt.return_value.publish.assert_called_with(b'contX/base/error',b"[E] Installation of files failed")

    # test request set device
    mock_umqtt.reset_mock()
    ab.mqtt_subscribe_cb(b"contX/base/cmnd/setdevice",b"newdevice")
    assert ab.device == "newdevice"
    assert ab.bdevice == b"newdevice"
    assert ab.client_id == "contXnewdevice"

@patch("AppBase.network.WLAN")
@patch("AppBase.time.sleep", side_effect=InterruptedError)
def test_main(mock_timesleep,mock_network):
    """
    testing of main program - a little bit tricky, because it contains an indefinite
    loop -> time.sleep will be mocked with an assertion :)
    """
    with pytest.raises(InterruptedError):
        AppBase.main()

