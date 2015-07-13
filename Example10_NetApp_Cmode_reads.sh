#!/bin/bash

# This is an example launcher script for PyLatencyMap and its integration with NetApp Cmode instrumentation
# The source python script connects to NetApp storage C-modei (OnTap version 8) and collects the latency histogram
# this is then piped into netapp_latency_connector.pl that converts NetApp histogram format into a power-of-two 
# latency histogram (with the same format as Oracle v$event_histogram)
# LatencyMap.py displays data as Frequency-Intensity heatmaps
#
# This script is intended to be used to measure the latency drilldown of nfs read operations for NetApp C-mode
#
# Notes:
#   - this script requires perl and some additional perl modules (see also README)
#   - configure the connection details here below before running       

PASS=Changeme2015
JUNCTION_PATH=/u01/app/oracle/oradata
CLUSTER_MANAGEMENT_NODE=mynas-cluster-mgmt
INTERVAL=3

perl NetApp_Cmode/NetApp_histogram_Cmode.pl -jp $JUNCTION_PATH -password $PASS -clustermgmt $CLUSTER_MANAGEMENT_NODE -histogram nfs_reads -iteraction 1000 -interval $INTERVAL| perl NetApp_Cmode/NetApp_latency_connector.pl | python LatencyMap.py

