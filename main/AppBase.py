import sys
sys.path.append('/main')
import machine
import time
import ubinascii
import ujson
import umqtt.simple
import network
import gc
import AppOtaUpd

class CAppBase:
    """
    Base class for all other applications
    """
    # constants for PinOut-Map of ESP32
    GPIO2  = 2  # internal led - used for alive signal
    
    # digital input / output with pullups
    GPIO4  = 4
    GPIO16 = 16
    GPIO17 = 17
    GPIO25 = 25
    GPIO26 = 26
    GPIO27 = 27
    GPIO32 = 32
    GPIO33 = 33

    # digital input only (possible ADC channels)
    GPIO34 = 34
    GPIO35 = 35
    GPIO36 = 36
    GPIO39 = 39

    def __init__(self,device = "",device_id="0",github_repo="https://github.com/matthandi/mrscontxUpdater",alive_led_pin=GPIO2,alive_led_mode=0):
        """
        constructor
        """
        super().__init__()
        self.topic = b'contX'
        self.device = device
        self.alive_led_pin = alive_led_pin
        self.alive_led_mode = alive_led_mode
        self.device_id = device_id
        self.github_repo = github_repo
        self.main_dir = "main"
        self.module = ""
        self.user_agent =  {'User-Agent':'contX-app'}
        self.set_devicename_id(device,device_id)

    def set_devicename_id(self,device,device_id):
        """
        sets the devicename and the device_id
        """
        self.bdevice = bytes(device,'utf-8')
        self.bdevice_id = bytes(device_id,'utf-8')
        self.client_id = "contX" + device + device_id
        # mqtt commands
        self.subscribe_cmnd_version_msg     = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/version"
        self.subscribe_cmnd_repoversion_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/repoversion"
        self.subscribe_cmnd_download_msg    = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/download"
        self.subscribe_cmnd_install_msg     = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/install"
        self.subscribe_cmnd_reboot_msg      = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/reboot"
        self.subscribe_cmnd_mem_free_msg    = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/memfree"
        self.subscribe_cmnd_mem_alloc_msg   = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/memalloc"
        self.subscribe_cmnd_getip_msg       = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/getip"

        # mqtt publishing
        self.topic_version_msg      = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/version"
        self.topic_repo_version_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/repoversion"
        self.topic_mem_free_msg     = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/memfree"
        self.topic_mem_alloc_msg    = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/memalloc"
        self.topic_ip_msg           = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/ip"
        self.topic_info_msg         = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/info"
        self.topic_warning_msg      = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/warning"
        self.topic_error_msg        = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/error"
        self.alive_led_state        = False

    def toggle_alive_led(self):
        """
        toggles internal led as alive led
        """
        self.alive_led_state = not self.alive_led_state
        self.alive_led.value(self.alive_led_state)

    def init_alive_led(self):
        """
        inits the alive led
        """
        self.alive_led = machine.Pin(self.alive_led_pin, machine.Pin.OUT)
        self.alive_timer = machine.Timer(1)
        self.alive_timer.init(period=1000,mode=machine.Timer.PERIODIC, callback=lambda t:self.toggle_alive_led())

    def flash_led(self):
        self.alive_led.value(1)
        time.sleep(0.05)
        self.alive_led.value(0)

    def init_flash_led(self):
        self.alive_led = machine.Pin(self.alive_led_pin, machine.Pin.OUT)

    def read_configfile(self,filename = 'ssid.json'):
        try:
            with open(filename) as f:
                self.ssid_data = ujson.load(f)
            self.ssid_wlan = self.ssid_data['SSIDS'][0]['ssid']
            self.key_wlan = self.ssid_data['SSIDS'][0]['key']
            self.mqtt_server = self.ssid_data['SSIDS'][0]['mqttbroker']
            device_name = self.ssid_data["device"]["name"] 
            device_id   = self.ssid_data["device"]["id"]
            d_changed = False
            if device_name != "":
                self.device = device_name
                d_changed = True
            if device_id != "0":
                self.device_id = device_id
                d_changed = True
            if d_changed == True:
                self.set_devicename_id(self.device,self.device_id)
            return True
        except (IndexError,KeyError,OSError,TypeError,ValueError):
            return False

    def mqtt_subscribe_cb(self,topic,payload):
        """
        subscribe callback function
        """
        self.flash_led()
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

        # request reboot
        if topic == self.subscribe_cmnd_reboot_msg:
            machine.reset()

        # request mem free
        if topic == self.subscribe_cmnd_mem_free_msg:
            gc.collect()
            self.mqtt_client.publish(self.topic_mem_free_msg,str(gc.mem_free()).encode('utf-8'))

        # request mem alloc
        if topic == self.subscribe_cmnd_mem_alloc_msg:
            gc.collect()
            self.mqtt_client.publish(self.topic_mem_alloc_msg,str(gc.mem_alloc()).encode('utf-8'))

        # request for ip
        if topic == self.subscribe_cmnd_getip_msg:
            ip_response = self.station.ifconfig()
            self.mqtt_client.publish(self.topic_ip_msg,str(ip_response[0]).encode('utf-8'))

    def request_download(self):
        """
        requests download of new App SW if available
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        if o.download_updates_if_available() == True:
            self.publish_info_message("update successfully downloaded")
        else:
            self.publish_info_message("no update available")
        gc.collect()

    def request_install_files(self):
        """
        request for installation of downloaded files
        """
        o = AppOtaUpd.CAppOtaUpd(self.github_repo)
        if o.install_files() == False:
            self.publish_error_message("Installation of files failed")
        gc.collect()

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
        self.station = network.WLAN(network.STA_IF)
        self.station.active(True)
        self.station.connect(self.ssid_wlan, self.key_wlan)
        print("connecting to wlan...")
        while self.station.isconnected() == False:
            self.toggle_alive_led()
            time.sleep(0.05)
 
        self.alive_led_state = False
        self.alive_led.value(self.alive_led_state)
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
        if self.alive_led_mode > 0:
            self.init_alive_led()
        self.init_flash_led()
        self.read_configfile()
        self.connect_mqtt()
        self.mqtt_publish_version()
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_version_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_repoversion_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_download_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_install_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_mem_free_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_mem_alloc_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_reboot_msg)
        self.mqtt_subscribe_to_msg(self.subscribe_cmnd_getip_msg)


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