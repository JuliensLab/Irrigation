#!/usr/bin/python
# -*- coding:UTF-8 -*-

from bottle import *
import VisionFive.gpio as GPIO
import socket

#GPIO Pin
Relay = [37, 38, 40]

#All the relay
Relay1 = 1
Relay2 = 1
Relay3 = 1

for i in range(3):
    GPIO.setup(Relay[i], GPIO.OUT)
    GPIO.output(Relay[i], GPIO.HIGH)

@get("/")
def index():
  global Relay1,Relay2,Relay3
  
  Relay1 = 1
  Relay2 = 1
  Relay3 = 1
  
  return static_file('index.html', './')

@route('/<filename>')
def server_Static(filename):
    return static_file(filename, root='./')

@route('/Relay', method="POST")
def Relay_Control():
  global Relay1,Relay2,Relay3
  
  Relay1 = request.POST.get('Relay1')
  Relay2 = request.POST.get('Relay2')
  Relay3 = request.POST.get('Relay3')
  GPIO.output(Relay[0], int(Relay1))
  GPIO.output(Relay[1], int(Relay2))
  GPIO.output(Relay[2], int(Relay3))
  
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
localhost = s.getsockname()[0]

run(host=localhost, port="8000")

