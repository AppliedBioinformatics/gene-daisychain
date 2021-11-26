# gene-daisychain
Linking several gene annotations in an easy to use web interface. It's a neo4j graph database with a web interface which stores different and connects annotations using MCL.

The web interface uses a JavaScript library from KnetMiner: https://github.com/Rothamsted/knetminer, https://knetminer.rothamsted.ac.uk/KnetMiner/, https://www.sciencedirect.com/science/article/pii/S2212066116300308

## Usage

Let's walk through a simple usage example. Users can, depending on the dataset used, select an example gene ID to search Daisychain:

![image](https://user-images.githubusercontent.com/413885/143526264-32036352-db3f-40eb-b3bb-fb3fc7116918.png)

This will display all genes with similar gene IDs:

![image](https://user-images.githubusercontent.com/413885/143526354-6d11f6d8-72f5-4717-aa3b-5079166a37ea.png)

Selecting this gene and clicking on 'Show graph' will reveal the gene-view, where the user can right-mouse click on genes to see more options:

![image](https://user-images.githubusercontent.com/413885/143526398-d828bbb6-c8b9-4eb3-9567-0b568b574c4a.png)

Selecting 'Show homologs' will then display all homologs for the current gene:

![image](https://user-images.githubusercontent.com/413885/143526429-d556bf35-c85c-4fac-80f1-788279012e9b.png)

3'/5' genes and more homologs can be displayed. Clicking on the 'refresh button' (arrow in a circle) will refresh the layout of the currently displayed genes.

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



