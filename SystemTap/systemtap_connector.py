#!/usr/bin/python

# systemtap_connector.py
# this is part of the PyLatencyMap package, Luca.Canali@cern.ch Aug 2013
# Input: dtrace data in PyLatencyMap format, for example from pread_tracedata.d script 
# Output: histogram record data in a format to be processes by LatencyMap.py for 
#         visualization as Frequency-Intensity HeatMap
#
# Usage:
#        stap -v SystemTap/blockio_rq_latency.stp |python SystemTap/systemtap_connector.py |python LatencyMap.py
#

import sys

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            print "\nReached EOF from data source, exiting."
            sys.exit(0)
        if line.strip() == '':
            continue
        line = line.strip()

        if line.startswith('<begin record>'):
            print('<begin record>')
            continue
        if line.startswith('<end record>'):
            print('<end record>')
            sys.stdout.flush()
            continue
        if line.startswith('timestamp'):
            print(line)
            continue
        if line.startswith('datasource'):
            print(line)
            continue
        if line.startswith('label'):
            print(line)
            continue
        if 'value' in line:
            continue
        if 'myhistogram' in line:
            continue

        line = line.replace(' ','')
        line = line.replace('@','')
        line = line.replace('|',',')

        if line.startswith('~'):   # Systemtap @hist_log may use ~ to represnet a set of blank lines 
            continue

        if (line.startswith('-') or line.startswith('0,')) : # filters out points of zero and negative latency,  
            continue               # this is a workaround in particular for SYstemTap and DTrace on Virtualbox
                                   # to be further investigated if something better can be done on this
        
        print(line)   # if we made it throughh all the filters above, print the line to stdout                      

if __name__ == '__main__':
    sys.exit(main())

