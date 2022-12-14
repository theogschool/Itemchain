#!/usr/bin/python3
import hashlib
import socket
import sys
import select

#Frontend of the blockchain project
#Created by Theo Gerwing, Student Number: 7864797

host = 0 #The ip of the host
portNum = 0 #The port number of the host
portNumSelf = 0 
hostSelf = '' #Gets filled in by the current ip
myKey = "" #The key this user has
myPubKey = ""
data = ''
request = '' #Data from stdin
sendData = '' #Data to be sent out via socket
maxBytes = 8192 #Max size of a socket message
clientsocket = '' #Socket used to connect to the blockchain or other clients
serversocket = '' #Socket used to hear requests from other clients
delim = "d"

#Opens a connection to the blockchain sends data then closes connection
def connectToChain(myData):
    returnData = ''
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    clientsocket.connect((host,portNum))
    clientsocket.send(myData.encode())
    returnData = (clientsocket.recv(maxBytes)).decode()
    clientsocket.close()
    
    return returnData

#Opens a connection to another client, sends data, then closes the connection    
def connectToClient(myData, ip, port):
    returnData = ''
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    clientsocket.connect((ip,port))
    clientsocket.send(myData.encode())
    returnData = (clientsocket.recv(maxBytes)).decode()
    clientsocket.close()
    
    return returnData
    
#Ran if another client connects. Used for trading
def handleClientConnect():
    conn, addr = serversocket.accept()
    originalRequest = (conn.recv(maxBytes)).decode()
    request = originalRequest.split("\n") #Recieve and split the data
    sendData = ""
    if(request[0] == "/getItems"): #Sends the other client a list of the items this client has
        sendData = connectToChain("/viewInventory" + " " + myKey) 
    elif(request[0] == "/trade" and len(request) > 3): #Displays the trade offer to the user and accepts or declines
        iterator = 3
        answer = ""
        newRequest = "/create\n" + request[1] + "\n" + request[2] + "\n" 
        print("User: " + request[2] + " is requesting a trade!\nThey are offering:")
        while request[iterator] != delim: #Displays the offer to the user
            print(request[iterator] + "\n")
            iterator = iterator + 1
        iterator = iterator + 1
        print("They would like your:")
        while iterator < len(request):
            print(request[iterator] + "\n")
            iterator = iterator + 1
        print("Will you accept the trade? (Type yes or no)")
        answer = input() #Asks if the user accepts the trade
        if(answer == "yes"): #If yes sends the transaction to the blockchain
            sendData = "A"
            newRequest = newRequest + myKey + "\n" + myPubKey
            iterator = 3
            while iterator < len(request):
                newRequest = newRequest + "\n" + request[iterator]
                iterator = iterator + 1
            connectToChain(newRequest)
        else: #Otherwise let the other client know the user declined
            sendData = "B"
    conn.send(sendData.encode())
    conn.close()

#Valid commands the vendor can use
def vendor():
    print("Hello, you are the vendor. As such your valid commands are: /create, /contest, /viewInventory")
    while True:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)
            for source in readable:
                if source is serversocket: #Trade offer incoming
                    handleClientConnect()
                else: #Otherwise user has input command
                    originalRequest = input()
                    request = originalRequest.split(" ")
                    if(request[0] == "/create" and len(request) >= 2): #Create command User inputs "/create NameOfNewItem stat1OfNewItem stat2OfNewItem etc."
                        data = connectToChain(originalRequest + " " + myKey)
                        print("Successfully added new item")
                    elif(request[0] == "/viewInventory"): #Gets the vendors inventory from the blockchain
                        data = connectToChain(originalRequest + " " + myKey)
                        print("You have the inventory: " + data)
                    elif(request[0] == "/contest"): #Adds a new contest. Asks how many items are in the winning group of the contest. Then asks the vendor to input them
                        newRequest = "/contest\n" + myKey
                        print("How many items were a part of the winning group?")
                        iterations = int(input())
                        for i in range(iterations):
                            print("Type one of the winning items. These must be exact and in the format: name stat1 stat2...")
                            newRequest = newRequest + "\n" + input()
                        data = connectToChain(newRequest)
                    else: #Invalid command
                        print("Invalid command. Please see the documentation for the commands and how to use them.")
                    
        except Exception as e:
            print(e)

def client():
    print("Hello, you are a client. As such your valid commands are: /viewInventory, /createMiner, /trade, /score")
    while True:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 0)
            for source in readable:
                if source is serversocket: #Trade offer incoming
                    handleClientConnect()
                else: #Otherwise user has input command
                    originalRequest = input() 
                    request = originalRequest.split(" ") #Get and split the input
                    if(request[0] == "/viewInventory"): #Prints the inventory of the current user
                        data = connectToChain(originalRequest + " " + myKey)
                        print("You have the inventory: " + data)
                    elif(request[0] == "/createMiner"): #Creates a new node for the blockchain with the user as the miner
                        data = connectToChain(request[0] + " " + myKey)
                        print("Added a new miner")
                    elif(request[0] == "/score"): #Gets the score of the user from all the contests
                        data = connectToChain(request[0] + " " + myKey)
                        print("Your current score is: " + data)
                    elif(request[0] == "/trade" and len(request) == 3): #Sends a trade request ran like "/trade ipOfOtherClient portOfOtherClient"
                        tempIp = request[1]
                        tempPort = int(request[2])
                        count = 0
                        wantItems = [] #Items this user wants
                        giveItems = [] #Items this user is willing to give
                        currentChoice = 0
                        tradeRequest = "/trade\n"
                        
                        data = connectToClient("/getItems", tempIp, tempPort)
                        splitData = data.split("\n") #Connect to the other client and get a list of their items
                        print("Items of the recipient:" + data) #Print the items the other client has
                        print("How many items would you like to recieve?") #Asks the user how many items they want
                        count = int(input())
                        for i in range(count): #Gets all the indexs of all the items this client wants
                            print("Provide the index for a value you want. If you provide an invalid index it will be ignored")
                            currentChoice = int(input())
                            if(currentChoice < len(splitData) and currentChoice != 0):
                                wantItems.append(splitData[currentChoice])
                        data = connectToChain("/viewInventory" + " " + myKey)
                        splitData = data.split("\n") #Get the current items this user has
                        print("Your Items:" + data) #Prints all the items this user has
                        print("How many items would you like to give?") #Asks how many items this user is giving
                        count = int(input())
                        for i in range(count): #Get the indexs of all items this user is giving away
                            print("Provide the index for a value you want to give. If you provide an invalid index it will be ignored")
                            currentChoice = int(input())
                            if(currentChoice < len(splitData) and currentChoice != 0):
                                giveItems.append(splitData[currentChoice])
                        tradeRequest = tradeRequest + myKey + "\n" + myPubKey #Forms the trade request
                        for i in range(len(giveItems)):
                            tradeRequest = tradeRequest + "\n" + giveItems[i]
                        tradeRequest = tradeRequest + "\n" + delim
                        for i in range(len(wantItems)):
                            tradeRequest = tradeRequest + "\n" + wantItems[i]
                        data = connectToClient(tradeRequest, tempIp, tempPort) #Sends out the trade request
                        if (data == "A"): #Tell the user if their trade has been accepted or declined
                            print("Trade Accepted")
                        else:
                            print("Trade Declined")
                    else: #Invalid command
                        print("Invalid command. Please see the documentation for the commands and how to use them.")
                            
        except Exception as e:
            print(e)

#Get the ip and port of the host as well as the clients private key from command line arguments. If the user does not supply these, let them know how to correctly run the program
if(len(sys.argv) < 5):
    print("Run this program like this: \"python3 server.py a b c d\" where a is ip address of the blockchain and b is the port used by the host.")
    print("c is your private key. d is the port number used by this client")
    quit()
else:
    host = sys.argv[1]
    host = str(host)
    portNum = sys.argv[2]
    portNum = int(portNum)
    myKey = sys.argv[3]
    myKey = str(myKey)
    myPubKey = hashlib.sha256(myKey.encode()).hexdigest()
    portNumSelf = sys.argv[4]
    portNumSelf = int(portNumSelf)
    

#Connect to the blockchain to determine if this user is the vendor
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
clientsocket.connect((host,portNum))
clientsocket.send(("/checkVendor " + myKey).encode())
data = clientsocket.recv(maxBytes)
clientsocket.close()

#Open socket and start listening
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((hostSelf, portNumSelf))
print(f"Listening on {hostSelf}: {portNumSelf}\n")
serversocket.listen()

inputs = [serversocket, sys.stdin] #Used in the select statement
outputs = [] #Used in the select statement

if(data.decode() == "True"):
    vendor()
else:
    client()
    
