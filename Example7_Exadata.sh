#!/bin/bash

# This is an example launcher script for PyLatencyMap 
# The sqlplus script outputs data from v$event_histogram for the wait event cell single block physical read
# This is a wait event for Exadata storage.
# LatencyMap.py displays data as Frequency-Intensity heatmaps
# This script is intended to be used to study single-block random read latency and iops for Exadata  
# 

sqlplus -S / as sysdba @Event_histograms_oracle/ora_latency.sql "cell single block physical read" 3 | python LatencyMap.py

