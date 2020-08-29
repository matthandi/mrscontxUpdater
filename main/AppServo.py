"""
App template file
can be used to create a new Application like AppLed, AppSwitch,...
"""

import sys
sys.path.append('/main')
import machine
import time
import ujson
import umqtt.simple
import AppBase

class CAppServo(AppBase.CAppBase):
    """
    inherited class for a servo application
    """

    def __init__(self, device='servo',device_id="0",servo_pin = AppBase.CAppBase.GPIO4,github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,device_id = device_id,github_repo=github_repo)
        self.position = 0
        self.freqency = 50
        self.servo_pin = servo_pin
        self.servo = machine.PWM(servo_pin,freq=self.freqency,duty=self.position)
        self.set_servo_devicename_id()

    def set_servo_devicename_id(self):
        self.prefix_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id
        # command messages
        self.topic_cmnd_set_pos_msg = self.prefix_msg + b"/cmnd/setpos"
        self.topic_cmnd_get_pos_msg = self.prefix_msg + b"/cmnd/getpos"
        # publish messages
        #   publish pos
        self.topic_pos_msg = self.prefix_msg + b"/pos"

    def mqtt_servo_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes - will be called, if a subscribed mqtt message is received
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)

        # request set pos command
        if topic == self.topic_cmnd_set_pos_msg:
            self.position = int(str(payload).encode('utf-8')) * 1024/100
            self.servo.duty(self.position)

        # request get pos command
        if topic == self.topic_cmnd_get_pos_msg:
            self.mqtt_client.publish(self.topic_pos_msg,str(self.position))


    def begin(self):
        """
        start function for the TPL application
        """
        super().begin()
        self.set_servo_devicename_id()
        # TODO: add your init calls here
        #       ...

        # TODO: add your subscribes to mqtt messages here
        #       ...
        # subscribe to command message for set pos
        self.mqtt_subscribe_to_msg(self.topic_cmnd_set_pos_msg)
        # subscribe to command message for get pos
        self.mqtt_subscribe_to_msg(self.topic_cmnd_get_pos_msg)

def main():   
    """
    main program - explicit coded for testability
    """
    app_servo = CAppServo("servo")
    app_servo.begin()
    while True:
        # check for mqtt messages
        app_servo.check_msg()
        # speed down the application a little bit
        # should not be removed, otherwise testing is not possible
        time.sleep(0.1)

if __name__ == "__main__":
    main()
    