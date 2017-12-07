import time
import telnetlib
import re
import string

"""

When using telnetlib.Telnet.read_until(), you have to write your first parameter like b'blahblah' to
encode it as a byte string. Then you must follow with a decode() function to make it UTF-8
"""
class TeamSpeak3:
	__conn = telnetlib.Telnet()
	__lastCommand = ""
	__lastMessage = "" # Return information
	__lastStatus = "" # Return error and message
	__verbosity = False
	__escapeValues = { '/' : '\/' , ' ' : '\s' , '|' : '\p' , '\a' : '\\a' , '\b' : '\\b' , '\f' : '\\f' , '\n' : '\\n' , '\r' : '\\r' , '\t' : '\\t' , '\v' : '\\v'} # NormalValue : Teamspeak value




	def connect(self, hostname , portname):
		"""

		:param string hostname: The address of the server.
		:param string portname: The port of the server.
		"""
		self.__conn.open(hostname.encode(), portname.encode())

		"""
		Teamspeak 3 servers have the following welcome message:

		TS3
		Welcome to the TeamSpeak 3 ServerQuery interface, type "help" for a list of commands and "help <command>" for information on a specific command.

		So this just flushes the buffer.
		"""
		self.__lastMessage = self.__conn.read_until(b'command.\n', 5).decode()
		self.printLastMessage()

	def connected(self):
		"""
		Checks if the connection is still open.

		:returns boolean: True if still connected, false if connection has been lost.
	    """

		if(self.__conn.get_socket()):
			return True
		else:
			return False

	def executeCommand(self, command):
		self.__lastMessage = ''
		self.__lastCommand = command
		self.__conn.write((command + "\n").encode()) # send the command to the server
		bufferMsg = self.__conn.read_until(b'\n', 1).decode('ascii',errors='ignore')
		# keeps cycling through the return until it finds "error id" in the message
		while(re.search("error id", bufferMsg)  == None):
			self.__lastMessage += bufferMsg
			bufferMsg = self.__conn.read_until(b'\n', 1).decode('ascii',errors='ignore')

		self.__lastStatus = bufferMsg
		self.printLastMessage()

	def login(self, username, password, serverID, nick):
		"""

		:param string username: The serverQuery username
		:param string password: The serverQuery password
		:param string serverID: Server ID (usually 1)
		:param string nick: The display nickname that people will see when actions are taken and shown in the log.
		:returns boolean: Returns True if login was successful
		"""
		self.executeCommand('login ' + username + ' ' + password)
		if (self.getErrorCode() != '0'):
			raise ValueError(self.getMsg() + "Error Code " + self.getErrorCode())
		self.executeCommand('use ' + serverID)
		if (self.getErrorCode() != '0'):
			raise ValueError('Could not connect to serverID. ' + self.getMsg())
		self.executeCommand('clientupdate client_nickname=' + nick)
		nickNumber = 0
		while (self.getErrorCode() == '513' and nickNumber < 20): # Nick is already in use
			nickNumber += 1
			self.executeCommand('clientupdate client_nickname=' + nick+nickNumber)
		if (self.getErrorCode() != '0'):
			raise ValueError('Could not set nickname. ' + self.getMsg())

		return True

	def getClientIdleList(self):
		"""
		Gets the list of clients and their length of time idle.

		:returns Teamspeak3IdleClient[]: Returns an array of Teaspeak3IdleClient objects
		"""
		self.executeCommand('clientlist')

		clientList = self.__lastMessage.split('|')
		clientObjList = []

		print(self.__lastMessage)

		print("clientList", clientList)
		for client in clientList:
			try:
				clientObj = Teamspeak3IdleClient()
				clientObj.clid = re.search('clid=(\d+)', client).group(1)
				clientObj.databaseid = re.search('client_database_id=(\d+)', client).group(1)
				clientObj.name = self.escapeString(re.search('client_nickname=([a-zA-Z0-9\\\]+)' , client).group(1))
				print('clientinfo clid=' + clientObj.clid)
				self.executeCommand('clientinfo clid=' + clientObj.clid)
				clientObj.idle = int(re.search('client_idle_time=(\d+)', self.__lastMessage).group(1))
				clientObjList.append(clientObj)
			except:
				print("Error processing client: ", client )

		return clientObjList

	def getServerGroupbySortID(self, sortIDRequested):
		"""
		Gets the list of server groups that match the sortIDRequested.

		:returns Teamspeak3IdleServerGroup[]: Returns an array of Teamspeak3IdleServerGroup objects
		"""
		self.executeCommand('servergrouplist')

		serverGroupList = self.parseLastMsg()
		serverGroupObjList = []

		for serverGroup in serverGroupList:
			serverGroupObj = Teamspeak3IdleServerGroup()
			try:
				serverGroupObj.sortID = serverGroup.get('sortid')
			except:
				continue
			if (serverGroupObj.sortID != sortIDRequested):
				continue
			serverGroupObj.id = serverGroup.get('sgid')
			serverGroupObj.name = self.unescapeString(serverGroup.get('name'))
			self.executeCommand("servergroupclientlist sgid=" + serverGroupObj.id)
			clientList = self.parseLastMsg()
			for client in clientList:
				clientID = client.get('cldbid')
				serverGroupObj.clients.append(clientID)

			# delete empty groups
			if(len(serverGroupObj.clients) == 0 ):
				self.executeCommand('servergroupdel sgid='+ serverGroupObj.id +' force=1')

			serverGroupObjList.append(serverGroupObj)


		return serverGroupObjList

	def getErrorCode(self):
		"""
		Returns a string of the error code of the last command used.

		:return string:
		:type return: str
		"""
		match = re.search('error id\=([0-9]+)', self.__lastStatus)
		return match.group(1).strip()

	def getMsg(self):
		"""
		Returns a string of the msg of the last command used.

		:return string:
		"""
		match = self.unescapeString(re.search('msg\=([^\n]+)', self.__lastStatus).group(1))
		return match.strip()

	def parseLastMsg(self):
		'''

		:return: A dictionary of the returned values.
		:type return: dict
		'''
		returnDictionary = []

		# return an empty array if there is nothing to run on
		if(len(self.__lastMessage) > 0):
			responses = self.__lastMessage.split('|')
			for response in responses:
				responseDict = {}
				for attribute in response.split(' '):
					values = re.search("([^\=]+)=([^\=]+)",attribute)
					if(values != None):
						responseDict[values.group(1).strip()] = self.unescapeString(values.group(2).strip())
				returnDictionary.append(responseDict)

		return returnDictionary

	def verbose(self, setVerbosity):
		"""
		Setting setVerbosity to True will print any responses from the server whenever any command is executed.

		:param bool setVerbosity: False (off) / True (on)
		"""
		self.__verbosity = setVerbosity



	def printLastMessage(self):
		if (self.__verbosity):
			print("Command: "+self.__lastCommand.strip() +"\nResponse: "+ self.__lastMessage.strip()+"\nError: "+ self.__lastStatus.strip())


	def __flushText(self):
		self.__lastMessage = self.__conn.read_until(b'98ig8gad8ug', 1).decode()
		self.printLastMessage()

	def escapeString(self, inputString):
		'''
		Replaces normal characters with escaped characters for executing commands.

		:param inputString: The value to convert
		:type inputString: str
		:return: The escaped string
		:type return: str
		'''
		newString = inputString
		for unescaped, escaped in self.__escapeValues.items():
			newString = newString.replace(unescaped, escaped)

		return newString

	def unescapeString(self, inputString):
		'''
		Replaces escaped characters with normal characters for reading returned data.

		:param inputString: The value to convert
		:type inputString: str
		:return: The unescaped string
		:type return: str
		'''
		newString = inputString
		for unescaped, escaped in self.__escapeValues.items():
			newString = newString.replace(escaped, unescaped)

		return newString


	def disconnect(self):
		self.__conn.close()

class Teamspeak3IdleClient:
	clid = ''
	databaseid = ''
	name = ''
	idle = 0

	def returnServerGroupsClientIsIdleIn(self, serverGroupList):
		'''

		:type serverGroupList: Teamspeak3IdleServerGroup[]:
		:type return: Teamspeak3IdleServerGroup[]
		'''
		returnedList = []
		for sg in serverGroupList:
			try:
				if (sg.clients.index(self.databaseid) > -1):
					returnedList.append(sg)
			except ValueError:
				continue

		return returnedList


class Teamspeak3IdleServerGroup:
	name = ''
	id = ''
	sortID = ''
	clients = []

	def __init__(self):
		self.clients = list()


