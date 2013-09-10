#!/usr/bin/python

# LatencyMap.py v1.0b Sep 2013, by Luca.Canali@cern.ch
# This is a tool to assist in performance investigations of latency data.
# Input: latency data histograms in a custom format
# Output: colored Latency Heatmaps. A frequency heatmap (IOPS) and an intensity heatmap (wait time)
# See README for more info and also http://externaltable.blogspot.com
#
# Usage: data_source|<optional connector script> | python LatencyMap.py <options>
# Help: python LatencyMap.py -h
#

import sys
import getopt
import math
import time

class GlobalParameters:
    def __init__(self):
        self.num_latency_records = 90  # size of the graph in the x directionm, i.e. num of time intervals displayed
        self.min_latency_bkt = -1   # lower latency bucket value, -1 means autotune 
        self.max_latency_bkt = 64   # highest latency bucket value, 64 means autotune 
        self.frequency_maxval = -1  # -1 means auto tuning of max value, otherwise put here a fixed number
        self.intensity_maxval = -1  # -1 means auto tuning of max value, otherwise put here a fixed number
        self.debug_level = 0        # 5 is max debug level
        self.print_legend = True    # set to False to turn off printing this part of the graph
        self.frequency_map = True   # set to False to turn off printing this part of the graph
        self.intensity_map = True   # set to False to turn off printing this part of the graph
        self.screen_delay = 0.1     # in seconds delay between screens, useful to slow down when working from trace files
        self.latency_unit = 'millisec'  # default is milliseconds, can be overwritten by latencyunit_tag data
        self.begin_tag = '<begin record>'
        self.end_tag = '<end record>'
        self.latencyunit_tag = 'latencyunit'
        self.label_tag = 'label'

    def get_options(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hn:d:",["num_records=","min_bucket=","max_bucket=",
                         "latency_unit=","frequency_maxval=","intensity_maxval=","screen_delay=",
                         "debug_level=","help"])
        except getopt.GetoptError, err:
            print err
            sys.exit(1)
        for opt, arg in opts:
            if opt in ('-h', '--help'): 
                # self.usage()  no need as usage is printed by default
                sys.exit(1)
            if opt in ('-d', '--debug_level'): 
                self.debug_level = int(arg)
            if opt in('-n', '--num_records'): 
                self.num_latency_records =int(arg)
            if opt == '--min_bucket': 
                self.min_latency_bkt = int(arg)
            if opt == '--max_bucket': 
                self.max_latency_bkt = int(arg) + 1
            if opt == '--frequency_maxval': 
                self.frequency_maxval = 1.2 * int(arg) # maxval becomes the base for the highest bucket 
            if opt == '--intensity_maxval': 
                self.intensity_maxval = 1.2 * int(arg) # maxval becomes the base for the highest bucket 
            if opt == '--screen_delay': 
                self.screen_delay = float(arg)

 
    def usage(self):
        print 'LatencyMap.py v1.0b Sep 2013, by Luca.Canali@cern.ch'
        print 'This is a tool to assist in performance investigations of latency data'
        print 'Input: latency data histograms in a custom format'
        print 'Output: Latency Heatmaps, Frequency heat map (IOPS study) and an intensity heat map (wait time)'
        print 'See README for more info and see also http://externaltable.blogspot.com'
        print
        print 'Usage: data_source| <optional connector script> | python LatencyMap.py <options>'
        print  
        print 'Options are:'
        print '--num_records=arg      : number of time intervals displayed, default is 90'
        print '--min_bucket=arg       : the lower latency bucket value is 2^arg, default is -1 (autotune)'
        print '--max_bucket=arg       : the highest latency bucket value is 2^arg, , default is 64 (autotune)'
        print '--frequency_maxval=arg : default is -1 (autotune)'
        print '--intensity_maxval=arg : default is -1 (autotune)'
        print '--screen_delay=arg     : used to add time delay when replaying trace files, default is 0.1 (sec)'
        print '--debug_level=arg      : debug level, default is 0, 5 is max debug level'



# this is the base class used to collect and store latency data, see also ArrayOfLatencyRecords
class LatencyRecord:
    def __init__(self):
        self.data = {} 
        self.frequency_histogram = [0 for x in range(0, g_params.max_latency_bkt + 1)]
        self.intensity_histogram = [0 for x in range(0, g_params.max_latency_bkt + 1)]
        self.delta_time = 0
        self.max_frequency = 0
        self.sum_frequency = 0
        self.max_intensity = 0
        self.sum_intensity = 0
        self.date = ''
        self.label = ''

    def print_record_debug(self):
        print '\nLatest data record:' 
        print self.data

    def get_new_line(self):
        while True:
           line = sys.stdin.readline()
           if not line:
                print "\nReached EOF from data source, exiting."
                sys.exit(0)
           if line.strip() <> '':
               return(line.lower().strip())    # return the line read from stdin, lowercase, strip 

    def go_to_begin_record_tag(self):
        while True:
            line = self.get_new_line() 
            if line == g_params.begin_tag:        
                return            # found the begin data tag, so return   

    def read_record(self):
        while True:
            line = self.get_new_line()
            split_line = line.split(',')                                     # split input into csv elements

            if len(split_line) == 1 and split_line[0].strip() == g_params.end_tag:
                return(0)                                                    # exit read_record, clean condition

            if len(split_line) == 4 and split_line[0].strip() == 'timestamp' and split_line[1].strip() == 'musec':
                self.data['timestamp'] = int(split_line[2].strip())     # timestamp in numeric form
                self.date = split_line[3].strip()                       # timestamp in human-readable format
                continue        # move to process next line                

            if len(split_line) == 2 and split_line[0].strip() == g_params.label_tag:
                self.label = split_line[1].strip()                       # optional label
                continue       # move to process next line          

            if len(split_line) == 2 and split_line[0].strip() == g_params.latencyunit_tag:
                latency_unit = split_line[1].strip()                     # latency unit (millisec, microsec, nanosec)
                if latency_unit not in ('millisec', 'microsec', 'nanosec'):
                    raise Exception('Cannot understand latency unit: '+ line) 
                else:
                    g_params.latency_unit = latency_unit
                continue       # move to process next line          

            if len(split_line) <> 2:          
                raise Exception('Cannot process record: '+ line)             # raise error condition

            # main record processing of latency data
            try:
                bucket = int(split_line[0].strip())
                value  = int(split_line[1].strip())
                bucket = math.log(bucket,2)    # we expect bucket values that are powers of 2
            except:
                    raise Exception('Cannot understand data: '+ line)        # raise error condition  

            if abs(int(bucket) - bucket) > 1e-6:                             # account for log computation errors
                raise Exception('Bucket value must be power of 2: '+ line)   # raise error condition  
            bucket = int(bucket)

            self.data[bucket] = self.data.get(bucket, 0) + value             # add new data point 

    def autotune_latency_buckets(self):
        if g_params.min_latency_bkt == -1:    # this computes values for autotune mode
             g_params.min_latency_bkt= {'millisec':0, 'microsec':8, 'nanosec':18}[g_params.latency_unit]

        if g_params.max_latency_bkt == 64:    # this computes values for autotune mode
            g_params.max_latency_bkt = g_params.min_latency_bkt + 11

    def compute_deltas(self, previous_record):

        # compute timestamp deltas if data available, otherwise it will be 0
        self.delta_time = self.data.get('timestamp',0) - previous_record.data.get('timestamp',0)
        if self.delta_time > 0:
            time_factor = self.delta_time / 1e6           # timestamps are in ms, need to convert to sec
        else:
            time_factor = 1                               # cover the case where timestamps are not used
        for bucket in self.data:
            if bucket == 'timestamp':
                continue                                  # this is a special value, the following does not apply
            write_bucket = bucket                         # default  for write_bucket = data.bucket 
            if bucket > g_params.max_latency_bkt:             
                write_bucket = g_params.max_latency_bkt   # catchall bucket for high values
            if bucket < g_params.min_latency_bkt:    
                write_bucket = g_params.min_latency_bkt   # collapse low latency values into lower bucket

            # compute the frequency array 
            delta_count = self.data.get(bucket,0) - previous_record.data.get(bucket,0)
            self.frequency_histogram[write_bucket] += delta_count / time_factor


            # compute the intensity array 
            # this approximate the time waited in a given bucket as 0.75 of latency bucket value * number of waits
            self.intensity_histogram[write_bucket] += (0.75 * 2**bucket * delta_count) / time_factor

        self.max_frequency = max(self.frequency_histogram)
        self.sum_frequency = sum(self.frequency_histogram)
        self.max_intensity = max(self.intensity_histogram)
        self.sum_intensity = sum(self.intensity_histogram)


class ArrayOfLatencyRecords:
    def __init__(self):
        zero_record = LatencyRecord()
        self.sample_number = 0 
        self.data = [zero_record for x in range(0, g_params.num_latency_records + 1)] 
        self.asciiescape_backtonormal = chr(27) + '[0m'

    def print_frequency_histograms_debug(self):
        print '\nFrequency histograms:'
        for record in self.data:
            print record.frequency_histogram, record.delta_time

    def print_intensity_histograms_debug(self):
        print '\nIntensity histograms:'
        for record in self.data:
            print record.intensity_histogram, record.delta_time

    def add_new_record(self, record):
        self.data = self.data[1:len(self.data)]
        self.data.append(record)
        self.sample_number += 1

    def asciiescape_color(self, token, palette):
        blue_palette = {0:15, 1:51, 2:45, 3:39, 4:33, 5:27, 6:21}        # shades of blue: white-light blue-dark blue
        red_palette  = {0:15, 1:226, 2:220, 3:214, 4:208, 5:202, 6:196}  # white-yellow-red palette
        if palette == 'blue':
            color_asciival = blue_palette[token]
        elif palette == 'red':
            color_asciival = red_palette[token]
        else:
            raise Exception('Wrong or missing palette name.')
            exit(1)
        return(chr(27) + '[48;5;' + str(color_asciival) + 'm')

    def bucket_to_string_with_suffix(self, bucket):
        if int(bucket/10) > 4:
            raise Exception('Cannot handle the number')   
        suffix = {0:'', 1:'k', 2:'m', 3:'g', 4:'t'}[int(bucket/10)]
        bucket_normalized = bucket % 10
        return( str(2**bucket_normalized) + suffix )

    def value_to_string(self,value):
        if value < 0:
            raise Exception('Cannot handle negative numbers') 
        elif value <= 9: 
            mystring = "%.1g" % value          # one decimal digit for numbers less than 10
        elif value < 1000000:
            mystring = str(int(round(value)))  # integer value, 6 digits
        else:
            mystring = "%.2g" % value          # exponential notation for numbers >=1e6
        return(mystring)

    def print_header(self):
        line = ''
        if g_params.debug_level < 2:
            line += chr(27) + '[0m' + chr(27) + '[2J' + chr(27) + '[H'   # clear screen and move cursor to top line
        line += 'LatencyMap.py v1.0b - Luca.Canali@cern.ch'
        print line

    def print_footer(self):
        record = self.data[len(self.data)-1]
        line = 'Sample num: ' + str(self.sample_number) 
        line += ', Delta time (sec): '                              # note timestamp is in musec, convert to second
        line += str(round(record.delta_time/1e6,1))     
        line += ', Date: ' + record.date.upper()
        print line
        if record.label <> '':
            print 'Label: ' + record.label

    def print_heat_map(self, type):                                 # type can be 'Frequency' or 'Intensity'

        if type == 'Frequency':
            params_maxval = g_params.frequency_maxval
            params_color = 'blue'
            chart_maxval = max([record.max_frequency for record in self.data]) 
            chart_title = 'Frequency Heatmap: operations per sec'
            unit = '(N#/sec)'
        elif type == 'Intensity':
            params_maxval = g_params.intensity_maxval
            params_color = 'red'
            chart_maxval = max([record.max_intensity for record in self.data]) 
            chart_title = 'Intensity Heatmap: time waited per sec'
            unit= '(' + g_params.latency_unit + '/sec)'

        # graph header
        line = '\nLatency bucket'
        line = line.ljust(g_params.num_latency_records/2 - 10)
        line += chart_title 
        line = line.ljust(g_params.num_latency_records + 2)
        line += 'Latest values'
        if g_params.print_legend:
            line += '    Legend'
        print line 
        line = '(' + g_params.latency_unit + ')'   
        line = line.ljust(g_params.num_latency_records - len(unit) + 14)
        line += unit 
        print line 

        # main part of the graph
        if params_maxval == -1:
            max_val = chart_maxval                                  # this is the auto tuning case
        else:
            max_val = params_maxval                                 # this is the manual setting case

        line_num = -1
        for bucket in range(g_params.max_latency_bkt, g_params.min_latency_bkt - 1, -1):

            line_num += 1
            # print scale values on the left of the graph
            if bucket == g_params.max_latency_bkt:           
                line = '>' + self.bucket_to_string_with_suffix(bucket - 1)
            elif bucket == g_params.min_latency_bkt:
                line = '<' + self.bucket_to_string_with_suffix(bucket)
            else:
                line = self.bucket_to_string_with_suffix(bucket)
            line = line.rjust(5,' ') + ' '
             
            # print heat map with colors
            for record in self.data:
                if type == 'Frequency':
                   data_point = record.frequency_histogram[bucket]
                elif type == 'Intensity':
                   data_point = record.intensity_histogram[bucket]
                if  data_point == 0:                                  # value 0 goes to token 0 (white)
                    token = 0
                elif data_point >= max_val:         # max val and above (if in manual max mode) go to token 6
                    token = 6
                else:
                    token = int(data_point*6/max_val) + 1   # normalize to range 1..6

                if g_params.debug_level >= 2:
                   line += str(token) + ':' + str(data_point) + ', '            # debug code
                else:
                   line += self.asciiescape_color(token, params_color) + ' '    # add a colored point in the graph

            # print values of latest point on the right side of the graph
            line += self.asciiescape_backtonormal

            line += self.value_to_string(data_point).rjust(7,'.')

            # print legend 
            if g_params.print_legend:        # do not print legend if print_legend is false
                if line_num <= 6:            # use line_num as guide 
                    line += '    ' + self.asciiescape_color(line_num, params_color) 
                    line += ' ' + self.asciiescape_backtonormal + ' '
                    display_val = int(max_val * (line_num-1) / 6)  
                    if line_num == 0:
                        line += '0'
                    else:
                        line += '>' + self.value_to_string(display_val)
                elif line_num == 7:
                    line += '    ' + 'Max: ' + self.value_to_string(chart_maxval)
                elif line_num == (g_params.max_latency_bkt-g_params.min_latency_bkt):  #last line of the heatmap
                    line += '    ' + 'Max(Sum):'
            print line 

        # trailing part of the graph
        line = '      ' 
        if type == 'Frequency':
            line += 'Number of latency operations per second: x=time, y=latency bucket'
            line = line.ljust(g_params.num_latency_records + 3)
            line += 'Sum:' + self.value_to_string(record.sum_frequency).rjust(7,'.')
            line += '    ' + self.value_to_string(max([record.sum_frequency for record in self.data])) 
        elif type == 'Intensity':
            line += 'Wait time over elapsed time: x=time, y=latency bucket'
            line = line.ljust(g_params.num_latency_records + 3)
            line += 'Sum:' + self.value_to_string(record.sum_intensity).rjust(7,'.')
            line += '    ' + self.value_to_string(max([record.sum_intensity for record in self.data]))
        print line + '\n'

def main():
    my_chart_data = ArrayOfLatencyRecords()
    I_am_first_record = True

    while True:
        myrecord = LatencyRecord()               # new empty record object
        myrecord.go_to_begin_record_tag()        # read and discard everything till the <begin data> tag
        try:
            myrecord.read_record()               # read record values
        except Exception, err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            return 1
        if g_params.debug_level >= 2:
            myrecord.print_record_debug()
        if I_am_first_record:
            myrecord.autotune_latency_buckets()        # check if latency buckets min and max need autotune
            I_am_first_record = False                  # no delta values computed for the first record
        else:
            myrecord.compute_deltas(previous_record)   # compute delta values of metrics
        my_chart_data.add_new_record(myrecord)         # add the record object to the historical array 
        previous_record = myrecord     # make a copy of the record used to compute deltas at the next iteration

        my_chart_data.print_header()
        if g_params.frequency_map:
            my_chart_data.print_heat_map('Frequency')
        if g_params.intensity_map:
            my_chart_data.print_heat_map('Intensity')
        my_chart_data.print_footer()
        time.sleep(g_params.screen_delay)             # delay useful when replaying historical data and/or trace files

        if g_params.debug_level >= 3:
            my_chart_data.print_frequency_histograms_debug()
        if g_params.debug_level >= 4:
            my_chart_data.print_intensity_histograms_debug()


if __name__ == '__main__':
    g_params = GlobalParameters()
    g_params.usage()
    g_params.get_options()
    sys.exit(main())

