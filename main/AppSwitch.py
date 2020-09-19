import sys
sys.path.append('./main')
import machine
import time
import ujson
import umqtt.simple
import AppBase

class CAppSwitch(AppBase.CAppBase):
    """
    inherited class for a switch application
    """

    def __init__(self, device='switch',device_id="0",btn_pin = AppBase.CAppBase.GPIO26,btn1_pin = AppBase.CAppBase.GPIO4,github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,device_id=device_id,github_repo=github_repo)
        self.btn_pin    = btn_pin
        self.btn1_pin   = btn1_pin
        self.last_state  = 0
        self.last_state1 = 0
        self.set_switch_devicename_id()

    def set_switch_devicename_id(self):
        # command messages
        #   request for state
        self.topic_cmnd_state_msg  = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/state"
        self.topic_cmnd_state1_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/state1"
        # publish messages
        #   publish state of switch
        self.topic_state_msg  = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/state"
        self.topic_state1_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/state1"

    def create_switch(self):
        """
        create a button interface
        """
        self.btn  = machine.Pin(self.btn_pin,  machine.Pin.IN)
        self.btn1 = machine.Pin(self.btn1_pin, machine.Pin.IN)

    def publish_switch_state(self):
        self.mqtt_client.publish(self.topic_state_msg,bytes(str(self.last_state),"utf-8"))

    def publish_switch_state1(self):
        self.mqtt_client.publish(self.topic_state1_msg,bytes(str(self.last_state1),"utf-8"))

    def check_switch(self):
        """
        checks the button state - and sends message on change
        """
        act_state = self.btn.value()
        # state changed
        if self.last_state != act_state:
            self.last_state = act_state
            self.publish_switch_state()

    def check_switch1(self):
        """
        checks the button state1 - and sends message on change
        """
        act_state1 = self.btn1.value()
        # state changed
        if self.last_state1 != act_state1:
            self.last_state1 = act_state1
            self.publish_switch_state1()

    def mqtt_switch_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)
        if topic == self.topic_cmnd_state_msg:
            self.publish_switch_state()
        if topic == self.topic_cmnd_state1_msg:
            self.publish_switch_state1()

    def begin(self):
        """
        start function for the switch application
        """
        super().begin()
        self.set_switch_devicename_id()
        # create button interface
        self.create_switch()
        # subscribe to command message for state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_state_msg)
        # subscribe to command message for state1
        self.mqtt_subscribe_to_msg(self.topic_cmnd_state1_msg)
        # overwrite callback of base class
        self.set_subscribe_cb(self.mqtt_switch_subscribe_cb)

def main():   
    """
    main program - explicit coded for testability
    """
    app_switch = CAppSwitch("switch")
    app_switch.begin()
    while True:
        app_switch.check_switch()
        app_switch.check_switch1()
        app_switch.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    