### send a sms through an attached serial device
## HOW IT WORKS: 
## DEPENDENCIES:
# OS:
# Python: pyserial
## CONFIGURATION:
# required: port, baud, to
# optional: 
## COMMUNICATION:
# INBOUND: 
# - NOTIFY: receive a notification request
# OUTBOUND: 

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import serial
from curses import ascii

from sdk.python.module.notification import Notification

import sdk.python.utils.exceptions as exception

class Gsm_sms(Notification):
    # What to do when initializing
    def on_init(self):
        # constants
        self.timeout = 15
        # configuration settings
        self.house = {}
        # require configuration before starting up
        self.config_schema = 1
        self.add_configuration_listener("house", 1, True)
        self.add_configuration_listener(self.fullname, "+", True)

    # What to do when running
    def on_start(self):
        pass
        
    # What to do when shutting down
    def on_stop(self):
        pass
        
    # send a command to the modem and parse the response
    def modem_write(self, modem, command, sleep=2):
        # send command to the modem
        self.log_debug("Modem write: "+str(command).rstrip())
        modem.write(command)
        # wait for a response
        self.sleep(sleep)
        output = modem.readlines()
        for line in output:
                line = str(line).rstrip()
                if line == "": continue
                self.log_debug("Modem read: "+line)
                if "+CMGS:" in line:
                    self.log_info("SMS sent successfully")
                    return True
                if "ERROR" in line:
                    self.log_info("Error while sending message: "+line)
                    return True
        return False

        
   # What to do when ask to notify
    def on_notify(self, severity, text):
        text = "["+self.house["name"]+"] "+text
        # truncate the text
        text = (data[:150] + '..') if len(text) > 150 else text
        # connect to the modem
        try:
            self.log_debug("Connecting to GSM modem on port "+self.config["port"]+" with baud rate "+str(self.config["baud"]))
            modem = serial.Serial(self.config["port"], self.config["baud"], timeout=5)
        except Exception,e:
            self.log_error("Unable to connect to the GSM modem: "+exception.get(e))
            return
        # for each recipient
        for to in self.config["to"].split(","):
            try: 
                i = self.timeout
                while True:
                    # send the sms
                    if i == self.timeout: 
                        self.log_debug("Sending SMS "+str(to))
                        self.sleep(2)
                        # enable radio
                        if self.modem_write(modem, b'AT +CFUN=1\r', 10): break
                        # switch to text mode
                        if self.modem_write(modem, b'AT+CMGF=1\r'): break
                        # set the recipient number
                        if self.modem_write(modem, b'AT+CMGS="' + str(to).encode() + b'"\r'): break
                        # send the message
                        if self.modem_write(modem, text.encode()): break
                        # end the message with ctrl+z
                        if self.modem_write(modem, ascii.ctrl('z')): break
                    i = i - 1
                    if i == 0:
                        # timeout reached
                        self.log_error("Unable to send SMS to "+str(to)+": timeout reached")
                        break
                    self.sleep(1)
            except Exception,e:
                self.log_error("Failed to send SMS to "+str(to)+": "+exception.get(e))
        # disconect
        modem.close()

     # What to do when receiving a new/updated configuration for this module    
    def on_configuration(self, message):
        if message.args == "house" and not message.is_null:
            if not self.is_valid_configuration(["name"], message.get_data()): return False
            self.house = message.get_data()
        # module's configuration
        if message.args == self.fullname and not message.is_null:
            if message.config_schema != self.config_schema: 
                return False
            if not self.is_valid_configuration(["port", "baud", "to"], message.get_data()): return False
            self.config = message.get_data()