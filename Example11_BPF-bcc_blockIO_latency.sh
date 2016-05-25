#!/bin/bash

# This is an example launcher script for PyLatencyMap
# Collect and display block I/O latency data using BPF-bcc/pylatencymap-biolatency.py
# This can be used to investigate block I/O latency
# Note this scripts requires BPF/bcc 
# Tested on: Fedora 24 (beta) using kernel v. 4.6

stdbuf -oL python BPF-bcc/pylatencymap-biolatency.py -QT 3 100 | python LatencyMap.py --min_bucket=4

