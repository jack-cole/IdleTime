# IdleTime
![idle users](https://i.imgur.com/ZMu0eDN.png) ![idle users](https://i.imgur.com/ivxrRcY.png) ![idle users](http://i.imgur.com/qgLOGLD.png)

This is a Python script that runs LOCALLY (if you try to run it remotely, you're gonna get a lot of lag) on a server with Teamspeak. It will append the time someone's been idle (not speaking, changing channels, or doing anything in Teamspeak) next to someone's name. This is helpful when you have a server full of people who leave their Teamspeak on while they do something else, and is a great alternative to moving people out of channels, which can be quite distracting to other people.

## Requirements

* Windows or Linux
	* Mac untested
* Perl
	* Suggested: Perl 5.2 or later
* Server running Teamspeak that you can execute Perl scripts on


## Installation

1. Get your ServerQuery login information
2. Rename **Example_idletime.cfg** to **idletime.cfg**
3. Open **idletime.cfg** and set the values. There's comments on everything inside.
4. Run **idletime.pl** with Perl