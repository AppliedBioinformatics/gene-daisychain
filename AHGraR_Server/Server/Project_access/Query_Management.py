# Provides database query functionality to AHGraR-server
# Connects to a project-specific graphDB (not the Main-DB!)
# This database can only by accessed from localhost on the server-side
# User name is neo4j, the password is stored in file "access" in project folder
# Class returns query results as returned by cypher without much editing
# Any postprocessing is performed by AHGraR-cmd or AHGraR-web
# The following functionalities are provided:
# Search for a gene and/or protein: Query must contain the project ID, everything else is optional:
# Species, Protein/Gene?, Name. Species and Name must not match over the entire field, e.g.
# ".coli" as query returns "E.coli" as well as "E.coli_abc".
# The returned protein/gene node(s) contain an unique ID. This ID is used to retrieve 5'/3' neighbours, coding genes,
# homologs, synteny-homologs etc. For these queries, only the project ID, the node ID and the relationship type are
# needed
import os
from neo4j.v1 import GraphDatabase, basic_auth


class QueryManagement:
    def __init__(self,  main_db_connection, send_data):
        self.main_db_conn = main_db_connection
        self.send_data = send_data

    # Establish a connection to project-specific graph db
    def get_project_db_connection(self, proj_id):
        # Retrieve bolt port nr from main-db
        # Project is either identified by unique ID (easy) or
        # by matching project name to a search term (still easy)
        try:
            if proj_id.isdigit():
                bolt_port = self.main_db_conn.run("MATCH(proj:Project) WHERE ID(proj)={proj_id} "
                                                       "RETURN proj.bolt_port",{"proj_id": int(proj_id)}).single()[0]
            else:
                bolt_port = self.main_db_conn.run("MATCH(proj:Project) WHERE LOWER(proj.name) contains LOWER({proj_id}) "
                                                  "RETURN proj.bolt_port LIMIT(1)", {"proj_id": str(proj_id.strip())}).single()[0]
            with open(os.path.join("Projects", str(proj_id), "access"), "r") as pw_file:
                bolt_pw = pw_file.read()
            project_db_driver = GraphDatabase.driver("bolt://localhost:" + str(bolt_port),
                                          auth=basic_auth("neo4j", bolt_pw), encrypted=False)
            return (project_db_driver.session())
        # Except errors while establishing a connection to project db and return error code
        except:
            self.send_data("-7")
            return




    # React to request send from a user app
    # User_request is a list of the "_" split command
    # e.g. [SEAR, ProjectID, Organism:Chromosome:Name:Annotation:Gene/Protein(Both]
    def evaluate_user_request(self, user_request):
        if user_request[0] == "SEAR" and user_request[1].isdigit() and len(user_request) == 4:
            self.find_node(user_request[1:])
        if user_request[0] == "RELA" and user_request[1].isdigit() and len(user_request) == 5:
            self.find_node_relations(user_request[1:])
        else:
            self.send_data("-8")

    def find_node(self, user_request):
        # Connect to the project-db
        project_db_conn = self.get_project_db_connection(user_request[0])
        # Determine requested return format
        # Format is either optimized for AHGraR-cmd or AHGraR-web
        return_format = user_request[1]
        if not return_format in ["CMD", "WEB"]:
            self.send_data("-9")
            return
        # "_" underscores were replaced by "\t" before being send to the server
        # Undo this here
        query_term = [item.strip().replace("\t", "_") for item in user_request[2].split(":")]
        print(query_term)
        # Species name or gene/protein name to query for can be empty
        query_species = str(query_term[0]).lower()
        query_chromosome = str(query_term[1]).lower()
        query_name = str(query_term[2]).lower()
        query_anno = str(query_term[3]).lower()
        query_type = str(query_term[4].lower())
        if query_type not in ["gene", "protein", "both"]:
            self.send_data("-10")
            return
        # Collect gene node hits and protein node hits
        gene_node_hits = []
        protein_node_hits = []
        # Search for gene node(s)
        if query_type in ["gene", "both"]:
            query_hits = project_db_conn.run("MATCH(gene:Gene) WHERE LOWER(gene.species) "
                                             "CONTAINS {query_species} "
                                             "AND LOWER(gene.gene_name) CONTAINS {query_name} WITH COLLECT(gene) AS "
                                             "genes UNWIND genes AS g1 UNWIND genes AS g2 "
                                             "OPTIONAL MATCH (g1)-[rel]->(g2) RETURN g1,rel,g2",
                                             {"query_species":query_species, "query_name": query_name,
                                              "query_chromosome":query_chromosome, "query_anno":query_anno})
            for record in query_hits:
                print(record["g1"]["geneId"], record["rel"], record["g2"])
            # for record in query_hits:
            #     gene_node_hits.append([str(record["gene"][item]) for item in ["geneId","species", " chromosome", "contig_name", "start",
            #                                              "stop", "gene_name"]] )
            # gene_node_hits.sort(key= lambda x: (x[1], x[2], x[3], x[4]))
            # gene_node_hits = ["\t".join(item) for item in gene_node_hits]
        # Search for protein node(s)
       # if query_type in ["protein", "both"]:
       #     query_hits = project_db_conn.run("MATCH(gene:Gene)", {})
       # self.send_data("\n".join(gene_node_hits))
        self.send_data("Working on it")


        # Close connection to the project-db
        project_db_conn.close()
