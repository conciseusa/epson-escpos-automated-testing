#!/usr/bin/python

# run with `python3 epson-escpos-hello-world-serial.py`
# If PySerial not installed, install as root or consider a python virtual environment
# sudo apt install python3-pip
# sudo pip3 install pyserial
# If you see Permission denied: '/dev/ttyS0' adding user to the dialout group may fix the error
# sudo adduser YourUserName dialout # logout, login and try again

import serial
from datetime import datetime
import time

serial_host  = ''
# Windows built in serial port
#serialp  = 'COM1'
#serial_host  = 'Windows'
# USB serial port
#serialp  = '/dev/ttyUSB0'
# Ubuntu on box with built-in serial port
# Tested with Epson TM-T20II connected with a Monoprice #479 6ft Null Modem DB9F/DB25M Molded Cable
serialp  = '/dev/ttyS0'
serial_host  = 'Ubuntu'
# Pine A64
#serialp  = '/dev/ttyS2'
#serial_host  = 'Pine A64'
# Raspberry Pi, may need to setup serial port first
#serialp  = '/dev/serial0'
#serial_host  = 'Raspberry Pi'
# Linux beaglebone 4.19.94-ti-r73
#serialp  = '/dev/ttyS1' # sudo apt-get install python3-serial if No module named 'serial' Error
#serial_host  = 'Beaglebone Black' # restart: sudo shutdown -r now / shutdown: sudo shutdown -h now
#from Adafruit_BBIO import UART # GPIO pins & UART need to be setup
#UART.setup('UART1')

# some common commands
init=b'\x1b\x40' # ESC @ Initialize printer
lf=b'\x0a' # LF Prints the data in the print buffer and feeds one line
gs=b'\x1d' # GS Group Separator
cut=gs+b'\x56\x00'; # GS V x00 worked on TM-T20II
paper_status=b'\x10\x04\x04'

# https://stackoverflow.com/questions/59887559/python-send-escpos-command-to-thermal-printer-character-size-issue
def magnify(wm, hm): # Code for magnification of characters.
    # wm: Width magnification from 1 to 8. Normal width is 1, double is 2, etc.
    # hm: Height magnification from 1 to 8. Normal height is 1, double is 2, etc.
    return bytes([0x1d, 16*(wm-1) + (hm-1)])

def text(t, encoding="ascii"): # Code for sending text.
    return bytes(t, encoding)

ser = serial.Serial(serialp, 38400, timeout=10)
ser.write(init)

ser.write(text("Hello World!"))
if serial_host:
    ser.write(text(" From {} land.".format(serial_host)))
ser.write(lf)

ser.write(text("The time is: "))
now = datetime.now()
ser.write(text("{}".format(now.strftime("%Y/%m/%d %H:%M:%S"))))
ser.write(lf)

# ser.write(magnify(2, 2)) # did not seem to do anything on TM-T20II

count = 1
while count <= 2:
    ser.write(text("Sent {} line(s)".format(count)))
    ser.write(lf)
    time.sleep(1)
    count += 1

# Read a value to test printer sending serial data
ser.write(paper_status)
paper_status = ser.read().hex()
# Print according to the hexadecimal value returned by the printer
if paper_status == "12":
    paper_status_text = 'Paper adequate'
elif paper_status == "1e":
    paper_status_text = 'Paper near-end detected by near-end sensor'
elif paper_status == "72":
    paper_status_text = 'Paper end detected by roll sensor'
elif paper_status == "7e":
    paper_status_text = 'Both sensors detect paper out'
else:
    paper_status_text = 'Unknown paper status value'
    # if the script stalls for the timeout period, and this is the paper status, read timed out
print(paper_status_text)
ser.write(lf)
ser.write(text("{}".format(paper_status_text)))

ser.write(lf+lf+lf+lf) # move printed area above blade
ser.write(cut)
