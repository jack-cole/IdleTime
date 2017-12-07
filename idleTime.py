import teamspeak3
import time
import re

hostname	= '192.168.1.10'
portnum		= '10011'
username	= 'IdleTime'
password	= 'nUpFfgav'
serverID	= '1'
nickname	= 'IdleTime'
reconnect   = True # if True it will try to reconnect if the connection is lost. False will terminate the program after connection lost.
servergroupSortID = '91115'
minIdleMinutes = 25

ts3 = teamspeak3.TeamSpeak3()

recon = 1 # this is set to reconnect's value after the first loop starts
# main program loop. Continously run until exited


def checkIdleClients(clientsList, serverGroupList):
	'''

	:type clientsList: Teamspeak3IdleClient[]
	:type serverGroupList: Teamspeak3IdleServerGroup[]
	'''
	for client in clientsList:

		# ignore self
		if( client.name == username):
			continue

		# client is not idle
		if(client.idle < minIdleMinutes * 60 * 1000):

			# client is in idle group
			for serverGroupID in client.returnServerGroupsClientIsIdleIn(serverGroupList):
				ts3.executeCommand('servergroupdelclient sgid='+serverGroupID.id+' cldbid='+client.databaseid)
				serverGroupID.clients.remove(client.databaseid)

		# client is idle
		else:

			timeIdleObj = IdleTime(client.idle)
			clientsServerGroups = client.returnServerGroupsClientIsIdleIn(serverGroupList)
			# client is in idle group
			if(len(clientsServerGroups) > 0):

				# rename the server group he is in if it needs to be renamed. Do not reduce the time.
				idlename = timeIdleObj.toString()
				if(timeIdleObj.compareToString(clientsServerGroups[0].name) > 0):
					ts3.executeCommand('servergrouprename sgid='+clientsServerGroups[0].id+' name=' + ts3.escapeString(idlename))
					clientsServerGroups[0].name = idlename


			#client is not in idle group
			else:

				# create new group and add client to it
				ts3.executeCommand('servergroupadd name=' + ts3.escapeString(timeIdleObj.toString()))
				errorCode = ts3.getErrorCode()

				# Server group add was successful
				if (errorCode == '0'):
					serverGroupID = ts3.parseLastMsg()[0].get('sgid')

				# if same server group name exists, search through the groups to find the same named one
				elif(errorCode == '1282'):
					for serverGroupToAddTo in serverGroupList:
						if(timeIdleObj.toString() == serverGroupToAddTo.name):
							serverGroupID = serverGroupToAddTo.id



				ts3.executeCommand('servergroupaddperm sgid='+serverGroupID+' permsid=i_group_sort_id permvalue='+servergroupSortID+' permnegated=0 permskip=0|permsid=i_group_show_name_in_tree permvalue=2 permnegated=0 permskip=0')
				ts3.executeCommand('servergroupaddclient sgid='+serverGroupID+' cldbid=' + client.databaseid)
	return


def removeOfflineClients(clients, idleServerGroups):
	'''

	:type clientsList: list[Teamspeak3IdleClient]
	:type serverGroupList: list[Teamspeak3IdleServerGroup]
	'''


	for serverGroup in idleServerGroups:
		for sgClient in serverGroup.clients:
			clientIsOnline = False
			for onlineClient in  clients:
				if(onlineClient.databaseid == sgClient and onlineClient.name != nickname):
					clientIsOnline = True
			if(clientIsOnline == False):
				ts3.executeCommand('servergroupdelclient sgid='+serverGroup.id+' cldbid='+sgClient)



class IdleTime:
	seconds = 0
	minutes = 0
	hours = 0

	def __init__(self, ms):
		ms = int(ms)

		self.seconds = int(ms / 1000)
		self.minutes = int(self.seconds / 60)
		self.hours = int(self.minutes / 60)
		self.seconds = self.seconds % 60
		self.minutes = self.minutes % 60
		self.hours = self.hours % 60

	def toString(self):
		returnTime = []
		if(self.hours > 0):
			returnTime.append(str(self.hours) + ' Hr' + ('' if self.hours == 1 else 's'))
		returnTime.append(str(self.minutes) + ' Min' + ('' if self.minutes == 1 else 's'))


		return ' '.join(returnTime) + ' Idle'

	def compareMinAccuracy(self, otherIdleTime):
		'''
		Compares to another IdleTime object

		:param otherIdleTime: IdleTime object to compare to.
		:type otherIdleTime: IdleTime
		:return: Positive if self is greater, zero if equal, and negative if self is less than.
		'''

		return (self.minutes - otherIdleTime.minutes) + ( 60 * (self.hours - otherIdleTime.hours) )

	def compareToString(self, otherIdleString):
		'''
		Compares to another IdleTime object that is in string format

		:param otherIdleString: Idletime that was converted toString()
		:type otherIdleString: string
		:return: Positive if self is greater, zero if equal, and negative if self is less than.
		'''
		hrSearch = re.search('(\d+) Hr', otherIdleString)
		if(hrSearch != None):
			otherHours = int(hrSearch.group(1))
		else:
			otherHours = 0

		minSearch = re.search('(\d+) Min', otherIdleString)
		if (minSearch != None):
			otherMinutes = int(minSearch.group(1))
		else:
			otherMinutes = 0

		return (self.minutes - otherMinutes) + (60 * (self.hours - otherHours))

while(recon):
	recon = reconnect
	ts3.verbose(False)

	try:
		print("Connecting to server.")
		ts3.connect(hostname, portnum)
		ts3.login(username, password, serverID, nickname)
		print("Connection successful! IdleTime is now running...")


		while(ts3.connected()):
			try:
				# Grab list of clients
				clients = ts3.getClientIdleList()

				# Grab list of idle server groups and delete empty ones
				idleServerGroups = ts3.getServerGroupbySortID(servergroupSortID)

				# Check each client to see if they're idle, then add them to a sever group if they are, or rename a server group they are already in. If they aren't idle, remove them from the group.
				checkIdleClients(clients, idleServerGroups)

				# Remove offine clients from server groups
				removeOfflineClients(clients, idleServerGroups)

				time.sleep(2)
			except ValueError as err:
				print("ValueError," , err.args)



	except ValueError as err:
		print("ValueError," , err.args)
		ts3.disconnect()
	except:
		print('Unidentified error. Disconnecting.')
		ts3.disconnect()

	if(recon):
		print('Reconnecting in 30 seconds')
		time.sleep(30)

ts3.disconnect()