import sys
sys.path.append('/main')
import machine
import time
import ujson
import umqtt.simple
import ssd1306
import AppBase

class CAppDisplay(AppBase.CAppBase):
    """
    inherited class for a display application
    """
    GPIO15 = 15
    def __init__(self, device='display',github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,github_repo=github_repo)
        # command messages
        #   request for state
        self.topic_cmnd_fill_msg    = self.topic + b"/" + self.bdevice + b"/cmnd/fill"
        self.topic_cmnd_settext_msg = self.topic + b"/" + self.bdevice + b"/cmnd/settext"
        self.topic_cmnd_gettext_msg = self.topic + b"/" + self.bdevice + b"/cmnd/gettext"
        # publish messages
        #   publish state of led
        self.topic_text_msg = self.topic + b"/" + self.bdevice + b"/text"
        self.dspl_onoff_state = 1
 
    def create_display(self):
        """
        creates a led interface
        """
        from machine import I2C, Pin
        self.dspl_onoff = machine.Pin(CAppDisplay.GPIO16,machine.Pin.OUT)
        self.dspl_onoff.value(self.dspl_onoff_state)
        self.i2c = machine.I2C(-1,scl=machine.Pin(CAppDisplay.GPIO15),sda=machine.Pin(AppBase.CAppBase.GPIO4))
        self.dspl = ssd1306.SSD1306_I2C(128, 64, self.i2c)
        self.dspl.fill(0)
        self.dspl.show()

    def publish_display_text(self):
        self.mqtt_client.publish(self.topic_state_msg,str(self.last_state))

    def mqtt_display_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)

        # request fill display command
        if topic == self.topic_cmnd_fill_msg:
            self.dspl.fill(int(payload))
            self.dspl.show()


        # request display set text at pos x,y command
        if topic == self.topic_cmnd_settext_msg:
            try:
                data = str(payload).replace("b'","").replace("'","").split(",")
                text = data[0]
                x = int(data[1])
                y = int(data[2])
                self.dspl.text(text,x,y) 
                self.dspl.show()
            except: 
                self.publish_error_message("invalid displaytext: " + str(payload))

    def begin(self):
        """
        start function for the led application
        """
        super().begin()
        # create button interface
        self.create_display()
        # subscribe to command message for set text
        self.mqtt_subscribe_to_msg(self.topic_cmnd_settext_msg)
        # subscribe to command message for get text
        self.mqtt_subscribe_to_msg(self.topic_cmnd_gettext_msg)
        # subscribe to command message for fill display
        self.mqtt_subscribe_to_msg(self.topic_cmnd_fill_msg)
        # overwrite callback of base class
        self.set_subscribe_cb(self.mqtt_display_subscribe_cb)

def main():   
    """
    main program - explicit coded for testability
    """
    app_display = CAppDisplay("display")
    app_display.begin()
    while True:
        app_display.check_msg()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    