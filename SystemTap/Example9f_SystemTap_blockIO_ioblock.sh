#!/bin/bash

# This is an example launcher script for PyLatencyMap 
# Collect and display SystemTap data for the block I/O request calls as a Frequency-Intensity Latency HeatMap
# This can be used to investigate single-block read latency 
# Note this scripts requires to have SystemTap installed 

stap -v ./blockio_ioblock_pylatencymap.stp |python ./systemtap_connector.py |python ../LatencyMap.py

