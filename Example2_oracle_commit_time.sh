#!/bin/bash

# This is an example PyLatencyMap Luca.Canali@cern.ch Aug 2013
# Display the Oracle's event histogram data log file sync wait events as 
# a Frequency-Intensity Latency HeatMap
# Can be used to study commit time latency
# 

sqlplus -S / as sysdba @event_histograms_oracle/ora_latency.sql "log file sync" 3 | python LatencyMap.py


