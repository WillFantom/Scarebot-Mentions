#!/bin/bash
/usr/bin/firefox -new-window 127.0.0.1:5000 &
sleep 20
xdotool key "F11"