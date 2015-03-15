#!/bin/bash

# This is an example launcher script for PyLatencyMap 
# The sqlplus script outputs data from gv$event_histogram_micro for the wait event db file sequential read
# this script only works with Oracle 12.1.0.2 (or higher) 
# LatencyMap.py displays data as Frequency-Intensity heatmaps
# This script is intended to be used to measure the latency drilldown for IOPS of single-block random read in Oracle
# 

sqlplus -S / as sysdba @Event_histograms_oracle/ora_latency_12c_micro.sql "db file sequential read" 3 | python LatencyMap.py


