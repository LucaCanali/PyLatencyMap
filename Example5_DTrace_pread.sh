#!/bin/bash

# This is an example of PyLatencyMap Luca.Canali@cern.ch Aug 2013
# Collect and display DTrace data for the pread and pread64 calls as a Frequency-Intensity Latency HeatMap
# This can be used to investigate single-block read latency (see also Oracle's db file sequential read tracing)
# Note this scripts requires to have DTrace installed 
# (see also http://externaltable.blogspot.com/2013/06/dtrace-explorations-of-oracle-wait.html)

dtrace -s DTrace/pread_tracedata.d |python DTrace/dtrace_connector.py |python LatencyMap.py

