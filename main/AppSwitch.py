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

    def __init__(self, device='switch',btn_pin = AppBase.CAppBase.D6,github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,github_repo=github_repo)
        self.btn_pin = btn_pin
        self.last_state = 0 
        # command messages
        #   request for state
        self.topic_cmnd_state_msg = self.topic + b"/" + self.bdevice + b"/cmnd/state"
        # publish messages
        #   publish state of switch
        self.topic_state_msg = self.topic + b"/" + self.bdevice + b"/state"

    def create_switch(self):
        """
        create a button interface
        """
        self.btn = machine.Pin(self.btn_pin, machine.Pin.IN)

    def publish_switch_state(self):
        self.mqtt_client.publish(self.topic_state_msg,self.last_state)

    def check_switch(self):
        """
        checks the button state - and sends message on change
        """
        act_state = self.btn.value()
        # state changed
        if self.last_state != act_state:
            self.last_state = act_state
            self.publish_switch_state()

    def mqtt_switch_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)
        if topic == self.topic_cmnd_state_msg:
            self.publish_switch_state()

    def begin(self):
        """
        start function for the switch application
        """
        super().begin()
        # create button interface
        self.create_switch()
        # subscribe to command message for state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_state_msg)
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
        app_switch.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    