#!/usr/bin/python
# @lint-avoid-python-3-compatibility-imports
#
# pylatencymap-biolatency.py 
# Summarize block device I/O latency as a histogram.
# Modified and integrated with PyLatencyMap for heatmap visualization
# For Linux, uses BCC, eBPF.
#
# USAGE: pylatencymap-biolatency.py [-h] [-T] [-Q] [-m] [-D] [interval] [count]
#
# biolatency is Copyright (c) 2015 Brendan Gregg.
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 20-Sep-2015   Brendan Gregg   Created biolatency
# May 2016      Luca Canali     Added integration to PyLatencyMap and
#                               remaed the script to pylatencymap-biolatency.py  
# 

from __future__ import print_function
from bcc import BPF
from time import sleep, strftime, time
import argparse

# arguments
examples = """examples:
    ./biolatency            # summarize block I/O latency as a histogram
    ./biolatency 1 10       # print 1 second summaries, 10 times
    ./biolatency -mT 1      # 1s summaries, milliseconds, and timestamps
    ./biolatency -Q         # include OS queued time in I/O time
    ./biolatency -D         # show each disk device separately
"""
parser = argparse.ArgumentParser(
    description="Summarize block device I/O latency as a histogram for PyLatencyMap",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("-T", "--timestamp", action="store_true",
    help="include timestamp on output")
parser.add_argument("-Q", "--queued", action="store_true",
    help="include OS queued time in I/O time")
parser.add_argument("-m", "--milliseconds", action="store_true",
    help="millisecond histogram")
parser.add_argument("-D", "--disks", action="store_true",
    help="print a histogram per disk device")
parser.add_argument("interval", nargs="?", default=99999999,
    help="output interval, in seconds")
parser.add_argument("count", nargs="?", default=99999999,
    help="number of outputs")
args = parser.parse_args()
countdown = int(args.count)
debug = 0

# define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

typedef struct disk_key {
    char disk[DISK_NAME_LEN];
    u64 slot;
} disk_key_t;
BPF_HASH(start, struct request *);
STORAGE

// time block I/O
int trace_req_start(struct pt_regs *ctx, struct request *req)
{
    u64 ts = bpf_ktime_get_ns();
    start.update(&req, &ts);
    return 0;
}

// output
int trace_req_completion(struct pt_regs *ctx, struct request *req)
{
    u64 *tsp, delta;

    // fetch timestamp and calculate delta
    tsp = start.lookup(&req);
    if (tsp == 0) {
        return 0;   // missed issue
    }
    delta = bpf_ktime_get_ns() - *tsp;
    FACTOR

    // store as histogram
    STORE

    start.delete(&req);
    return 0;
}
"""

# code substitutions
if args.milliseconds:
    bpf_text = bpf_text.replace('FACTOR', 'delta /= 1000000;')
    label = "msecs"
else:
    bpf_text = bpf_text.replace('FACTOR', 'delta /= 1000;')
    label = "usecs"
if args.disks:
    bpf_text = bpf_text.replace('STORAGE',
        'BPF_HISTOGRAM(dist, disk_key_t);')
    bpf_text = bpf_text.replace('STORE',
        'disk_key_t key = {.slot = bpf_log2l(delta)}; ' +
        'bpf_probe_read(&key.disk, sizeof(key.disk), ' +
        'req->rq_disk->disk_name); dist.increment(key);')
else:
    bpf_text = bpf_text.replace('STORAGE', 'BPF_HISTOGRAM(dist);')
    bpf_text = bpf_text.replace('STORE',
        'dist.increment(bpf_log2l(delta));')
if debug:
    print(bpf_text)

# load BPF program
b = BPF(text=bpf_text)
if args.queued:
    b.attach_kprobe(event="blk_account_io_start", fn_name="trace_req_start")
else:
    b.attach_kprobe(event="blk_start_request", fn_name="trace_req_start")
    b.attach_kprobe(event="blk_mq_start_request", fn_name="trace_req_start")
b.attach_kprobe(event="blk_account_io_completion",
    fn_name="trace_req_completion")

# print("Tracing block device I/O... Hit Ctrl-C to end.")

# output
exiting = 0 if args.interval else 1
dist = b.get_table("dist")
while (1):
    try:
        sleep(int(args.interval))
    except KeyboardInterrupt:
        exiting = 1

    print()
    print("<begin record>")
    if args.timestamp:
        print("timestamp, microsec,", int(time()*1000000),",", strftime("%c"))

    print("label, Latency of block I/O requests measured with BPF/bcc")
    print("latencyunit, microsec")
    
    # this means that the bucket value in the output is the lower end of the interval as for Systemtap histograms
    print("datasource, systemtap")    
    
    # print histogram in the a format required by pylatencymap: "bucket,val"
    # zero vals can be omitted  
    for k, v in dist.items():
        if v.value <> 0:
            print ( (1 << k.value-1), ",", v.value )

    # commentted out as pylatencymap requires comulative values 
    # dist.clear()

    print("<end record>")

    # replaced the original bcc print log histogram with custom code
    # uncomment, if needed for debug purposes
    # dist.print_log2_hist(label, "disk")

    countdown -= 1
    if exiting or countdown == 0:
        exit()

