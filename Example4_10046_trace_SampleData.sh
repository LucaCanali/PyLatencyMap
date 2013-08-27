#!/bin/bash

# This is an example of PyLatencyMap Luca.Canali@cern.ch Aug 2013
# Display 10046 trace data as a Frequency-Intensity Latency HeatMap
# This example is for db file sequential read: can be used to study commit time latency
# data comes from a trace file (either cat for an existing trace file or tail -f if processing 'live' data

cat SampleData/test_10046_tracefile.trc|python 10046_trace_oracle/10046_connector.py |python LatencyMap.py 

