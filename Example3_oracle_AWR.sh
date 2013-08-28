#!/bin/bash

# This is an example of PyLatencyMap Luca.Canali@cern.ch Aug 2013
# Display Oracle's event histogram historical data from AWR as a Frequency-Intensity Latency HeatMap
# This example is for db file sequential read: can be used to study commit time latency
# 

sqlplus -S / as sysdba @AWR_oracle/awr_latency.sql "db file sequential read" 91 | python LatencyMap.py


