#!/usr/bin/perl -w

# Copyright (C) 2015, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

# NAME: NetApp_histogram_Cmode.pl
# AUTHOR: Ruben Gaspar
# Date: 29/06/15
# PURPOSE: Script created to provide a histogram of a given junction-path. Output should be fed to NetApp connector. Powered by Luca's https://github.com/LucaCanali/PyLatencyMap

use strict;
use warnings;
use Getopt::Long; 
use Net::OpenSSH;
use Data::Dumper;
 


our($debug, $junctionpath,$user,$password,$clusterip,$histogram,$iteractions, $interval);

sub Setup {
	my ($help, $h);

	$Getopt::Long::ignorecase=0;

	GetOptions('help' => \$help,'h' => \$h, 'debug' => \$debug, 'jp=s' => \$junctionpath, 'user=s' => \$user, 'password=s'=> \$password, 'clustermgmt=s' => \$clusterip , 'histogram=s' => \$histogram, 'iteractions=i' => \$iteractions, 'interval=i' => \$interval ) || die "Please use: $0 -help \n ";

	if (defined $help || defined $h){
		Help();
	}
	if (! defined $clusterip)  {
		Help();
	}
	if (! defined $password) {
		Help();
	}
	if (! defined $user) {
		$user='admin';
	}
	if (! defined $histogram) {
		$histogram='nfs_reads';
	}
	if (! $iteractions)  {
		$iteractions =100;
	}
	if (! $interval) {
		$interval = 1;
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
	print "This command tries to fetch necessary information from a C-mode cluster to retrieve histograms of a given junction-path. It's expected to connect via SSH with a cluster account, defaults to admin.\n"; 
	print "$0: [-help|-h] [-debug] ...  \n";
	print "-jp: junction path. It's mandatory.\n";
	print "-user: if not present defaults to admin.\n";
	print "-password: password. It's mandatory.\n";
	print "-clustermgmt: IP to connect to the C-mode cluster with a cluster account.\n";
	print "-histogram: nfs_reads, nfs_writes,... . It defaults to nfs_reads\n";
	print "-interval: how much time each iteration should be. It defaults to 1 sec.\n";
	print "-iteraction: How many iteractions of a given interval should we do. It defaults to 100\n";
	exit 0;
}


sub RunSSHStr {  
	my($cmd,$str,$user,$passwd,$host,$fake,$text) = @_;
	my $this=(caller(0))[3];
	&LogPrint("$this: begin: cmd: <$cmd> user: <$user> host: <$host> fake: <$fake> ");
	my($rc); 
    	if ($fake) {
		if (defined $text) {
			&LogPrint("$this: would do $text");
		} else {
			&LogPrint("$this: would do $cmd");
		}
  	} else {
		if (defined $text) {
			&LogPrint("$this: running $text");
		} else {
			&LogPrint("$this: running $cmd");
		}
		my($ssh);
		#eval {	
		$ssh = Net::OpenSSH->new("$user\@$host",password => $passwd, strict_mode => 0, master_stdout_discard => 0,ctl_dir => $ENV{HOME}, master_stderr_discard => 1, master_opts => [-o => "UserKnownHostsFile=/dev/null", -o => "StrictHostKeyChecking=no", -o => "ConnectTimeout=30" ]) or die $ssh->error;
		#};
		if (! defined $ssh) {
			&LogPrint("$this: no ssh object!, likely wrong IP" );
			return 0; #error	
		}
		if ($ssh->error) {
			&LogPrint("$this: opening connection: " . $ssh->error);
			undef $ssh;
			return 0;#error
		} elsif ($@) {
			&LogPrint("$this: eval running " . $@);
			undef $ssh;
			return 0;#error
		}
		my($output,$errput)=$ssh->capture2({timeout => 60 },"$cmd"); 
		if ($ssh->error) {
			&LogPrint("$this: running" . $ssh->error);
			return 0;#error
		}
		if (defined $output && length($output) > 0) {
			push @$str,"stdout:\n";	
			push @$str, $output;
		}
		if (defined $errput && length($errput) > 0) {
			push @$str,"stderr:\n";	
			push @$str, $errput;
		}
		undef $ssh;    	
	}
	
	return 1; #ok
}

sub OpenSSHCon {   
	my($user,$passwd,$host) = @_;
	my $this=(caller(0))[3];
 
	&LogPrint("$this: begin: user: <$user> host: <$host>");
    	my($ssh);
	#eval {	
 		$ssh = Net::OpenSSH->new("$user\@$host",password => $passwd, strict_mode => 0,master_stdout_discard => 0,ctl_dir => $ENV{HOME},master_stderr_discard => 1, master_opts => [-o => "UserKnownHostsFile=/dev/null", -o => "StrictHostKeyChecking=no", -o => "ConnectTimeout=30" ]) or die $ssh->error;
	#};
	if (! defined $ssh) {
		&LogPrint("$this: no ssh object!, likely wrong IP" );
		return 0; #error	
	} elsif ($ssh->error) {
		&LogPrint("$this: opening connection: " . $ssh->error);  
		undef $ssh;
		return 0;#error
	} elsif ($@) {
		&LogPrint("$this: eval running " . $@);
		undef $ssh;
		return 0;#error
	}
	return $ssh; #ok   	
} 

sub Main {
	LogPrint("Starting Main");
	local $|=1;
	#retrive data from the cluster $cmd,$str,$user,$passwd,$host,$fake,$text
	my(@output,$cmd,$rc);
	$cmd="vol show -fields volume,node -junction-path $junctionpath";
	$rc = &RunSSHStr($cmd, \@output, $user, $password, $clusterip, 0, $cmd); 
	if ($rc == 0) {
		print "Some error while calling <$cmd>\n";
		print @output;
		exit 1; # error
	} 
	my($stdout,@params,@values,@comodin);
	foreach (@output) {
		if (/stdout:$/) {
			$stdout=1;
			next;
		} 
		if ($stdout) {
			@comodin= split /\n/,$_; 
			last;
		}
	}
	#cleanup
	foreach (@comodin){
		next if (/^\s/);
		next if (/-{1,}/);
		next if (length($_) == 0 );
		my @arr = split /\s/,$_;
		foreach (@arr) {
			chomp $_;
			s/^\s+//;
			push @params,$_ if (/\w+/);
		} 
	} 
	my %pairs;
	if ((scalar(@params) % 2 ) != 0 ) {
		print "A even number of parameters should be retrived from C-mode NetApp cluster.\n";
		print @params;
		exit 1; # error
	}
	
	for (my $i=0;$i<scalar(@params)/2;$i++) {
		$pairs{$params[$i]}=$params[scalar(@params)/2+$i];
	}
	LogPrint("Main: value pairs for the junction-path: ". Dumper \%pairs);	
	my $beautifier;
	#build the command
	for ($histogram) {
		if (/nfs_reads/) {
			$cmd="system node run -node " . $pairs{'node'} . " stats show -r -n $iteractions -i $interval volume:". $pairs{'volume'} . ":nfs_protocol_read_latency";
			$beautifier="NetApp performance counter: volume:" . $pairs{'volume'} . ":nfs_protocol_read_latency";
		}
		if (/nfs_writes/) {
			$cmd="system node run -node " . $pairs{'node'} . " stats show -r -n $iteractions -i $interval volume:". $pairs{'volume'} . ":nfs_protocol_write_latency";
			$beautifier="NetApp performance counter: volume:" . $pairs{'volume'} .  ":nfs_protocol_write_latency";
		}
	}; 
	print "beautifier: $beautifier\n" if defined $beautifier;
	my $ssh=OpenSSHCon($user,$password,$clusterip,0);
	if ($ssh == 0) {
		LogPrint("Main: cant open ssh connection to <$clusterip> using <$user>");
		exit 1; #error
	}
	
	my($rout, $pid) = $ssh->pipe_out($cmd);
	while (my $line = <$rout>) {
		print $line;
      	}
	
 	return;
}



Setup;
Main;
1;
