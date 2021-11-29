# gene-daisychain
Linking several gene annotations in an easy to use web interface. It's a neo4j graph database with a web interface which stores different and connects annotations using MCL.

The web interface uses a JavaScript library from KnetMiner: https://github.com/Rothamsted/knetminer, https://knetminer.rothamsted.ac.uk/KnetMiner/, https://www.sciencedirect.com/science/article/pii/S2212066116300308

## Usage

Let's walk through a simple usage example. Users can, depending on the dataset used, select an example gene ID to search Daisychain:

![image](https://user-images.githubusercontent.com/413885/143526264-32036352-db3f-40eb-b3bb-fb3fc7116918.png)

This will display all genes with similar gene IDs:

![image](https://user-images.githubusercontent.com/413885/143526354-6d11f6d8-72f5-4717-aa3b-5079166a37ea.png)

Selecting this gene and clicking on 'Show graph' will reveal the gene-view, where the user can right-mouse click on genes to see more options:

![image](https://user-images.githubusercontent.com/413885/143526789-2d68b41b-ac1b-4c9c-9c46-6d55c70130d7.png)

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


### Setting up a new database

The script Daisychain_admin/Daisychain_admin.py is used to build new databases. Run this (with the correct config file):

    python3 Daisychain_admin/Daisychain_admin.py 
    
Press 1 to see all databases, press 2 to create new databases, :

![image](https://user-images.githubusercontent.com/413885/143820165-2cb48294-b219-48be-a4bb-a4b1164f79f6.png)

Press (2) to make a new project, give it a name, then (3) to import data into this project. Here is an example CSV for two assemblies that step (3) will take:

<pre>
Brassica napus,ZS11,genome,/some/location/brassica_napus/Brassica_napus_ZS11_genome_assemblyV201608.fa
Brassica napus,ZS11,annotation,/some/location/brassica_napus/Brassica_napus_ZS11_GenesetV201608_head.gff
Brassica napus,Darmorv5,genome,/some/location/brassica_napus/Brassica_napus_v4.1.chromosomes.fa
Brassica napus,Darmorv5,annotation,/some/location/brassica_napus/Brassica_napus.annotation_v5_head.gff3
</pre>

Copy-paste the paste to this CSV, and the clustering and import step will begin. The running server will print status updates, example:

<pre>
Importing now
Brassica napus,ZS11,genome,/some/location/brassica_napus/Brassica_napus_ZS11_genome_assemblyV201608.fa
Importing now
Brassica napus,ZS11,annotation,/some/location/brassica_napus/Brassica_napus_ZS11_GenesetV201608_head.gff
Importing now

Finished importing
</pre>

Once `Finished importing` has printed, we can build the database. Go to the admin script and press (4), to build a projects database. Choose the right project ID. It will print how many genomes and annotations it has found (2 in the above example).

One can then choose whether admin should guess as much as possible from the gff, or set fields to manual: 

![image](https://user-images.githubusercontent.com/413885/143820636-5157a55d-a334-43f6-b53c-fcdab389b5b4.png)

(a)utomatic mode works with many gffs. After a few seconds, the parser will print potential annotations it has found:

![image](https://user-images.githubusercontent.com/413885/143820727-e814a761-b4e4-452a-a4e6-4a7b37c862c3.png)

Choose one that makes sense via 1, 2, 3, etc., and proceed through all assemblies in this way. Then wait for the clustering to end, the Server window will provide constant updates.

You can use the admin menu to check on the status of the database via the (1) option, List available projects, it should look like this once it's finished:

![image](https://user-images.githubusercontent.com/413885/143821641-f81ad349-81c3-4d3c-b630-9520bdbb52fd.png)

While the clustering is running, this status window will display INIT_SUCCESS.

There is E. coli example input data in the folder *example* in this repo. Building this database should only take 5 minutes. 



