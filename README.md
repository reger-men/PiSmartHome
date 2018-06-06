# PiSH
PiSH: Smart Home on Pi
PiSH was developed to detect any anomalies (motion, fire,...) in image sequence. The fact that the camera does not necessarily have to be in wired connected with the server, makes it easy to monitor different potential locations simultaneously from the same system. To avoid unnecessary memory space usage, this system only saves images where an anomaly has been detected.
# Installation 

## Install necessary libraries 
- ```sudo su```
- ```chmod +x install_opencv.sh```
- ```sh ./install_opencv.sh``` 
- ```sudo easy_install pip```
- ```sudo pip install picamera```

## Setup config files
- utils.py: Set your email address and password to be used by the system.
- conf.json: Set your email address to be noticed for each alert

## Run the agent
- ```python server.py ```
- Go to given URL on the terminal
- Start or stop the system. Stop the PiSH system once when you come home, to avoid any false alarm.

## How to run
PiSH support either PiCamera or URL-Streaming, to define which one to use, please set the arguments ```-s or --source``` to cam or stream1, stream2,...

- ```python server.py ```

OR run the surveillance directly.
- ```python pi_surveillance.py -c conf.json -s stream1 ```

https://onvif-spotlight.bemyapp.com/#/projects/5b12b2dae67b8e00047120d3
