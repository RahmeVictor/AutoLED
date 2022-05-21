# AutoLED

## Info

Controls RGB lights using a website. Can be accessed from phone or pc. It uses minimal javascript and css to be as fast
to load as possible. Supports adding / renaming / removing controllers.

![](https://github.com/RahmeVictor/AutoLED/blob/master/images/AutoLED%20Showcase.gif)

## How it works

The user inputs the desired color and brightness or warmth, which is then sent to the P9813 controller through the PI's
GPIO. The controllers can be wired in series and are accessed through their IDs: the first controller has ID 0, the
second ID 1 etc...

Data about controllers is saved in controllers.json

GPIOSim is used to simulate Raspberry's GPIO pins. It provides dummy functions that do nothing.

## Requirements

- Raspberry pi
- P9813 based controller

Built using Flask and Python 3.10

## How to use

It can be used just as any Flask app. The main app is in AutoLED.py, it's recommended to use a WSGI server like
gunicorn and have it autorun when the device starts.

update.py automatically pulls from GitHub the latest commit.
