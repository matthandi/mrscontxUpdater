"""
AppPwm - application for handling PWM signals
"""

import sys
sys.path.append('/main')
import machine
import time
import ujson
import umqtt.simple
import AppBase

class CAppPwm(AppBase.CAppBase):
    """
    inherited class for a pwm application
    """

    def __init__(self, device='pwm',device_id="0",pwm_pin = AppBase.CAppBase.GPIO4,github_repo="https://github.com/matthandi/mrscontxUpdater"):
        """
        constructor
        """
        super().__init__(device=device,device_id = device_id,github_repo=github_repo)
        self.duty     = 77
        self.frequency = 50
        self.pwm_pin  = machine.Pin(pwm_pin,machine.Pin.OUT)
        self.pwm = machine.PWM(self.pwm_pin,freq=self.frequency,duty=self.duty)
        self.set_pwm_devicename_id()

    def set_pwm_devicename_id(self):
        self.prefix_msg = self.topic + b"/" + self.bdevice + b"/" + self.bdevice_id
        # command messages
        self.topic_cmnd_set_duty_msg      = self.prefix_msg + b"/cmnd/setduty"
        self.topic_cmnd_get_duty_msg      = self.prefix_msg + b"/cmnd/getduty"
        self.topic_cmnd_set_frequency_msg = self.prefix_msg + b"/cmnd/setfrequency"
        self.topic_cmnd_get_frequency_msg = self.prefix_msg + b"/cmnd/getfrequency"
        self.topic_cmnd_duty_sweep_msg    = self.prefix_msg + b"/cmnd/dutysweep"
        # publish messages
        #   publish duty
        self.topic_duty_msg      = self.prefix_msg + b"/duty"
        self.topic_frequency_msg = self.prefix_msg + b"/frequency"

    def mqtt_pwm_subscribe_cb(self,topic,payload):
        """
        callback function for mqtt subscribes - will be called, if a subscribed mqtt message is received
        """
        # call callback function from base class
        super().mqtt_subscribe_cb(topic,payload)

        # request set duty command
        if topic == self.topic_cmnd_set_duty_msg:
            self.duty = int(payload)
            self.pwm.duty(self.duty)

        # request get duty command
        if topic == self.topic_cmnd_get_duty_msg:
            self.mqtt_client.publish(self.topic_duty_msg,str(self.duty).encode('utf-8'))

        # request set frequency command
        if topic == self.topic_cmnd_set_frequency_msg:
            self.frequency = int(payload)
            self.pwm.freq(self.frequency)

        # request get frequency command
        if topic == self.topic_cmnd_get_frequency_msg:
            self.mqtt_client.publish(self.topic_frequency_msg,str(self.frequency).encode('utf-8'))

        # request duty sweep
        if topic == self.topic_cmnd_duty_sweep_msg:
            try:
                # expected: duty_min, duty_max, duration
                #             65    , 120     , 1500
                [d_min,d_max,d_duration] = str(payload,'utf-8').split(",")
                d_range = int(d_max) - int(d_min)
                step_wait = int(d_duration) / abs(d_range) / 1000.
                step = -1 if d_range < 0 else 1
                for d in range(int(d_min),int(d_max)+1*step,step):
                    self.duty = d
                    self.pwm.duty(d)
                    time.sleep(step_wait)

            except (ZeroDivisionError,IndexError,KeyError,OSError,TypeError,ValueError):
                self.publish_error_message("Invalid dutysweep data: " + payload)

    def begin(self):
        """
        start function for the TPL application
        """
        super().begin()
        self.set_pwm_devicename_id()
        # subscribe to command message for set duty
        self.mqtt_subscribe_to_msg(self.topic_cmnd_set_duty_msg)
        # subscribe to command message for get duty
        self.mqtt_subscribe_to_msg(self.topic_cmnd_get_duty_msg)
        # subscribe to command message for set frequency
        self.mqtt_subscribe_to_msg(self.topic_cmnd_set_frequency_msg)
        # subscribe to command message for get frequency
        self.mqtt_subscribe_to_msg(self.topic_cmnd_get_frequency_msg)
        # subscribe to command message for dutysweep
        self.mqtt_subscribe_to_msg(self.topic_cmnd_duty_sweep_msg)
        # overwrite callback of base class
        self.set_subscribe_cb(self.mqtt_pwm_subscribe_cb)

def main():   
    """
    main program - explicit coded for testability
    """
    app_pwm = CAppPwm("pwm")
    app_pwm.begin()
    while True:
        # check for mqtt messages
        app_pwm.check_msg()
        # speed down the application a little bit
        # should not be removed, otherwise testing is not possible
        time.sleep(0.1)

if __name__ == "__main__":
    main()
    