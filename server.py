#!/usr/bin/env python

import time
time.sleep(30)
import argparse
import socket
import sys
import glob
import threading
import os
import Adafruit_PCA9685
import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD
from datetime import datetime

des_temp = 20.0

current_temp = "0" # vairiable for holding the current temp

HOST = '192.168.0.21'   # Symbolic name meaning all available interfaces
PORT = 1884 # Arbitrary non-privileged port

turn_on_off_count = 0 # counter for the turn off or on
turn_on_off_times = 5 # amount of times to test before heating turns on or off

run_event = threading.Event() # this is for cleanly stopping threads and is the condition for the while loops

lcd = CharLCD(numbering_mode=GPIO.BOARD, cols=16, rows=2, pin_rs=37, pin_e=19, pins_data=[33, 31, 29, 23])
lcd.clear()
lcd_counter = 0
adjust_lcd_time = 5 # time untill lcd changes back to default display

GPIO.setmode(GPIO.BOARD)

# setup for push switches
up_button_pin = 12
down_button_pin = 16
GPIO.setup(up_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(down_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
button_pressed = False

# Pin setup for rgb led
redPin   = 40
greenPin = 38
bluePin  = 36

# servo setup
servo_channel = 0 # set servo channel
servo_speed = .02 # servo speed between steps
servo_steps = 1 # distance the server will travel in each step

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()
servo_min = 300  # Min pulse length out of 4096
servo_max = 520  # Max pulse length out of 4096
pwm.set_pwm_freq(60)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# set up for temperature SENSOR
base_dir = '/sys/bus/w1/devices/'
top_sensor = base_dir + '28-0316823cdeff' + '/w1_slave'
bottom_sensor = base_dir + '28-03168244b4ff' + '/w1_slave'
# device_file = device_folder + '/w1_slave'

# rgb led set up
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)

GPIO.output(redPin, GPIO.LOW)
GPIO.output(greenPin, GPIO.LOW)
GPIO.output(bluePin, GPIO.LOW)

heating_on_off = False

def server(run_event):
	try :
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print('Socket created')
	except socket.error as msg :
		print('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])

	# Bind socketto local host and port
	try:
		s.bind((HOST, PORT))
		s.settimeout(10)
	except socket.error as msg:
		print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])

	print('Socket bind complete')

	#now keep talking with the client
	while run_event.is_set():
		try:
			# receive data from client (data, addr)
			d = s.recvfrom(1024)
			data = d[0]
			addr = d[1]

			if not data:
				continue
			data = current_temp
			reply = data

			s.sendto(data , addr)
			print('Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + data.strip())
		except socket.timeout:
			print("socket timeout")
			continue
		except KeyboardInterrupt:
			print('shutting down socket')
			s.close()
			sys.exit()


	s.close()
	sys.exit()

	print("closing socket")
	s.close()

class NewButton():
	def __init__(self, pin,up = True):
		self.pin = pin
		self.up = up
	def loop(self,run_event):
		global des_temp
		global button_pressed
		global lcd_counter
		while run_event.is_set():
			button_state = GPIO.input(self.pin)
			if button_state == False:
				if self.up:
					des_temp += 0.5
				else:
					des_temp -= 0.5
				print("Up button pressed. New desired temp: " + str(des_temp))
				button_pressed = True
				lcd_counter = 0
				time.sleep(0.2)

button_up = NewButton(up_button_pin)
button_down = NewButton(down_button_pin, False)

def lcd_write(line, text):
	if len(text) < 16:
		print("the text is shorter for the lcd by" + str((16 - len(text))))
		output = text + " " * (16 - len(text))
	else:
		output = text
	lcd.cursor_pos = (line, 0)
	lcd.write_string(output)

def read_temp_raw(sensor):
    f = open(sensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_c(sensor):
    lines = read_temp_raw(sensor)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = int(temp_string) / 1000.0 # TEMP_STRING IS THE SENSOR OUTPUT, MAKE SURE IT'S AN INTEGER TO DO THE MATH
        temp_c = str(round(temp_c, 1)) # ROUND THE RESULT TO 1 PLACE AFTER THE DECIMAL, THEN CONVERT IT TO A STRING
        return temp_c
def compare_temps():

	global current_temp

	a = read_temp_c(top_sensor)
	b = read_temp_c(bottom_sensor)

	if a <= b:
		current_temp = a
	else:
		current_temp = b
# Datagram (udp) socket

def servo(on_off):
	global heating_on_off
	print("servo test")
	if on_off == 1 and heating_on_off == False:
		print("turning the heating on.")
		GPIO.output(redPin, GPIO.LOW)
		GPIO.output(bluePin, GPIO.HIGH)
		adjust = servo_max
		while adjust > servo_min:
			pwm.set_pwm(servo_channel, 0, adjust)
			adjust -= servo_steps
			time.sleep(servo_speed)
		heating_on_off = True
	if on_off == 0 and heating_on_off == True:
		print("turning the heating off")
		GPIO.output(greenPin, GPIO.LOW)
		GPIO.output(bluePin, GPIO.HIGH)
		adjust = servo_min
		while adjust < servo_max:
			pwm.set_pwm(servo_channel, 0, adjust)
			adjust += servo_steps
			time.sleep(servo_speed)
		heating_on_off = False

def lcd_loop(run_event):
	global lcd_counter
	global button_pressed

	while run_event.is_set():
		if button_pressed == False:
			if len(str(turn_on_off_count)) > 1:
				count_string = str(turn_on_off_count)
			else:
				count_string = " " + str(turn_on_off_count)
			lcd_write(0, "Temp is:" + current_temp + " C" + count_string)
			lcd_write(1, "Desire temp:" + str(des_temp))
		else:
			lcd_write(0, "Change des Temp")
			lcd_write(1, "Desire temp:" + str(des_temp))
			lcd_counter += 1
			if lcd_counter == adjust_lcd_time:
				button_pressed = False
				lcd.clear()
		time.sleep(0.1)

def main(run_event):
	global des_temp
	while run_event.is_set():
		if heating_on_off == True:
			GPIO.output(bluePin, GPIO.LOW)
			GPIO.output(greenPin, GPIO.HIGH)
			GPIO.output(redPin, GPIO.LOW)
		else:
			GPIO.output(bluePin, GPIO.LOW)
			GPIO.output(redPin, GPIO.HIGH)
			GPIO.output(greenPin, GPIO.LOW)
		# print("The temperature is: "+ str(compare_temps()))
		print(des_temp)
		if float(current_temp) < des_temp:
			print("Trying to turn on heating")
			heating_on_off_logic(True)
		else:
			print("Trying to turn heating off")
			heating_on_off_logic(False)
		time.sleep(1)
		compare_temps()

#only turn on servo if the condition is met by turn_on_off_times. This is to stop the heating constantly turning on and off.
def heating_on_off_logic(on_or_off):
	global turn_on_off_count
	if on_or_off == True:
		turn_on_off_count += 1
	else:
		turn_on_off_count -= 1
	if turn_on_off_count == turn_on_off_times:
		turn_on_off_count = 0
		servo(1)
	elif turn_on_off_count == -turn_on_off_times:
		turn_on_off_count = 0
		servo(0)

def start():
	global run_event
	print("Warming up")
	GPIO.output(bluePin, GPIO.HIGH)
	servo(0)
	time.sleep(3)
	GPIO.output(bluePin, GPIO.LOW)
	run_event.set()
	t1 = threading.Thread(target=main, args = (run_event,))
	t2 = threading.Thread(target=button_up.loop, args = (run_event,))
	t3 = threading.Thread(target=button_down.loop, args = (run_event,))
	t4 = threading.Thread(target=lcd_loop, args = (run_event,))
	t5 = threading.Thread(target=server, args = (run_event,))
	t1.start()
	time.sleep(0.5)
	t2.start()
	time.sleep(0.5)
	t3.start()
	time.sleep(0.5)
	t4.start()
	time.sleep(0.5)
	t5.start()
	try:
		while 1:
			time.sleep(.1)
	except KeyboardInterrupt:
		print("turning heating off for standby mode")
		run_event.clear()
		t1.join()
		t2.join()
		t3.join()
		t4.join()
		t5.join()
		servo(0)
		lcd.clear()
		lcd_write(0, "System OFF as")
		lcd_write(1, str(datetime.now().strftime('%d-%m-%Y %H:%M')))
		print("cleaning pins")
		GPIO.cleanup()
		sys.exit()

if __name__ == '__main__':
	start()
