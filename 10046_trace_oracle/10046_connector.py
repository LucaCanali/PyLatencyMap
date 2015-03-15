#!/usr/bin/python

# 10046_connector.py
# this is part of the PyLatencyMap package, Luca.Canali@cern.ch Aug 2013
# Input: Oracle 10046 trace (sql trace) 
# Output: histogram record data in a format to be processes by LatencyMap.py for 
#         visualization as Frequency-Intensity HeatMap
#
# Usage:
#        cat $DIAG_DIG/mytrace.trc|python 10046_connector.py
#        alternative: tail -100f $DIAG_DIG/mytrace.trc|python 10046_connector.py
#

import sys
import math
import time

event_filter='db file sequential read'
sample_interval=3000000   # 3 sec


class LatencyHistogram:
    def __init__(self):
        self.histogram = {}

    def add_datapoint(self,value):

        bucket = int(math.log(value,2)) + 1 # the +1 is added to uniform to the use of Oracle event_histograms
                                            # for example SystemTap and Dtrace will just use log(value,2)
        self.histogram[bucket] =  self.histogram.get(bucket, 0) + 1      

    def print_histogram(self,print_time):

        print '<begin record>'
        for bucket in self.histogram:
            print str(2**bucket) + ',' + str(self.histogram[bucket])
        print 'timestamp,microsec,' + str(print_time) + ', ' + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(print_time/1000000))
        print 'label, 10046 trace data for event: ' + event_filter
        print 'latencyunit, microsec'
        print 'datasource, oracle'   # we have chosen the Oracle conventions for bucket assignment, see bucket calculation above
        print '<end record>'
        sys.stdout.flush()

def value_from_key(line, field_key):
    begin_field = line.find(field_key) + len(field_key)
    field_length = line[begin_field:].find(' ')
    if field_length == -1:
        field_value = line[begin_field:]
    else:
        field_value = line[begin_field:begin_field+field_length]
    return(field_value)


def main():

    myhistogram = LatencyHistogram()
    current_time = 0

    while True:
        line = sys.stdin.readline()
        if not line:                        # reached EOF, exit
            sys.exit(0)
        line = line.strip()          
        if line == '':
            continue
        if not line.startswith('WAIT #'):   # only process trace lines with wait event details
            continue
        if event_filter not in line:        # only process trace lines for the event_filter wait event
            continue
 
        ela,tim = int(value_from_key(line, 'ela= ')), int(value_from_key(line, 'tim='))
        sample_time = tim - tim % sample_interval
        myhistogram.add_datapoint(ela)

        if sample_time > current_time:
            try:
                myhistogram.print_histogram(current_time)
            except:
                sys.exit(1)   # cannot print to stdout most likely a broken pipe towards LatencyMap.py
            current_time = sample_time
        elif sample_time < current_time:
            raise Exception('Found data with timestamp higher than already processed data. Cannot handle this')

if __name__ == '__main__':
    sys.exit(main())


