#!/bin/bash

# This is an example PyLatencyMap Luca.Canali@cern.ch Aug 2013
# Display the Oracle's event histogram data db file sequential read wait events as 
# a Frequency-Intensity Latency HeatMap
# Can be used to study single-block random read access  
# 

sqlplus -S / as sysdba @event_histograms_oracle/ora_latency.sql "db file sequential read" 3 | python LatencyMap.py


