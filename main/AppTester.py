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
        self.defaultpin  = 13 # pin for default init of pin
        self.pin_map = {
            "GPIO4": {
                    "PinPort": AppBase.CAppBase.GPIO4,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO4,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO16": {
                    "PinPort": AppBase.CAppBase.GPIO16,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO16,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO17": {
                    "PinPort": AppBase.CAppBase.GPIO17,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO17,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO25": {
                    "PinPort": AppBase.CAppBase.GPIO25,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO25,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO26": {
                    "PinPort": AppBase.CAppBase.GPIO26,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO26,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO27": {
                    "PinPort": AppBase.CAppBase.GPIO27,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO27,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO32": {
                    "PinPort": AppBase.CAppBase.GPIO32,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO32,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            },
            "GPIO33": {
                    "PinPort": AppBase.CAppBase.GPIO33,
                    "Pin"    : machine.Pin(AppBase.CAppBase.GPIO33,machine.Pin.IN),
                    "Mode"   : "",
                    "Publish": -1,
                    "State"  : -1
            }
        }
        self.set_tester_devicename_id()

    def set_tester_devicename_id(self):
        # command messages
        #   request for state
        self.topic_cmnd_setpinmode_msg          = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/setpinmode"
        self.topic_cmnd_getpinmode_msg          = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/getpinmode"
        self.topic_cmnd_setpin_msg              = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/setpin"
        self.topic_cmnd_getpin_msg              = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/getpin"
        self.topic_cmnd_publishpin_msg          = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/publishpin"
        self.topic_cmnd_statepin_msg            = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/statepin"
        self.topic_cmnd_setautopublishpin_msg   = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/setautopublishpin"
        self.topic_cmnd_getautopublishpin_msg   = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/getautopublishpin"
        
        # publish messages
        #   publish state of tester
        self.topic_statepin_msg       = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/statepin"
        self.topic_modepin_msg        = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/modepin"
        self.topic_autopublishpin_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/autopublishpin"

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
            if self.pin_map[pin]['Publish'] == 1:
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

        # get pinmode command found
        if self.topic_cmnd_getpinmode_msg in topic:
            pin = (topic.replace(self.topic_cmnd_getpinmode_msg + b"/",b"")).decode("utf-8")
            if pin in self.pin_map:
                mode = self.pin_map[pin]['Mode']
                self.mqtt_client.publish(self.topic_modepin_msg + bytes("/" + pin,'utf-8'),mode)

        # set pin command found
        if self.topic_cmnd_setpin_msg in topic:
            pin = topic.replace(self.topic_cmnd_setpin_msg + b"/",b"")
            self.set_pin((pin).decode("utf-8"),payload.decode("utf-8"))

        # request state command
        if self.topic_cmnd_getpin_msg in topic:
            pin = topic.replace(self.topic_cmnd_getpin_msg + b"/",b"")
            if self.get_pin(pin.decode("utf-8"))[1] == True:
                self.publish_pin_state(pin.decode("utf-8"))

        # set autopublish pin command
        if self.topic_cmnd_setautopublishpin_msg in topic:
            pin = (topic.replace(self.topic_cmnd_setautopublishpin_msg + b"/",b"")).decode("utf-8")
            if pin in self.pin_map:
                self.pin_map[pin]['Publish'] = int(payload)

        # get autopublish pin state command found
        if self.topic_cmnd_getautopublishpin_msg in topic:
            pin = (topic.replace(self.topic_cmnd_getautopublishpin_msg + b"/",b"")).decode("utf-8")
            if pin in self.pin_map:
                appmode = self.pin_map[pin]['Publish']
                self.mqtt_client.publish(self.topic_autopublishpin_msg + bytes("/" + str(pin),'utf-8'),str(appmode))

    def begin(self):
        """
        start function for the tester application
        """
        super().begin()
        self.set_tester_devicename_id()
        # subscribe to command message for set pinmode
        self.mqtt_subscribe_to_msg(self.topic_cmnd_setpinmode_msg + b"/#")
        # subscribe to command message for get pinmode
        self.mqtt_subscribe_to_msg(self.topic_cmnd_getpinmode_msg + b"/#")
        # subscribe to command message for set pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_setpin_msg + b"/#")
        # subscribe to command message for get pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_getpin_msg + b"/#")
        # subscribe to command message for set autopublish pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_setautopublishpin_msg + b"/#")
        # subscribe to command message for get autopublish pin state
        self.mqtt_subscribe_to_msg(self.topic_cmnd_getautopublishpin_msg + b"/#")
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
    