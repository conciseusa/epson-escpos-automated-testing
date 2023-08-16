#!/usr/bin/python

# run with `python3 test-runner.py`

# If PySerial not installed, install as root or consider a python virtual environment
# sudo apt install python3-pip
# sudo pip3 install pyserial
# If you see Permission denied: '/dev/ttyS0' / or port trying to use, adding user to the dialout group may fix the error
# sudo adduser YourUserName dialout # logout, login and try again

import serial
from datetime import datetime
import time

serial_host  = ''
# Linux beaglebone 4.19.94-ti-r73
serialp  = '/dev/ttyS1' # /dev/ttyS1 at pins 24, 26 # sudo apt-get install python3-serial if No module named 'serial' Error
serial_host  = 'Beaglebone Black' # restart: sudo shutdown -r now / shutdown: sudo shutdown -h now

# While this is Python and can run many places, the testing IO code is written for the beaglebone black.

# Below are some ports that can be used to talk to the printer on other platforms.
# Windows built in serial port
#serialp  = 'COM1'
#serial_host  = 'Windows'
# USB serial port
#serialp  = '/dev/ttyUSB0'
# Ubuntu on box with built-in serial port
# Tested with Epson TM-T20II connected with a Monoprice #479 6ft Null Modem DB9F/DB25M Molded Cable
#serialp  = '/dev/ttyS0'
#serial_host  = 'Ubuntu'
# Pine A64
#serialp  = '/dev/ttyS2'
#serial_host  = 'Pine A64'
# Raspberry Pi, may need to setup serial port first
#serialp  = '/dev/serial0'
#serial_host  = 'Raspberry Pi'

from Adafruit_BBIO import UART
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO

ADC.setup()
GPIO.setup("P8_19", GPIO.IN, GPIO.PUD_UP) # Push button to trigger tests. Button pulls down when pushed.

# Some common TM-T20II commands, should work on other printers, but need to be tested.
init=b'\x1b\x40' # ESC @ Initialize printer
lf=b'\x0a' # LF Prints the data in the print buffer and feeds one line
gs=b'\x1d' # GS Group Separator
cut=gs+b'\x56\x00'; # GS V x00 worked on TM-T20II
get_paper_status=b'\x10\x04\x04'

# https://stackoverflow.com/questions/59887559/python-send-escpos-command-to-thermal-printer-character-size-issue
def magnify(wm, hm): # Code for magnification of characters.
    # wm: Width magnification from 1 to 8. Normal width is 1, double is 2, etc.
    # hm: Height magnification from 1 to 8. Normal height is 1, double is 2, etc.
    return bytes([0x1d, 16*(wm-1) + (hm-1)])

def text(t, encoding="ascii"): # Code for sending text to printer.
    return bytes(t, encoding)

enable_printer = True # True  False
if enable_printer:
    UART.setup('UART1')
    ser = serial.Serial(serialp, 38400, timeout=10)
    ser.write(init)

dut_id = 'P783F-LM317'

def test_result(test_name, pass_chain, in_lgo, in_hgo, out_lgo, out_hgo):
    vin = ADC.read_raw("P9_40")/100
    vout = ADC.read_raw("P9_39")/100
    vout *= 1.03 # first unit built with 470 trimmers, was not enough, use this hack until hardware updated
    test_go = vin >= in_lgo and vin <= in_hgo and vout >= out_lgo and vout <= out_hgo
    pass_chain = test_go if not test_go else pass_chain # set pass chain to False if a test fails
    result_str = "Vin: {0:.1f} Vout: {1:.1f} Passed: {2}"
    result = result_str.format(vin, vout, str(test_go))
    print(test_name)
    print(result)
    if enable_printer:
        ser.write(text(test_name))
        ser.write(lf)
        ser.write(text(result))
        ser.write(lf)

    return pass_chain

print('Init done. Waiting for button press...')

while True:
    print('Waiting for button press...')
    GPIO.wait_for_edge("P8_19", GPIO.FALLING) # GPIO.RISING

    print("")
    print("DUT: " + dut_id)

    if enable_printer:
        ser.write(text("DUT: " + dut_id))
        ser.write(lf)

        ser.write(text("The time is: "))
        now = datetime.now()
        ser.write(text("{}".format(now.strftime("%Y/%m/%d %H:%M:%S"))))
        ser.write(lf)

        # ser.write(magnify(2, 2)) # did not seem to do anything on TM-T20II

        count = 3 # disable for now
        while count <= 2:
            ser.write(text("Sent {} line(s)".format(count)))
            ser.write(lf)
            time.sleep(1)
            count += 1

        # Read a value to test printer sending serial data
        ser.write(get_paper_status)
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
        if paper_status != "12": # show if there is a problem
            print('Warning: ', paper_status_text)
            ser.write(lf)
            ser.write(text("Warning: {}".format(paper_status_text)))

    #value = ADC.read("P9_40") # read returns values 0-1.0 

    # read_raw returns non-normalized value
    # use voltage divider: 221K | 10K + 1K trimmer for .01V per ADC level, .1 uf cap at ADC input adds low pass filter
    count = 0 # set to greater then 1 to loop and make it easier to set trimmers, etc.
    while count:
        vin = ADC.read_raw("P9_40")
        print("A1 Vin: ", vin)
        vout = ADC.read_raw("P9_39")
        vout *= 1.03 # first unit built with 470 trimmers, was not enough, use this hack until hardware updated
        print("A0 Vout: ", vout)
        count -= 1

    GPIO.setup("P8_7", GPIO.OUT) # test voltage in, on is higher
    #GPIO.setup("GPIO0_26", GPIO.OUT)  # Alternative: use actual pin names
    GPIO.setup("P8_9", GPIO.OUT) # not used
    GPIO.setup("P8_11", GPIO.OUT) # 22 ohm load
    GPIO.setup("P8_13", GPIO.OUT) # 100 ohm load
    GPIO.setup("P8_15", GPIO.OUT) # DUT enable

    vinnll = 11.8 # Vin normal low limit
    vinnhl = 12.5 # Vin normal high limit
    vinhll = 22 # Vin higher low limit
    vinhhl = 24.5 # Vin higher high limit
    voutll = 7.8 # Vout low limit
    vouthl = 8.2 # Vout high limit
    on_time = 2 # in seconds
    pass_chain = True # starts off passing, set to false if there is a failure in a test
    GPIO.output("P8_15", GPIO.HIGH)
    time.sleep(on_time)
    pass_chain = test_result("No Load", pass_chain, vinnll, vinnhl, voutll, vouthl)
    GPIO.output("P8_7", GPIO.HIGH)  # You can also write '1' instead
    time.sleep(on_time)
    pass_chain = test_result("Higher Vin, No Load", pass_chain, vinhll, vinhhl, voutll, vouthl)
    GPIO.output("P8_7", GPIO.LOW)   # You can also write '0' instead
    #PIO.output("P8_9", GPIO.HIGH)
    #time.sleep(on_time)
    #GPIO.output("P8_9", GPIO.LOW)
    GPIO.output("P8_11", GPIO.HIGH)
    time.sleep(on_time)
    pass_chain = test_result("~.36A Load", pass_chain, vinnll, vinnhl, voutll, vouthl)
    GPIO.output("P8_11", GPIO.LOW)
    GPIO.output("P8_13", GPIO.HIGH)
    time.sleep(on_time)
    pass_chain = test_result("~.08A Load", pass_chain, vinnll, vinnhl, voutll, vouthl)
    GPIO.output("P8_11", GPIO.HIGH) # turn on both loads
    time.sleep(on_time)
    pass_chain = test_result("~.44A Load", pass_chain, vinnll, vinnhl, voutll, vouthl)
    GPIO.output("P8_7", GPIO.HIGH) # increase input voltage
    time.sleep(on_time)
    pass_chain = test_result("Higher Vin, ~.44A Load", pass_chain, vinhll, vinhhl, voutll, vouthl)
    GPIO.output("P8_15", GPIO.LOW)
    time.sleep(on_time)
    pass_chain = test_result("Disable, Higher Vin, ~.44A Load", pass_chain, vinhll, vinhhl, 0, .1)
    GPIO.output("P8_7", GPIO.LOW)
    GPIO.output("P8_11", GPIO.LOW)
    GPIO.output("P8_13", GPIO.LOW)
    if enable_printer:
        ser.write(text("All tests passed: " + str(pass_chain)))
        ser.write(lf)

    if enable_printer:
        # all tests done finish printing
        ser.write(lf+lf+lf+lf) # move printed area above blade
        ser.write(cut)

    # wait for run button to be releases so a stuck button will not burn out all the printer paper
    while not GPIO.input("P8_19"):
        print('Tests done. Waiting for button release...')
        time.sleep(1)
