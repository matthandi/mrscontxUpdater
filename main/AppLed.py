import sys
sys.path.append('/main')
import machine
import time
import ujson
import umqtt.simple
import AppBase

class CAppLed(AppBase.CAppBase):
    """
    inherited class for a led application
    """

    def __init__(self, device='led',device_id="0",led_pin = AppBase.CAppBase.GPIO4,github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,device_id = device_id,github_repo=github_repo)
        self.led_pin = led_pin
        self.last_state = 0 
        self.set_led_devicename_id()

    def set_led_devicename_id(self):
        # command messages
        #   request for state
        self.topic_cmnd_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/state"
        self.topic_cmnd_set_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/set"
        # publish messages
        #   publish state of led
        self.topic_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/state"

    def create_led(self):
        """
        creates a led interface
        """
        self.led = machine.Pin(self.led_pin, machine.Pin.OUT)
        self.led.value(0)

    def publish_led_state(self):
        self.mqtt_client.publish(self.topic_state_msg,str(self.last_state))

    def set_led(self,state):
        """
        sets the led state
        """
        self.last_state = state
        self.led.value(state)

    def mqtt_led_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)

        # request state command
        if topic == self.topic_cmnd_state_msg:
            self.publish_led_state()

        # set led command
        if topic == self.topic_cmnd_set_msg:
            self.set_led(int(payload))

    def begin(self):
        """
        start function for the led application
        """
        super().begin()
        self.set_led_devicename_id()
        # create button interface
        self.create_led()
        # subscribe to command message for state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_state_msg)
        # subscribe to command message for set
        self.mqtt_subscribe_to_msg(self.topic_cmnd_set_msg)
        # overwrite callback of base class
        self.set_subscribe_cb(self.mqtt_led_subscribe_cb)

def main():   
    """
    main program - explicit coded for testability
    """
    app_led = CAppLed("led")
    app_led.begin()
    while True:
        app_led.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    