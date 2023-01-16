# A blockchain implementation for trading of unique items

Project Idea: Blockchain implementation that stores transactions of unique items. Users can trade items
to each other. A vendor is used to create items and hold contests but does not interfere with trading.
Contests can be held by the vendor, each item in a contest awards points to a user that had that item at
the time of the contest. Points can also be gained from mining a block. Think fantasy football but does
not need to be with football players, could be anything (other sports, trading cards, etc.)

As this is just a proof of concept some features have been "faked". The mining that occurs is just the blockchain.py program choosing a random node to be the miner every minute. All nodes are created within blockchain.py, ideally they would be distributed so there is no single authroity.

Technical components: Created in Python, works on Linux machines (have not tested other operating
systems). Has a frontend (called frontend.py) and a backend (blockchain.py). These components
communicate with each other over sockets. Two frontends connect to each other to perform a trade.
Uses hashlib library for sha256 encryption.

## Instructions:

Default vendorId = bob

Start up blockchain.py first

Then open as many frontends as you like

### Front-end Commands:

/create a b: Can only be done by the vendor, creates a new item.

 * a = name of new item
 
 * b = list of stats, space separated (Can be left blank for no stats)
 
/viewInventory: Displays all the items the current user has

/contest: Declares the winners of a contest. Follow how I did it in the video if instructions are unclear.

* Can only be done by the vendor

/createMiner: Creates a miner with the id = current user. Non-Vendor only.

/trade: (Non vendor only) Trade with other users. When asked for the index of an item, start at 1 then
count up
* Example: items A and B are listed (in that order). Type 1 for A and 2 for B

/score: Displays the score of the current user (Non vendor only) 
