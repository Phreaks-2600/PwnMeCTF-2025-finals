# 3xF1ltr4t0r 

## Description :
Some strange access point with a web server is open, named: `PWNME_APX`.
I suspect it might be a rogue access point because I tried to log in, but I dont get my WiFi !
It’s up to you to investigate and find out how it exfiltrates your data!
This 3xF1ltr4t0r is build for esp32
Searc OTA :wink: 

## Author:
- [Eun0us](https://github.com/Eun0us)

## Difficulty: 
- Easy

## Usage
```sh
cd build/
pip install esptool
7z x 3xFilt.7z
```

```sh
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash \
  0x1000   AP.ino.bootloader.bin \
  0x8000   AP.ino.partitions.bin \
  0x10000  AP.ino.bin
```



## Writeups:
- N/A