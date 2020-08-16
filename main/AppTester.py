import sys
sys.path.append('./main')
import machine
import time
import ujson
import umqtt.simple
import AppBase

class CAppTester(AppBase.CAppBase):
    """
    inherited class for a tester application
    """
    def __init__(self, device='tester',github_repo="https://api.github.com/repos/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,github_repo=github_repo)
        self.pinmode_in = machine.Pin.IN
        self.pinmode_out = machine.Pin.OUT
        self.pinmode_map = {"OUT": self.pinmode_out,"IN":self.pinmode_in}
        self.pin_map = {
            "D0": {
                    "PinPort": AppBase.CAppBase.D0,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D1": {
                    "PinPort": AppBase.CAppBase.D1,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D2": {
                    "PinPort": AppBase.CAppBase.D2,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D3": {
                    "PinPort": AppBase.CAppBase.D3,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D4": {
                    "PinPort": AppBase.CAppBase.D4,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D5": {
                    "PinPort": AppBase.CAppBase.D5,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D6": {
                    "PinPort": AppBase.CAppBase.D6,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "D7": {
                    "PinPort": AppBase.CAppBase.D7,
                    "Pin"    : machine.Pin(16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            }
        }

        # command messages
        #   request for state
        self.topic_cmnd_setpinmode_msg = self.topic + b"/" + self.bdevice + b"/cmnd/setpinmode"
        self.topic_cmnd_getpinmode_msg = self.topic + b"/" + self.bdevice + b"/cmnd/getpinmode"
        self.topic_cmnd_setpin_msg     = self.topic + b"/" + self.bdevice + b"/cmnd/setpin"
        self.topic_cmnd_getpin_msg     = self.topic + b"/" + self.bdevice + b"/cmnd/getpin"
        self.topic_cmnd_publishpin_msg = self.topic + b"/" + self.bdevice + b"/cmnd/publishpin"
        self.topic_cmnd_statepin_msg   = self.topic + b"/" + self.bdevice + b"/cmnd/statepin"
        # publish messages
        #   publish state of tester
        self.topic_statepin_msg = self.topic + b"/" + self.bdevice + b"/statepin"

    def set_pinmode(self,pin,pin_mode,val=0):
        """
        creates a tester interface
        """
        if pin in self.pin_map and pin_mode in self.pinmode_map:

            self.pin_map[pin]['Pin'] = machine.Pin(self.pin_map[pin]['PinPort'], self.pinmode_map[pin_mode])
            self.pin_map[pin]['Mode'] = pin_mode
            if pin_mode == "OUT":
                self.pin_map[pin]['Pin'].value(val)
                self.pin_map[pin]['State'] = val

            return True
        else:
            return False

    def set_pin(self,pin,val):
        """
        sets the tester pin state
        """

        if pin in self.pin_map:
            val = int(val)
            if self.pin_map[pin]['Mode'] == "OUT":
                self.pin_map[pin]['Pin'].value(val)
                self.pin_map[pin]['State'] = val
                return True
            else:
                return False
        else:
            return False

    def publish_in_pins(self):
        """
        publishes all pins with input mode on change
        """
        for pin in self.pin_map:
            if self.pin_map[pin]['Mode'] == "IN":
                oldstate = self.pin_map[pin]['State']
                retval = self.get_pin(pin)
                if retval[1] == True and retval[0] != oldstate:
                    self.pin_map[pin]['State'] = retval[0]
                    self.publish_pin_state(pin)
                    time.sleep(0.1)

    def publish_pin_state(self,pin):
        """
        publish state of pin
        """
        if pin in self.pin_map:
            self.mqtt_client.publish(self.topic_statepin_msg + bytes("/" + pin,'utf-8'),str(self.pin_map[pin]['State']))
            return True
        else:
            return False

    def get_pin(self,pin):
        """
        gets the tester pin state
        """
        if pin in self.pin_map:
            if self.pin_map[pin]['Mode'] == 'IN':
                val = self.pin_map[pin]['State'] = self.pin_map[pin]['Pin'].value()
                return [val,True]
            else:
                return [-1,False]
        else:
            return [-1,False]

    def mqtt_tester_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)

        # set pinmode command found
        if self.topic_cmnd_setpinmode_msg in topic:
            pin = topic.replace(self.topic_cmnd_setpinmode_msg + b"/",b"")
            self.set_pinmode((pin).decode("utf-8"),(payload).decode("utf-8"))

        # set pin command found
        if self.topic_cmnd_setpin_msg in topic:
            pin = topic.replace(self.topic_cmnd_setpin_msg + b"/",b"")
            self.set_pin((pin).decode("utf-8"),payload.decode("utf-8"))

        # request state command
        if self.topic_cmnd_getpin_msg in topic:
            pin = topic.replace(self.topic_cmnd_getpin_msg + b"/",b"")
            if self.get_pin(pin.decode("utf-8"))[1] == True:
                self.publish_pin_state(pin.decode("utf-8"))

    def begin(self):
        """
        start function for the tester application
        """
        super().begin()
        # subscribe to command message for set pinmode
        self.mqtt_subscribe_to_msg(self.topic_cmnd_setpinmode_msg + b"/#")
        # subscribe to command message for set pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_setpin_msg + b"/#")
        # subscribe to command message for get pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_getpin_msg + b"/#")
        # overwrite callback of base class
        self.set_subscribe_cb(self.mqtt_tester_subscribe_cb)

def main():   
    """
    main program - explicit coded for testability
    """
    app_tester = CAppTester("tester")
    app_tester.begin()
    while True:
        # publish all input pins on change
        app_tester.publish_in_pins()
        # check on new mqtt messages
        app_tester.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    