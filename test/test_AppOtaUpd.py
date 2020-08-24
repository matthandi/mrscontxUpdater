import sys
import pytest
import json
sys.path.append('./main')
sys.path.append('./lib')
import unittest
from unittest.mock import call,Mock
from unittest.mock import MagicMock
from unittest.mock import mock_open,patch
import AppOtaUpd

repo_url = "https://github.com/matthandi/mrscontxUpdater"

def test_read_config():
    """
    testing of correct reading of (dummy) config file
    """
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    ou.read_configfile()
    assert ou.ssid_wlan == "xxxxx"
    assert ou.key_wlan == "xxxx"
    assert ou.github_repo == "https://api.github.com/repos/matthandi/mrscontxUpdater"
    assert ou.main_dir == "main"
    assert ou.module == ""
    assert ou.user_agent == {'User-Agent':'awesome-app'}


@patch("AppOtaUpd.network.WLAN")
def test_using_network(mock_network):
    """
    testing network usage
    """
    mock_network.return_value.isconnected.side_effect = [False,False,True]
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    ou.read_configfile()
    ou.using_network(ou.ssid_wlan,ou.key_wlan)
    mock_network.assert_called_with(AppOtaUpd.network.STA_IF)
    mock_network.return_value.active.assert_called_with(True)

def test_get_version():
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    assert ou.get_version("test/main", '.version_old') == '0.0'
    assert ou.get_version("test/main", '.version') == '1.3'
    assert ou.get_version("test/main") == '1.3'

@patch("AppOtaUpd.os.listdir", side_effect=OSError)
def test_get_version_assertion(mock_os_listdir):
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    assert ou.get_version("abc") == '0'

@patch("AppOtaUpd.urequests")
def test_get_latest_release_version(mock_urequests):
    mock_urequests.get.return_value = Mock(status_code=201, json=lambda : {"download_url":"http://file.ext","tag_name":"1.1"})
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    assert ou.get_latest_release_version() == '1.1'

    # invalid response
    mock_urequests.get.return_value = Mock(status_code=201, json=lambda : {"download_url":"http://file.ext","tag":"1.1"})
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    assert ou.get_latest_release_version() == '[E] reading latest version'


#@patch("AppOtaUpd.CAppOtaUpd")
@patch("AppOtaUpd.os")
def test_rmtree(mock_os):#,mock_rmtree):
    """
    testing remove tree
    - at the moment no recursive test
    """
    def side_effect(*args, **kwargs):
        if side_effect.counter < 1:
            side_effect.counter += 1
            return AppOtaUpd.CAppOtaUpd.rmtree("main/dir")
        else:
            return None
    side_effect.counter = 0
    #mock_rmtree.return_value.rmtree.side_effect = side_effect
    #mock_os.ilistdir.side_effect = [[["file",0x0],["dir",0x4000],["file1",0x0]]]
    mock_os.ilistdir.side_effect = [[["file",0x0],["dir",0x000],["file1",0x0]]]
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    ou.rmtree("main")
    mock_os.remove.assert_called_with("main/file1")
    mock_os.rmdir.assert_called_with("main")


@patch("AppOtaUpd.urequests")
@patch("__main__.__builtins__.open", new_callable=mock_open)
def test_download_file(mock_open,mock_urequests):
    """
    """
    mock_urequests.get.return_value = Mock(status_code=201, text="return data")
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    ou.download_file("http://file","main")
    mock_open.assert_called_with("main","w")
    mock_open.return_value.write.assert_called_with("return data")

@patch("AppOtaUpd.os.mkdir")
@patch("AppOtaUpd.urequests")
@patch("AppOtaUpd.open")
def test_download_files(mock_open,mock_urequests,mock_osmkdir):
    """
    testing of downloading all files
    """
    mock_urequests.get.return_value = Mock(status_code=200, json=lambda : [{'name':'file.py','type':'file','download_url':'https://download/file.py','path':'abc'},{'name':'dir1','type':'dirx','path':'abc'}])
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    ou.download_all_files("http://file","1.1")


def test_modulepath():
    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    assert ou.modulepath("abc") == "abc"
    ou.module="mod"
    assert ou.modulepath("abc") == "mod/abc"

@patch("AppOtaUpd.os.mkdir")
@patch("AppOtaUpd.CAppOtaUpd.get_latest_release_version")
@patch("AppOtaUpd.CAppOtaUpd.get_version")
@patch("AppOtaUpd.urequests")
@patch("AppOtaUpd.open")
def test_download_updates_if_available(mock_open,mock_urequests,mock_getversion,mock_getlatestversion,mock_osmkdir):
    ou = AppOtaUpd.CAppOtaUpd(repo_url,main_dir="test/main")
    mock_getversion.return_value="0.0"
    mock_getlatestversion.return_value="0.0"
    ou.download_updates_if_available()
    mock_getversion.return_value="0.0"
    mock_getlatestversion.return_value="1.0"
    ou.download_updates_if_available()
    with patch("AppOtaUpd.os.mkdir", side_effect=OSError):
        ou.download_updates_if_available()

@patch("AppOtaUpd.os", side_effect=OSError)
@patch("AppOtaUpd.CAppOtaUpd.rmtree")
@patch("AppOtaUpd.CAppOtaUpd.get_version")
def test_install_files(mock_getversion,mock_rmtree, mock_os):

    ou = AppOtaUpd.CAppOtaUpd(repo_url)
    mock_getversion.return_value = '0.0'
    assert ou.install_files() == False
    mock_getversion.return_value = '0.1'
    assert ou.install_files() == True
    with patch("AppOtaUpd.CAppOtaUpd.rmtree", side_effect=OSError):
        with patch("AppOtaUpd.os.rename", side_effect=OSError):
            assert ou.install_files() == False

    
