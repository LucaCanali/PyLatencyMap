#!/usr/bin/perl -w

# Copyright (C) 2015, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction. 

# NAME: netapp_latency_connector.pl 
# AUTHOR: Ruben Gaspar
# Date: 15/06/15 
# PURPOSE: Script created to convert NetApp performance histogram output in a format understanded by Luca's https://github.com/LucaCanali/PyLatencyMap

use strict;
use warnings;
use Getopt::Long; 
use POSIX qw(strftime);
our($debug, %buckets, %buckets_time, $ms, $beauty); 

sub Setup {
	my ($help, $h);

	$Getopt::Long::ignorecase=0;

	GetOptions('help' => \$help,'h' => \$h, 'debug' => \$debug, 'ms' => \$ms, ) || die "Please use: $0 -help \n ";

	if (defined $help || defined $h){
		Help();
	}
	return;
}

sub LogPrint {
   	my($sentence) = @_;
   	if ($main::debug) {	
   		my($date)=`date`;
   		chop($date);
   
		printf "%-30s: $sentence\n",$date;
   	}
	return;
}

sub Help {  
	print "Connector to be used as filter for NetApp latency output. Defaults works on microseconds. It can be changed to millisecs. \n";
	print "$0 [-ms]\n";
	return;
}
sub ConvertMs {
	my($value)=@_;

	if ($value =~ /(\d+)us/) {
		return $1/1000;
	} elsif ($value =~ /(\d+)ms/) {  
		return $1;
	} elsif ($value =~ /(\d+)s/) {
		return $1 * 1000;
	}
	return;	
}

sub ConvertUs { 
	my($value)=@_;

	if ($value =~ /(\d+)us/) {
		return $1;
	} elsif ($value =~ /(\d+)ms/) {  
		return $1*1000;
	} elsif ($value =~ /(\d+)s/) {
		return $1 * 1000000;
	}
	return;	


} 
sub WhichBucket {
	my($interval,$oracle) = @_;
	#remove out-layers
	#too small
	if ($interval < $oracle->[0]) {
		return $oracle->[0];
	}
	#too big
	if ($interval > $oracle->[scalar(@$oracle)-1]) {
		LogPrint("$interval is bigger than " . $oracle->[scalar(@$oracle)-1] ); # for now it's not assigned
		return;
	}
	for(my $i=0; $i < scalar(@$oracle);$i++) {
		if ($interval > $oracle->[$i] && ((scalar(@$oracle)-1) - $i) > 0) {
			next;
		} else {
			return $oracle->[$i] ;
		}	 
	}
	return;
}
sub PrintRecord {
	
	print "<begin record>\n";
	#my $dt = DateTime->now;
	#my $usecs = ($dt->hour * 3600 + $dt->minute * 60 + $dt->second) * 1000000;
	#my $timestr = dt.strftime('%d-%b-%y %l.%M.%S %p%z');

	my $secs = time;
       my $timestr = strftime("%d-%b-%y %l.%M.%S %p%z",localtime($secs));
	my $usecs = $secs * 1000000; 

	print "timestamp, microsec, $usecs, $timestr\n";
	print "label,$beauty\n";
	if ($ms) {
		print "latencyunit, millisec\n";
	} else {
		print "latencyunit, microsec\n";
	}
	print "datasource, oracle\n";

	foreach my $key ( sort { $a <=> $b } keys %buckets ) {
		print "$key, $buckets{$key}\n";
	}
	print "<end record>\n";
	return;
}
sub Main {
	LogPrint("Starting Main");
	local $|=1; 
	my @netapp_histogram = qw/20us 40us 60us 80us 100us 200us 400us 600us 800us 1ms 2ms 4ms 6ms 8ms 10ms 12ms 14ms 16ms 18ms 20ms 40ms 60ms 80ms 100ms 200ms 400ms 600ms 800ms 1s 2s 4s 6s 8s 10s 20s 30s 60s 90s 120s 120s/;
	my @oracle_histogram_ms = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096); #all values in millisecs
	my @oracle_histogram_us = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304); # all values in microsecs
	my @oracle_histogram;
	$beauty="NetApp histogram based on counters";

	if ($ms) {
		@oracle_histogram = @oracle_histogram_ms;
	} else {
		@oracle_histogram = @oracle_histogram_us; 
	}
	#initialise buckets
	foreach (@oracle_histogram) {
		$buckets{$_}=0;
	}
 
	my $done=0;
	while (<>) {
		LogPrint("line: $_\n");
		if (!defined($_) || length($_) < 3) {
			next;
		}
		if (!$done && /^beautifier: (.*)$/) {
			$beauty=$1;
			chomp $beauty;
			$done=1;
			next;
		}
		my @arr=split /:/,$_;
		my ($time,$value,$islast);
		$time=$arr[2]; #needs to be assigned to an oracle bucket 
		if ($time =~ /\.\>(\w+)/) {
			$islast=1;
			$time=$1;
		}  
		if ($ms) {
			$time=ConvertMs($time); 
		} else {
			$time=ConvertUs($time);
		}
		$value=$arr[3]; #an integer
		chomp $value;
		LogPrint("time: $time & value: $value");
		my $bucket = WhichBucket($time,\@oracle_histogram);
		if (defined $bucket) {
			$buckets{$bucket} += $value;
		}
		if ($islast) { 
			PrintRecord;
			$islast=0;
		}
	} 
	return;
}

Setup;
Main;
1;