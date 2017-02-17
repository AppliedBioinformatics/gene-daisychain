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
        try:
            bolt_port = self.main_db_conn.run("MATCH(proj:Project) WHERE ID(proj)={proj_id} "
                                                   "RETURN proj.bolt_port",{"proj_id": int(proj_id)}).single()[0]
            with open(os.path.join("Projects", str(proj_id), "access"), "r") as pw_file:
                bolt_pw = pw_file.read()
            project_db_driver = GraphDatabase.driver("bolt://localhost:" + str(bolt_port),
                                          auth=basic_auth("neo4j", bolt_pw))
            return (project_db_driver.session())
        # Except errors while establishing a connection to project db and return error code
        except IndexError:
            self.send_data("-7")
            return




    # React to request send from a user app
    # User_request is a list of the "_" split command
    # e.g. [SEAR, ProjectID, Organism:Prot/Gene:Name]
    def evaluate_user_request(self, user_request):
        if user_request[0] == "SEAR" and user_request[1].isdigit() and len(user_request) == 4:
            self.find_node(user_request[1:])
        if user_request[0] == "RELA" and user_request[1].isdigit() and len(user_request) == 5:
            self.find_node_relations(user_request[1:])
        else:
            self.send_data("-6")

    def find_node(self, user_request):
        # Connect to the project-db
        project_db_conn = self.get_project_db_connection(user_request[0])
        self.send_data("Find a node :-)")
        # Close connection to the project-db
        project_db_conn.close()
