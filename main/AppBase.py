import sys
sys.path.append('/main')
import machine
import time
import ubinascii
import ujson
import umqtt.simple
import AppOtaUpd
import network

class CAppBase:
    """
    Base class for all other applications
    """
    # constants for PinOut-Map of ESP8266
    D0 = 16
    D1 = 5
    D2 = 4
    D3 = 0
    D4 = 2
    D5 = 14
    D6 = 12
    D7 = 13
    # A0 = ?

    def __init__(self,device = "",github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__()
        self.device = device
        self.bdevice = bytes(device,'utf-8')
        self.client_id = "contX" + device
        self.topic = b'contX'
        self.github_repo = github_repo
        self.main_dir = "main"
        self.module = ""
        self.user_agent =  {'User-Agent':'contX-app'}
        # mqtt commands
        self.subscribe_cmnd_version_msg = self.topic + b"/" + self.bdevice + b"/cmnd/version"
        self.subscribe_cmnd_repoversion_msg = self.topic + b"/" + self.bdevice + b"/cmnd/repoversion"
        self.subscribe_cmnd_download_msg = self.topic + b"/" + self.bdevice + b"/cmnd/download"
        self.subscribe_cmnd_install_msg = self.topic + b"/" + self.bdevice + b"/cmnd/install"
        self.subscribe_cmnd_setdevice_msg = self.topic + b"/" + self.bdevice + b"/cmnd/setdevice"
        # mqtt publishing
        self.topic_version_msg      = self.topic + b"/" + self.bdevice + b"/version"
        self.topic_repo_version_msg = self.topic + b"/" + self.bdevice + b"/repoversion"
        self.topic_info_msg         = self.topic + b"/" + self.bdevice + b"/info"
        self.topic_warning_msg      = self.topic + b"/" + self.bdevice + b"/warning"
        self.topic_error_msg        = self.topic + b"/" + self.bdevice + b"/error"
    
    def read_configfile(self):
        with open('ssid.json') as f:
            self.ssid_data = ujson.load(f)
        self.ssid_wlan = self.ssid_data['SSIDS'][0]['ssid']
        self.key_wlan = self.ssid_data['SSIDS'][0]['key']
        self.mqtt_server = self.ssid_data['SSIDS'][0]['mqttbroker']

    def set_devicename(self,new_device_name):
        """
        sets a new device name (e.g. for debugging / testing)
        """
        self.device = new_device_name
        self.bdevice = bytes(new_device_name,'utf-8')
        self.client_id = "contX" + new_device_name

    def mqtt_subscribe_cb(self,topic,payload):
        """
        subscribe callback function
        """
        # request for version
        if topic == self.subscribe_cmnd_version_msg:
            # publish version
            self.mqtt_publish_version()
        
        # request for repo version
        if topic == self.subscribe_cmnd_repoversion_msg:
            # publish repo version
            self.mqtt_publish_repoversion()

        # request for download
        if topic == self.subscribe_cmnd_download_msg:
            # request download
            self.request_download()

        # request for install files
        if topic == self.subscribe_cmnd_install_msg:
            # request download
            self.request_install_files()

        # request for setting new device name
        if topic == self.subscribe_cmnd_setdevice_msg:
            self.set_devicename(payload.decode("utf-8"))

    def request_download(self):
        """
        requests download of new App SW if available
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        o.download_updates_if_available()

    def request_install_files(self):
        """
        request for installation of downloaded files
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        o.install_files()        

    def mqtt_subscribe_to_msg(self,msg):
        """
        subscribe to a specific message
        - be aware to use a byte array (use bytes(value) or b'string')
        """
        self.mqtt_client.subscribe(msg)

    def mqtt_publish_msg(self,topic,payload):
        """
        publish a message consists of topic and payload
        """
        self.mqtt_client.publish(topic, payload)

    def mqtt_publish_version(self):
        """
        publish the version - if available
        otherwise '0.0' will be returned, if no version is available
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        appversion = o.get_version(self.main_dir)
        self.mqtt_publish_msg(self.topic_version_msg,appversion)

    def mqtt_publish_repoversion(self):
        """
        publish the repoversion - if available
        otherwise '0.0' will be returned, if no version is available
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        latest_release_version = o.get_latest_release_version()
        self.mqtt_publish_msg(self.topic_repo_version_msg,latest_release_version)

    def publish_info_message(self,msg):
        """
        publishes info messages
        """
        self.mqtt_client.publish(self.topic_info_msg,b'[I] ' + bytes(msg,'utf-8'))

    def publish_warning_message(self,msg):
        """
        publishes warning messages
        """
        self.mqtt_client.publish(self.topic_warning_msg,b'[W] ' + bytes(msg,'utf-8'))

    def publish_error_message(self,msg):
        """
        publishes error messages
        """
        self.mqtt_client.publish(self.topic_error_msg,b'[E] ' + bytes(msg,'utf-8'))

    def connect_mqtt(self):
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(self.ssid_wlan, self.key_wlan)
        print("trying to connect...")
        while station.isconnected() == False:
            pass
 
        self.mqtt_client = umqtt.simple.MQTTClient(self.client_id,self.mqtt_server)
        self.set_subscribe_cb(self.mqtt_subscribe_cb)
        self.mqtt_client.connect()

    def set_subscribe_cb(self,cb):
        """
        set subscribe callback 
        """
        self.mqtt_client.set_callback(cb)

    def check_msg(self):
        """
        check for new subscribe messages
        """
        self.mqtt_client.check_msg()


    def begin(self):
        """
        call this function to begin
        """
        self.read_configfile()
        self.connect_mqtt()
        self.mqtt_publish_version()
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_version_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_repoversion_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_download_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_install_msg)


def main():   
    """
    main program - explicit coded for testability
    """
    ab = CAppBase("base")
    ab.begin()
    while True:
        ab.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()