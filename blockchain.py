#!/usr/bin/python3
import hashlib
import socket
import sys
import select
import time
import random
import copy

#Project by Theo Gerwing
#Student Number: 7864797

host = '' #Used when creating a socket
port = 0 #Used when creating a socket
request = '' #Used in socket communication
sendData = '' #Used in socket communication
dataSize = 8192 #Size of the data when using the recv() function

vendorId = "bob" #The private id of the vendor
vendorPubKey = hashlib.sha256(vendorId.encode()).hexdigest() #The public id of the vendor
delim = "d" #Character used as a delimiter for a few functions
initialMinerId = "miner" #The private id of the initial miner
initialMinePubKey = hashlib.sha256(initialMinerId.encode()).hexdigest() #The public id of the initial miner
miningTime = 1 #The time it takes to mine a block in seconds
miningReward = 1 #The reward (in points) for mining a block
scoringReward = 100 #The reward for having the right item for a contest
testMode = False #Whether or not we are in test mode

lastMineTime = 0 #The last time a block was mined
randomNode = 0 #Randomly chooses a node to mine a block (Simulates proof of work)

#Contests are held by the vendor. The vendor chooses which items "won" the contest. If someone had one of those items at the time, they get a reward
class Contest:
    def __init__(self, myTimestamp, myItems):
        self.timestamp = myTimestamp #Time the contest was logged
        self.items = myItems #Winners of the contest
        
    def getTime(self):
        return self.timestamp
        
    def getItems(self):
        return self.items

#Each Node has it's own copy of the blockchain.
class Node:
    def __init__(self, myBlockchain, pubKey):
        self.blockchain = myBlockchain #Copy of the blockchain
        self.user = pubKey #The miner
        
    def getChain(self):
        return self.blockchain
        
    def getUser(self):
        return self.user

#An item is created by the vendor. It has a name and a list of stats
class Item:
    def __init__(self, itemName, itemStats):
        self.name = itemName #Item name
        self.stats = itemStats #Item Stats
        
    #Returns a string in the format "ItemName [stat1 stat2 stat3... ]"    
    def getString(self):
        returnVal = self.name + " ["
        for i in self.stats:
            returnVal = returnVal + i + " "
            
        returnVal = returnVal + "]"
        return returnVal
        
    #Checks if an item is the exact same as another item (Same stats, same name)
    def isEqual(self, otherItem):
        if(self.getString() == otherItem.getString()):
            return True
        else:
            return False

#Data is a transaction of items.
class Data:
    def __init__(self, myPrivKeyA, myPubKeyA, myPrivKeyB, myPubKeyB, myItemsA, myItemsB):
        self.privKeyA = myPrivKeyA #Person A's private key
        self.pubKeyA = myPubKeyA #Person A's public key
        self.privKeyB = myPrivKeyB #Person B's private key
        self.pubKeyB = myPubKeyB #Person B's public key
        self.itemsA = myItemsA #The items Person A is giving up and Person B is getting
        self.itemsB = myItemsB #The opposite of itemsA
            
    #Used to ensure the keys provided are valid. Must be true to complete the transaction
    def validKeys(self):
        if((self.privKeyA != None) and (self.privKeyB != None) and (self.pubKeyA != None) and (self.pubKeyB != None)):
            if((hashlib.sha256(self.privKeyA.encode()).hexdigest() == self.pubKeyA) and (hashlib.sha256(self.privKeyB.encode()).hexdigest() == self.pubKeyB)):
                return True
            else:
                return False
        else:  
            return False
            
    #Determine if the supplied key when hashed is equal to public key A. Used to determine if the vendor is performing a transaction        
    def isVendorKey(self):
        if((self.pubKeyA == vendorPubKey) and (hashlib.sha256(self.privKeyA.encode()).hexdigest() == self.pubKeyA)):
            return True
        else:
            return False
         
    #Provides a string of the transaction
    def getString(self):
        returnString = self.privKeyA + self.pubKeyA
        if(not self.isVendorKey()):
            returnString = returnString + self.privKeyB + self.pubKeyB
        if(self.itemsA != None):
            for i in self.itemsA:
                returnString = returnString + i.getString()
        if(self.itemsB != None):
            for i in self.itemsB:
                returnString = returnString + i.getString()
        return returnString
    
    #Returns all the items within this transaction
    def getItems(self, person):
        if((person == vendorPubKey) and (self.pubKeyA == vendorPubKey)):
            return self.itemsA
        elif(self.pubKeyA == person):
            return self.itemsB + [delim] + self.itemsA
        elif(self.pubKeyB == person):
            return self.itemsA + [delim] + self.itemsB
        else:
            return []
            
    def getPubKeyA(self):
        return self.pubKeyA
        
    def getPubKeyB(self):
        return self.pubKeyB
        
    def getItemsA(self):
        return self.itemsA
    
    def getItemsB(self):
        return self.itemsB

#The Blockchain is made up of Blocks. Each Block contains a data(transaction of items)
class Block:
    def __init__(self, givenData, hashPrev, pubKey, time):
        self.data = givenData #The transaction stored in this block
        self.miner = pubKey #The person who mined this block
        self.timestamp = time #When this block was mined
        self.previousHash = hashPrev #Hash of the previous block. Used in the hash of this block
        self.nextBlock = None #Pointer to the next Block in the chain (Not used in the hash as this will change)
        
    def connectNew(self, block):
        self.nextBlock = block
    
    #Generates a hash based on the data, the miner, the timestamp and the previous hash. This will never change after the block is created    
    def getHash(self):
        if(self.data != None):
            myHash = hashlib.sha256((self.data.getString() + self.miner + str(self.timestamp) + str(self.previousHash)).encode()).hexdigest()
        else:
            myHash = hashlib.sha256(str(self.previousHash).encode()).hexdigest()
        return myHash
    
    #Gets all items from the stored transaction
    def getItems(self, person):
        if(self.data != None):
            return self.data.getItems(person)
        else:
            return []
    
    def getNextBlock(self):
        return self.nextBlock
        
    def getTime(self):
        return self.timestamp
        
    def getMiner(self):
        return self.miner

#The blockchain. Made up of blocks. Stored in a linked list format
class Blockchain:
    def __init__(self):
        self.head = Block(None, 0, None, 0) #The head of the Blockchain. Set to an empty block
        self.tail = self.head #The end block of the blockchain
    
    def updateTail(self, block):
        self.tail.connectNew(block)
        self.tail = block
    
    #Gets all the items for a particular person. This is done by taking all the items this person ever had and removing the ones they traded    
    def getItems(self, person):
        gainItems = [] #The items gained from a trade at some point
        loseItems = [] #The items lost to a trade at some point
        tempItems = [] #While iterating through the chain, stores new transactions here to parse
        returnItems = [] #The list of items to be returned. Of the format: [gained items, delim, lost items]
        isGaining = True 
        curr = self.head
        while curr != None:
            tempItems = curr.getItems(person)
            if(len(tempItems) > 0):
                for i in tempItems:
                    if (i == delim):
                        isGaining = False
                    else:
                        if(isGaining):
                            gainItems.append(i)
                        else:
                            loseItems.append(i)
            isGaining = True
            curr = curr.getNextBlock()
            
        returnItems = gainItems + [delim] + loseItems
        return returnItems
    
    #Calulates the score of a user. This is done by checking what the user had the block added directly before the contest
    def calculateScore(self, person, contests):
        gainItems = []
        loseItems = []
        tempItems = []
        checkItems = []
        contestItems = []
        isGaining = True
        curr = self.head
        currTimestamp = 0 #Timestamp of the current contest
        currScore = 0
        #Iterates through all the contests. Checks the persons items directly before this point and awards points for any items matching a contest winner
        for i in range(len(contests)):
            currTimestamp = contests[i].getTime()
            contestItems = contests[i].getItems()
            while curr != None and curr.getTime() < currTimestamp:
                tempItems = curr.getItems(person)
                if(curr.getMiner() == person):
                    currScore = currScore + miningReward
                if(len(tempItems) > 0):
                    for j in tempItems:
                        if (j == delim):
                            isGaining = False
                        else:
                            if(isGaining):
                                gainItems.append(j)
                            else:
                                loseItems.append(j)
                isGaining = True
                curr = curr.getNextBlock()
            checkItems = gainItems + [delim] + loseItems
            checkItems = removeLoses(checkItems)
            for k in range(len(contestItems)):
                for l in range(len(checkItems)):
                    if contestItems[k].isEqual(checkItems[l]):
                        currScore = currScore + scoringReward
                        
        return currScore
    
    def getTail(self):
        return self.tail
        
#This function recieves the input from calculateScore or Blockchain.getItems takes: [Items gained from trade, delim, items lost from trade]
#Function transforms the above input into [Persons items after removing those lost from trade]        
def removeLoses(items):
    isAtLoses = False
    foundVal = False
    returnArray = []
    for i in items:
        if (i == delim):
            isAtLoses = True
        elif(isAtLoses):
            for j in returnArray:
                if(i.isEqual(j) and (foundVal == False)):
                    returnArray.remove(j)
                    foundVal = True
            if(foundVal == False):
                returnArray = None
                return returnArray
            else:
                foundVal = False
        else:
            returnArray.append(i)
            
    return returnArray

#Checks if both people in a transaction have the nessisary items to perform the transaction
def hasItems(data, blockchain):
    itemsA = blockchain.getItems(data.getPubKeyA())
    itemsB = blockchain.getItems(data.getPubKeyB())
    
    itemsA = itemsA + data.getItemsA()
    itemsB = itemsB + data.getItemsB()
    
    if((removeLoses(itemsA) != None) and (removeLoses(itemsB) != None)):
        return True
    else:
        return False

#Checks if both users in a transaction have the proper keys and the proper inventory
def checkValid(data, blockchain):
    if(data.isVendorKey()):
        return True
    else:
        if(data.validKeys() and hasItems(data, blockchain)):
            return True
        else:
            return False

def addBlock(block, blockchain):
    blockchain.updateTail(block)
    
def makeBlock(data, blockchain, miner, time):
    return Block(data, blockchain.getTail().getHash(), miner, time)
    
#Test cases if the input parameter true is set
def tests(testNum):
    #Ensure all these values are default for a consistent testing environment
    vendorId = "bob"
    vendorPubKey = hashlib.sha256(vendorId.encode()).hexdigest()
    delim = "d"
    initialMinerId = "miner"
    initialMinePubKey = hashlib.sha256(initialMinerId.encode()).hexdigest()
    miningTime = 1 
    miningReward = 1
    scoringReward = 100
    
    
    if testNum == 0:
            #Testing getting the items of an empty chain
            myItems = myBlockChains[0].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 0)
            #Testing the vendor creating items
            itemA = Item("Sword", ["Attack:4","Defense:0"])
            itemB = Item("Spear", ["Attack:4","Defense:0"])
            itemC = Item("Shield", ["Attack:4","Defense:7","Blocking:3"])
            myData.append(Data(vendorId, vendorPubKey, None, None, [itemA], None))
            myData.append(Data(vendorId, vendorPubKey, None, None, [itemB,itemC], None))
            return 1
    elif testNum == 1:
            myItems = myBlockChains[0].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            #Testing the vendor creating items
            assert(len(myItems) == 3)
            #Testing the isEqual method in the Item class
            assert(myItems[0].isEqual(Item("Sword", ["Attack:4","Defense:0"])))
            assert(not myItems[0].isEqual(Item("Sword", ["Attack:4","Defense:1"])))
            assert(not myItems[0].isEqual(Item("Sword", ["Attack:4"])))
            #Testing two valid trades (client to vendor)
            testPerson = "testone"
            testPersonPub = hashlib.sha256(testPerson.encode()).hexdigest()
            itemA = Item("Sword", ["Attack:4","Defense:0"])
            itemB = Item("Spear", ["Attack:4","Defense:0"])
            itemC = Item("Shield", ["Attack:4","Defense:7","Blocking:3"])

            myData.append(Data(testPerson, testPersonPub, vendorId, vendorPubKey, [], [itemA,itemB]))
            myData.append(Data(testPerson, testPersonPub, vendorId, vendorPubKey, [itemA], [itemC]))
            return 2
    elif testNum == 2:
            testPerson = "testone"
            testPersonPub = hashlib.sha256(testPerson.encode()).hexdigest()
            #Testing two valid trades (client to vendor)
            myItems = myBlockChains[0].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 1)
            assert(myItems[0].isEqual(Item("Sword", ["Attack:4","Defense:0"])))
            myItems = myBlockChains[0].getChain().getItems(testPersonPub)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 2)
            #Testing an invalid trade (one or more trade partner does not have the required items)
            itemA = Item("Sword", ["Attack:4","Defense:0"])
            itemB = Item("Spear", ["Attack:4","Defense:0"])
            itemC = Item("Shield", ["Attack:4","Defense:7","Blocking:3"])
            testPersonB = "testtwo"
            testPersonBPub = hashlib.sha256(testPersonB.encode()).hexdigest()
            myData.append(Data(testPersonB, testPersonBPub, vendorId, vendorPubKey, [], [itemB,itemC]))
            #Then doing a valid trade after
            myData.append(Data(testPersonB, testPersonBPub, vendorId, vendorPubKey, [], [itemA]))
            return 3
    elif testNum == 3:
            myItems = myBlockChains[0].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 0)
            testPersonB = "testtwo"
            testPersonBPub = hashlib.sha256(testPersonB.encode()).hexdigest()
            myItems = myBlockChains[0].getChain().getItems(testPersonBPub)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 1)
            assert(myItems[0].isEqual(Item("Sword", ["Attack:4","Defense:0"])))
            #Testing adding a new blockchain node then having one of them mine a new block
            myBlockChains.append(Node(copy.deepcopy(myBlockChains[0].getChain()), testPersonBPub))
            itemD = Item("Axe", ["Attack:8","Defense:0"])
            myData.append(Data(vendorId, vendorPubKey, None, None, [itemD], None))
            return 4
    elif testNum == 4:
            myItems = myBlockChains[0].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 1)
            myItems = myBlockChains[1].getChain().getItems(vendorPubKey)
            myItems = removeLoses(myItems)
            assert(len(myItems) == 1)
            hash1 = myBlockChains[0].getChain().getTail().getHash()
            hash2 = myBlockChains[1].getChain().getTail().getHash()
            assert(hash1 == hash2)
            #Testing contests
            testPerson = "testone"
            testPersonPub = hashlib.sha256(testPerson.encode()).hexdigest()
            itemB = Item("Spear", ["Attack:4","Defense:0"])
            itemC = Item("Shield", ["Attack:4","Defense:7","Blocking:3"])
            itemD = Item("Axe", ["Attack:8","Defense:0"])
            assert(myBlockChains[0].getChain().calculateScore(testPersonPub, myContests) == 0)
            myContests.append(Contest(time.time(), [itemB,itemC]))
            assert(myBlockChains[0].getChain().calculateScore(testPersonPub, myContests) == 200)
            #Performing a trade then doing a contest
            myData.append(Data(testPerson, testPersonPub, vendorId, vendorPubKey, [itemB], [itemD]))
            return 5
    elif testNum == 5:
            testPerson = "testone"
            testPersonPub = hashlib.sha256(testPerson.encode()).hexdigest()
            itemB = Item("Spear", ["Attack:4","Defense:0"])
            myContests.append(Contest(time.time(), [itemB]))
            assert(myBlockChains[1].getChain().calculateScore(testPersonPub, myContests) == 200)
            print("All tests passed! Closing program")
            sys.exit()
    
#Set the desired port, otherwise let the user know to include one. b is whether or not to run the tests
if(len(sys.argv) < 3):
    print("Run this program like this: \"python3 blockchain.py a b\" where a is port number and b is whether or not to run the automated tests (input: True or False)")
    quit()
else:
    port = sys.argv[1]
    port = int(port)
    testMode = sys.argv[2]
    testMode = str(testMode)
    if testMode == "True":
        testMode = True
    else:
        testMode = False
        
#Set up serversocket to listen on
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((host, port))
print(f"Listening on {host}: {port}\n")

myBlockChains = [Node(Blockchain(), initialMinePubKey)] #List of blockchains in the system
myData = [] #Data to be added to the blockchain
myContests = [] #List of contests. Not in the blockchain

inputs = [serversocket] #Used in the select statement
outputs = [] #Used in the select statement

lastMineTime = time.time() #Last time a block was mined
testState = 0 #Current state of the tests
testTimer = 0 #Last time a test was run

serversocket.listen()

while True:
    try:
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)
        for source in readable:
            if source is serversocket: #A client is connected
                conn, addr = serversocket.accept()
                request = (conn.recv(dataSize)).decode()
                splitRequest = request.split("\n")
                request = request.split(" ") #Get the request and split it
                sendData = ""
                if(request[0] == "/checkVendor" and len(request) == 2): #checkVendor command used to check whether or not the client communicating is the vendor
                    if(request[1] == vendorId):
                        sendData = "True"
                    else:
                        sendData = "False"
                elif(request[0] == "/create" and len(request) >= 3 and request[len(request) - 1] == vendorId): #Used by the vendor to create a new item
                    request.pop() #Remove the vendor id from the end of the request
                    newStats = [] #Stats of the new item
                    for i in range(len(request) - 2):
                        newStats.append(request[i + 2])
                    myNewItem = Item(request[1], newStats)
                    myData.append(Data(vendorId, vendorPubKey, None, None, [myNewItem], None)) #Append the item to the blockchain
                    sendData = "True"
                elif(request[0] == "/viewInventory" and len(request) == 2): #Returns the items this user currently has
                    tempPubKey = hashlib.sha256(request[1].encode()).hexdigest()
                    myItems = myBlockChains[0].getChain().getItems(tempPubKey)
                    myItems = removeLoses(myItems)
                    for i in myItems:
                        sendData = sendData + "\n" + i.getString()
                elif(request[0] == "/createMiner" and len(request) == 2 and request[1] != vendorId): #Creates a new node with the miner id of the client
                    tempPubKey = hashlib.sha256(request[1].encode()).hexdigest()
                    blockChainCopy = copy.deepcopy(myBlockChains[0].getChain())
                    myBlockChains.append(Node(blockChainCopy, tempPubKey))
                elif(len(request) == 2 and request[0] == "/score" and request[1] != vendorId): #Tallies up the current score of the user and returns it
                    tempPubKey = hashlib.sha256(request[1].encode()).hexdigest()
                    sendData = str(myBlockChains[0].getChain().calculateScore(tempPubKey, myContests))
                elif(len(splitRequest) > 2 and splitRequest[0] == "/contest" and splitRequest[1] == vendorId): #Adds a new contest. Appends it to myContests
                    tempTimeStamp = time.time()
                    tempItems = [] #The winners of the contest
                    tempName = "" #Name of a winner
                    tempStats = [] #Stats of a winner
                    iterator = 2
                    while iterator < len(splitRequest):
                        tempString = splitRequest[iterator]
                        tempString = tempString.split(" ")
                        tempName = tempString[0]
                        for i in range(1, len(tempString)):
                            tempStats.append(tempString[i])
                        tempItems.append(Item(tempName, tempStats))
                        tempStats = []
                        iterator = iterator + 1
                    myContests.append(Contest(tempTimeStamp, tempItems))
                elif(len(splitRequest) > 5 and splitRequest[0] == "/create" and splitRequest[1] != vendorId): #Performs a trade
                    traderId = splitRequest[1]
                    traderPubId = splitRequest[2]
                    recieverId = splitRequest[3]
                    recieverPubId = splitRequest[4]
                    traderItems = []
                    recieverItems = []
                    tempString = ""
                    tempName = ""
                    tempStats = []
                    iterator = 5
                    foundDelim = False
                    #Adds items to traderItems until the delim is found then adds to recieverItems
                    while iterator < len(splitRequest):
                        if(splitRequest[iterator] == delim):
                            foundDelim = True
                        else:
                            tempString = splitRequest[iterator].replace("[", "")
                            tempString = tempString.replace("]", "")
                            tempString = tempString[:-1]
                            tempString = tempString.split(" ")
                            tempName = tempString[0]
                            for i in range(1, len(tempString)):
                                tempStats.append(tempString[i])
                            if(foundDelim):
                                recieverItems.append(Item(tempName, tempStats))
                            else:
                                traderItems.append(Item(tempName, tempStats))
                            tempStats = []
                        iterator = iterator + 1
                    myData.append(Data(traderId, traderPubId, recieverId, recieverPubId, traderItems, recieverItems))
                conn.send(sendData.encode()) #Send out any neccissary data
                conn.close() #Close the connection
        if (len(myData) > 0): #Check if there are transactions that need to be added to the blockchain
            if((time.time() - lastMineTime) > miningTime): #Check if it has been enough time since the mining of the last block
                lastMineTime = time.time() #Update the last time a block was mined
                randomNode = random.randint(0, len(myBlockChains) - 1) #Choose a random node to have mined this block
                if(checkValid(myData[0], myBlockChains[randomNode].getChain()) == True): #Node checks to make sure the transaction is valid
                    newBlock = makeBlock(myData[0], myBlockChains[randomNode].getChain(), myBlockChains[randomNode].getUser(), time.time()) #Node creates a new block
                    addBlock(newBlock, myBlockChains[randomNode].getChain()) #Node adds the block to it's blockchain
                    for i in myBlockChains: #Node sends the block it mined to the other nodes
                        if (not(i is myBlockChains[randomNode])):
                            tempBlock = copy.deepcopy(newBlock) #They copy the block and add it
                            addBlock(tempBlock, i.getChain())
                    myData.pop(0)
                else:
                    myData.pop(0)
        if(testMode): #Runs test cases if was specified to do so
            if((time.time() - testTimer) > 10):
                testTimer = time.time()
                testState = tests(testState)
    except Exception as e:
        print(e)

            
                     