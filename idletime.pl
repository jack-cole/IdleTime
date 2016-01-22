#!/usr/bin/perl
#	 ___    _ _       _____ _               
#	|_ _|__| | |___  |_   _(_)_ __  ___ _ _ 
#	 | |/ _` | / -_)   | | | | '  \/ -_| '_|
#	|___\__,_|_\___|   |_| |_|_|_|_\___|_|  
#	v1.1 [2016-01-22]
#	by Jack the Smack                                      
#	Old Discussion Thread: http://forum.teamspeak.com/showthread.php/101272-Perl-Idle-Timer-Display-how-long-they-ve-been-AFK-without-moving-or-kicking-them
#	Github: https://github.com/jackthesmack/IdleTime
#	Contact: idle_timer@jack-cole.com

#	How to use: 
#		Configure all the settings in idletime.cfg, then run this:
#			perl "...\idletime.pl"
#		in terminal, or download Perl for Windows by using your google foo. 

##		----------------------------		##
##		Ignore everything below here		##
##		...or not.							##
##		I'm a comment, not your mother.		##
##		----------------------------		##

use strict; use warnings;
use Data::Dumper qw(Dumper);
use File::Basename;
use Cwd 'abs_path';
use Time::HiRes qw (usleep);
no warnings "experimental::autoderef";

#Defaults
my %cfg = (
	"host" => 'localhost',
	"port" => '10011',
	"username" => "serverQuery",
	"password" => "xxx",
	"sid" => 1,
	"minidleminutes" => 25,
	"labelhours" => " Hr",
	"labelminutes" => " Min",
	"labelseconds" => " Sec",
	"labelplural" => 1,
	"idletitle" => " Idle",
	"idlenickname" => "Idle Timer",
	"shortenedtime" => 0,
	"secondsenabled" => 0,
	"serversortid" => 91115,
	"updatetime" => 5,
	"testing" => 0,
	"slowdown" => 0
);


#CFG File
my $cfgfilename = dirname(abs_path($0))."/";
$cfgfilename .= 'idletime.cfg';
if (open(my $fh, $cfgfilename)) {
  while (my $row = <$fh>) {
	chomp $row;
	$row =~ s/[^\\]\#[^\n]+//g;
	if($row =~ /[^\n]+=[^\n]+/){
		my @row = split(/\=/, $row);
		next if(@row != 2);
		$row[0] = trim($row[0]);$row[1] = trim($row[1]);
		$row[0] = lc($row[0]);
		$row[1] = ($row[1] =~ /[\"\']([^\n]+)[\"\']/)[0] if($row[1] =~ /[\"\'][^\n]+[\"\']/);
		$cfg{$row[0]} = $row[1];
		
	};
  };
}else{
	warn "Could not open file '$cfgfilename' $!\n";
};


#Command Line Arguments
foreach (@ARGV){
	my ($Key) = $_ =~ /([^ ]+)=[^ ]+/;
	my ($Value) = $_ =~ /[^ ]+=([^\n]+)/;
	$Key = lc($Key);
	$cfg{$Key} = $Value;
};


$cfg{"idlenickname"}  =~ s/ /\\s/g;

print "Connecting to server\n";
my $buf = '';
use IO::Socket; 
my $sock = new IO::Socket::INET (
	PeerAddr => $cfg{"host"}
	,PeerPort => $cfg{"port"}
	,Proto => 'tcp'
	,Autoflush   => 1
	,Blocking    => 1
	,Timeout    => 10
	); 
die "Could not connect to Server: $!\n" unless $sock;



sub ExecuteCommand{ # ExecuteCommand( command [string], return error [boolean] )
	$_[1] = 0 if(!defined($_[1]));
	print $sock $_[0]."\n";
	my $response = "";
	while (1){
		$sock->sysread($buf,1024*10);
		$response .= $buf;
		if($buf =~ /error id=\d+/){
			if(!$_[1] == 1){
				my @split_response = split("error id", $response);
				$response = $split_response[0];
			};
			last;
		};
	};
	usleeep_(1);
	return $response;

};

sub ConvertTime{
	my $IdleSeconds = floor($_[0]/1000);
	my $IdleMinutes =  floor($IdleSeconds/60);
	my $IdleHours =  floor($IdleMinutes/60);
	$IdleSeconds = $IdleSeconds - $IdleMinutes*60;
	$IdleMinutes = $IdleMinutes - $IdleHours*60;
	my @returnTime;
	push(@returnTime, "$IdleHours$cfg{labelhours}".Pluralize($IdleHours)) if($IdleHours > 0 );
	push(@returnTime, "$IdleMinutes$cfg{labelminutes}".Pluralize($IdleMinutes)) if($IdleMinutes > 0);
	push(@returnTime, "$IdleSeconds$cfg{labelseconds}".Pluralize($IdleSeconds)) if($_[1] == 1);
	return join(' ', @returnTime) if($_[2] == 0);
	return $returnTime[0] if($_[2] == 1);
	

};
sub ParseError{
	my ($error_msg) = $_[0] =~ /msg=([^\t]+)/;
	$error_msg =~ s/ extra_msg=/ | /;
	$error_msg =~ s/\\s/ /g;
	$error_msg =~ s/\n\s/ /g;
	return $error_msg;
}
sub Pluralize{	
	return "" if ($_[0] == 1 || !$cfg{"labelplural"});
	return "s";
};
sub floor{
	return ($_[0] =~ /(\d+)/i)[0];
};

sub usleeep_{
	usleep($cfg{"slowdown"}*$_[0]) if($cfg{"slowdown"} > 0);
};
sub  trim { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s };
my $LoginResponse = ExecuteCommand("login $cfg{username} $cfg{password}",1);

my $TS3_Confirmed = $LoginResponse =~ /TS3\n/;
my $Login_Confirmed = $LoginResponse =~ /error id=0/;
my $Login_error = ParseError($LoginResponse);


print "Successfully connected to Teamspeak 3 Server\n" if ($TS3_Confirmed);
die "Error: Did not connect to a Teamspeak 3 server\n" if (!$TS3_Confirmed);
print "Login Successful\n" if ($Login_Confirmed);
die "Error: $Login_error\n" if(!$Login_Confirmed);

my $SID_Response = ExecuteCommand("use sid=$cfg{sid}", 1);
my $SID_Confirmed = $SID_Response =~ /error id=0/;
my $SID_error = ParseError($SID_Response);
print "Connected to SID $cfg{sid}\n" if ($SID_Confirmed);
die "SID Error: $SID_error\n" if(!$SID_Confirmed);

print ExecuteCommand("clientupdate client_nickname=$cfg{idlenickname}")."\n";



while($sock){
	print "\[".localtime."\] Beginning Loop...\n";
	my $client_list = ExecuteCommand("clientlist",1);
	if(!$client_list =~ /error code=0/i){ #Skips if no client information
		print "\[".localtime."\] No Client Information retrieved";
		print "--- Waiting $cfg{updatetime} second".Pluralize($cfg{"updatetime"})." before next execution\n" if ($cfg{"testing"});
		sleep($cfg{"updatetime"});
	};
	my @client_IDs = $client_list =~ /clid=(\d+)/g;	
	my $idle_times;
	my $ClientIdleCount = 0;
	my %IdleServerGroups;
	my %Clients;
	

	foreach (@client_IDs) {
		my $client_info = ExecuteCommand("clientinfo clid=$_",1);
		print "$client_info \n" if($cfg{'testing'});
		next if($client_info =~ /client_platform=ServerQuery/i); #Skips if server Query
		my ($client_idle) = $client_info =~ /client_idle_time=(\d+)/i;
		my($client_name) = $client_info =~ /client_nickname=([a-zA-Z0-9\\]{1,})/i;
		my ($client_db_id) = $client_info =~ /client_database_id=(\d+)/i;
		$client_name =~ s/\\s/ /g;
		$idle_times .=  "\t[$_]\t[$client_db_id]\t\t$client_name\t$client_idle ms\n";
		$Clients{"$client_db_id"}{"client_id"} = $_;
		$Clients{"$client_db_id"}{"client_db_id"} = $client_db_id;
		$Clients{"$client_db_id"}{"client_name"} = $client_name;
		$Clients{"$client_db_id"}{"client_idle"} = $client_idle;
		
	}; 	

	my @servergrouplist = split(/\|/, ExecuteCommand("servergrouplist",1));

	foreach (@servergrouplist) {
		
		my $servergroupid = ($_ =~ /sgid=(\d+)/)[0];
		if(length($servergroupid) == 0){
			next;
		}
		my $server_group_sort_group_id = ($_ =~ /sortid=(\d+)/)[0];
		next if(!($server_group_sort_group_id == $cfg{"serversortid"}));
		my $sgclientlist = ExecuteCommand("servergroupclientlist sgid=$servergroupid");
		# print "\$\"servergroupclientlist sgid=$servergroupid\": ".$sgclientlist."\n";
		# print "Press Enter to continue\n";
		# <STDIN>;
		if (!length($sgclientlist =~ s/^\s+//) == 0){
			print "Deleting Empty Group: ".ExecuteCommand("servergroupdel sgid=$servergroupid force=1")."\n";
			next;
		};
		# my @sg_client_db_id = split(/\|/, $sgclientlist);
		# $IdleServerGroups{"$servergroupid"}{"clients"} = "$sgclientlist";
		$IdleServerGroups{"$servergroupid"}{"name"} = ($_ =~ /name=([a-zA-Z\\0-9]{1,})/)[0];
		$IdleServerGroups{"$servergroupid"}{"response"} = ($_);
		
		my @sg_Client_list = split(/\|/, $sgclientlist);

		foreach my $Client_db_id_key (@sg_Client_list) {
			($Client_db_id_key)  = $Client_db_id_key =~ /cldbid=(\d+)/;
			$Clients{"$Client_db_id_key"}{"server_idle_group"} = $servergroupid;
		};
		if(!@sg_Client_list){
			print "(2)Deleting Empty Group sgid=$servergroupid: ".ExecuteCommand("servergroupdel sgid=$servergroupid force=1")."\n";
		};
		
		
	};
	print 	"\$Clients: \n\t".(Dumper \%Clients)."\n" if ($cfg{"testing"});
	print 	"\$IdleServerGroups: \n\t".(Dumper \%IdleServerGroups)."\n" if ($cfg{"testing"});
	
	my $total_clients = 0;
	my $client_verbose_info = "" if ($cfg{"testing"});
	foreach my $Client_key (keys {%Clients}) {
		
		
		my $client_id = $Clients{$Client_key}{"client_id"};
		my $client_db_id = $Clients{$Client_key}{"client_db_id"};
		my $client_name = $Clients{$Client_key}{"client_name"};
		$client_name =~ s/\\s/ /g;
		my $client_idle = $Clients{$Client_key}{"client_idle"};
		my $server_idle_group = "";
		$server_idle_group = $Clients{$Client_key}{"server_idle_group"} if(exists($Clients{$Client_key}{"server_idle_group"}));
		
		
		# if($client_db_id == 4 && $client_idle > 1000*5){  #For testing on a single client
		if ($client_idle > 1000*60*$cfg{"minidleminutes"}){
			# Client is Idle
			$ClientIdleCount++;
			my $client_idle_time = ConvertTime($client_idle,$cfg{"secondsenabled"},$cfg{"shortenedtime"});
			my $client_idle_time_formatted = $client_idle_time.$cfg{"idletitle"};
			$client_idle_time_formatted =~ s/ /\\s/g;
			if(exists($Clients{$Client_key}{"server_idle_group"})){
				my $server_idle_group_name = $IdleServerGroups{"$server_idle_group"}{"name"};
				if($server_idle_group_name eq $client_idle_time_formatted){
					print "Server Group $server_idle_group\'s name \"$client_idle_time\" doesn't need to be changed\n" if ($cfg{"testing"});
				}else{
					my $server_idle_rename = ExecuteCommand("servergrouprename sgid=$server_idle_group name=$client_idle_time_formatted",1);
					if($server_idle_rename =~ /error id=1282/){
						ExecuteCommand("servergroupdel sgid=$server_idle_group force=1");
						print "Server Group $server_idle_group deleted due to being unable to be renamed\n" if ($cfg{"testing"});
					}else{
						print "Server Group $server_idle_group renamed to \"$client_idle_time\"\n" if ($cfg{"testing"});
					};
				};
			}else{
				my $server_idle_add = ExecuteCommand("servergroupadd name=$client_idle_time_formatted", 1);
				if($server_idle_add =~ /error id=1282/){
					foreach my $IdleServerGroupKey (keys {%IdleServerGroups}) {
						$server_idle_group = $IdleServerGroupKey if($IdleServerGroups{$IdleServerGroupKey}{"name"} eq $client_idle_time_formatted);
					};
				}else{
					($server_idle_group) = $server_idle_add =~ /sgid=(\d+)/;
					$IdleServerGroups{$server_idle_group}{"name"} = $client_idle_time_formatted;
				};
				ExecuteCommand("servergroupaddperm sgid=$server_idle_group permsid=i_group_sort_id permvalue=$cfg{serversortid} permnegated=0 permskip=0|permsid=i_group_show_name_in_tree permvalue=2 permnegated=0 permskip=0");
				print "$client_name is now marked as idle after being idle for ".ConvertTime($client_idle,1,0)."\n";
			};
			ExecuteCommand("servergroupaddclient sgid=$server_idle_group cldbid=$client_db_id");
		}else{
			# Client is not idle
			if(exists($Clients{$Client_key}{"server_idle_group"})){
				ExecuteCommand("servergroupdelclient sgid=$server_idle_group cldbid=$Client_key");
				undef $Clients{$Client_key}{"server_idle_group"};
				print "$client_name is no longer idle.\n";
			};
		};
		
		$total_clients++;
		$client_verbose_info .= "\t$client_name\t".ConvertTime($client_idle,1,0)."\n" if ($cfg{"testing"});
		
	};
	print "\[".localtime."\] $total_clients Total Clients | ";
	print "$ClientIdleCount Idle for longer than $cfg{minidleminutes}$cfg{labelminutes}".Pluralize($cfg{"minidleminutes"})."\t\n";
	print "\t[name]\t[Current Idle Time]\n$client_verbose_info" if ($cfg{"testing"});
	print "--- Waiting $cfg{updatetime} second".Pluralize($cfg{"updatetime"})." before next execution\n" if ($cfg{"testing"});
	sleep($cfg{"updatetime"});
	
};

close $sock;
die "Connection Lost\n";