#!/bin/bash

# This is an example launcher script for PyLatencyMap 
# Collect and display SystemTap data for the pread I/O request calls as a Frequency-Intensity Latency HeatMap
# This can be used to investigate pread system call latency 
# Note this scripts requires to have SystemTap installed 

stap -v SystemTap/pread_pylatencymap.stp 3 |python SystemTap/systemtap_connector.py |python LatencyMap.py

