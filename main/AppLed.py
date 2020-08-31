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
        self.r_led_pin = AppBase.CAppBase.GPIO25
        self.y_led_pin = AppBase.CAppBase.GPIO26
        self.g_led_pin = AppBase.CAppBase.GPIO27
        self.last_state   = 0
        self.r_last_state = 0 
        self.y_last_state = 0 
        self.g_last_state = 0 

        self.set_led_devicename_id()

    def set_led_devicename_id(self):
        # command messages
        #   request for state
        self.topic_cmnd_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/state"
        self.topic_cmnd_set_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/set"
        self.topic_cmnd_ryg_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/rygstate"
        self.topic_cmnd_ryg_set_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/rygset"
        self.topic_cmnd_ryg_sweep_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/cmnd/rygsweep"
        # publish messages
        #   publish state of led
        self.topic_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/state"
        self.topic_ryg_state_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id + b"/rygstate"

    def create_led(self):
        """
        creates a led interface
        """
        self.led = machine.Pin(self.led_pin, machine.Pin.OUT)
        self.r_led = machine.Pin(self.r_led_pin, machine.Pin.OUT)
        self.y_led = machine.Pin(self.y_led_pin, machine.Pin.OUT)
        self.g_led = machine.Pin(self.g_led_pin, machine.Pin.OUT)
        self.led.value(0)
        self.r_led.value(0)
        self.y_led.value(0)
        self.g_led.value(0)

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

        # set rygled command
        if topic == self.topic_cmnd_ryg_set_msg:
            # expected payload r,y,g
            try:
                [r,y,g] = str(payload,'utf-8').split(",")
                self.r_last_state = int(r)
                self.y_last_state = int(y)
                self.g_last_state = int(g)

                self.r_led.value(self.r_last_state)
                self.y_led.value(self.y_last_state)
                self.g_led.value(self.g_last_state)
            except (ZeroDivisionError,IndexError,KeyError,OSError,TypeError,ValueError):
                self.publish_error_message("Invalid rygset data: " + payload)

        # request rygstate command
        if topic == self.topic_cmnd_ryg_state_msg:
            ryg_state =   str(self.r_last_state) + "," + str(self.y_last_state) + "," + str(self.g_last_state)
            self.mqtt_publish_msg(self.topic_ryg_state_msg,
                                    ryg_state.encode('utf-8')
                                 )

        # request rygsweep command
        if topic == self.topic_cmnd_ryg_sweep_msg:
            # payload: ryg or gyr, <time>
            # example: ryg,1000
            try:
                [ryg_dir,ryg_time] = str(payload,'utf-8').split(",")
                wait_time = int(ryg_time) / 2. / 1000.
                if ryg_dir == 'ryg':
                    self.r_led.value(1)
                    self.y_led.value(0)
                    self.g_led.value(0)
                    time.sleep(wait_time)
                    self.r_led.value(1)
                    self.y_led.value(1)
                    self.g_led.value(0)
                    time.sleep(wait_time)
                    self.r_led.value(0)
                    self.y_led.value(0)
                    self.g_led.value(1)
                    self.r_last_state = 0
                    self.y_last_state = 0
                    self.g_last_state = 1
                elif ryg_dir == 'gyr':
                    self.r_led.value(0)
                    self.y_led.value(0)
                    self.g_led.value(1)
                    time.sleep(wait_time)
                    self.r_led.value(0)
                    self.y_led.value(1)
                    self.g_led.value(0)
                    time.sleep(wait_time)
                    self.r_led.value(1)
                    self.y_led.value(0)
                    self.g_led.value(0)
                    self.r_last_state = 1
                    self.y_last_state = 0
                    self.g_last_state = 0
                else:
                    raise ValueError

            except (ZeroDivisionError,IndexError,KeyError,OSError,TypeError,ValueError):
                self.publish_error_message("Invalid rygset data: " + payload)

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
        # subscribe to command message for rygstate
        self.mqtt_subscribe_to_msg(self.topic_cmnd_ryg_state_msg)
        # subscribe to command message for rygset
        self.mqtt_subscribe_to_msg(self.topic_cmnd_ryg_set_msg)
        # subscribe to command message for rygstate
        self.mqtt_subscribe_to_msg(self.topic_cmnd_ryg_sweep_msg)
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
    