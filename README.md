# AutoLED

## Info

Controls RGB lights using a website. Can be accessed from phone or pc. It uses minimal javascript and css to be as fast
to load as possible. Supports adding / renaming / removing controllers.

## How it works

The user inputs the desired color and brightness, which is then sent to the P9813 controller through the PI's GPIO. The
controllers can be wired in series and are accessed through their IDs: the first controller has ID 0, the second ID 1
etc...

Data about controllers is saved in controllers.conf

GPIOSim is used to simulate Raspberry's GPIO pins. It provides dummy functions that do nothing.

## Requirements

- Raspberry pi
- P9813 based controller

Built using Flask and Python 3.10

