# gene-daisychain
Linking several gene annotations in an easy to use web interface. It's a neo4j graph database with a web interface which stores different annotation between 

The web interface uses a JavaScript library from KnetMiner: https://github.com/Rothamsted/knetminer, https://knetminer.rothamsted.ac.uk/KnetMiner/, https://www.sciencedirect.com/science/article/pii/S2212066116300308

This is mostly Python code
## Setup

You have three things that have to be running, could be on the same machine, could be on two. There is a Daisychain_config.txt file in every folder, make sure that the servers' IPs and ports are correct, and that these ports are open to each other.

In the following we have two machines: a *server* which runs the graph database, and a *client* which runs the web-frontend and sends user queries to the graph database running on *server*.

### Daisychain server

This is the neo4j graph database containing the links between genes running on *server*. It needs to be up and running and visible to the world, in a screen session or as a daemon.

    python3 /mnt/Daisychain_server/Daisychain_server.py

### Daisychain gateway

There's a client script which facilitates communication between the server and the web-server (=client). It also has to be up and running on the *client*.

    python3 /mnt/Daisychain_Gateway/Daisychain_Client.py
    
### Daisychain web frontent

This is the web server running on *client*. There's a bash script in Daisychain_knet_web which will host the server using npm's serve, but feel free to use Apache too.


    bash start_server.sh


### Talking to all these

The script Daisychain_admin/Daisychain_admin.py is used to build new databases. Run this (with the correct config file):

    python3 Daisychain_admin/Daisychain_admin.py 
    
Press 1 to see all databases, press 2 to create new databases, etc.

There is E. coli example input data in the folder *example* in this repo. Building this database should only take 5 minutes.


## Things to change

You have to adjust the daisychain_config.txt everywhere. I also hardcoded some example data from each database in *Daisychain_knet_web/javascript*



