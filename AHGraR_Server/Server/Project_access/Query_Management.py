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
        # Check if query term has expected length: ["Organism", "Chromosome", "Keyword", "Protein/Gene/Both]
        # Fields can be left empty, i.e. being ""
        # Keyword looks in both gene/protein name and gene/protein annotation
        if len(query_term) != 4:
            self.send_data("-10")
            return
        # Species name or gene/protein name to query for can be empty
        query_species = str(query_term[0]).lower()
        query_chromosome = str(query_term[1]).lower()
        query_keyword = str(query_term[2]).lower()
        query_type = str(query_term[3].lower())
        if query_type not in ["gene", "protein", "both"]:
            self.send_data("-11")
            return
        # Collect gene node hits and protein node hits
        # Also collect relations between gene nodes, protein nodes
        # and gene/protein nodes
        # Nodes are first collected in dicts to ensure uniqueness
        # Format: dict["ProteinID"]= ("Protein_name", "Protein_descr")
        # or dict["GeneID"]=("Organism", "chromosome", "contig_name", "strand", "start", "stop", "gene_name")
        # These are later turned into a list format:
        # ("Protein", "ProteinID", "Protein_name", "Protein_descr")
        # Relationships between nodes are stored in list format:
        # ("ProteinID", "relation", "ProteinID")
        gene_node_hits = {}
        gene_node_rel = []
        protein_node_hits = {}
        protein_node_rel = []
        protein_gene_node_rel = []
        # Search for gene node(s) and gene-gene relationships
        if query_type in ["gene", "both"]:
            query_hits = project_db_conn.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
                                             "AND LOWER(gene.gene_name) CONTAINS {query_keyword} WITH COLLECT(gene) AS "
                                             "genes UNWIND genes AS g1 UNWIND genes AS g2 "
                                             "OPTIONAL MATCH (g1)-[rel]->(g2) RETURN g1,rel,g2",
                                             {"query_species": query_species, "query_keyword": query_keyword,
                                              "query_chromosome": query_chromosome, "query_anno": query_keyword})
            # The record format is a n x m matrix of all possible relations between gene nodes
            # First column is gene node 1, third is gene node 2 and the middle column is the relationship between
            # g1 and g2. This relationship can be None, i.e. there is no relationship.
            # The overall set of matching gene nodes is extracted from column 1 and stored in a dict to enforce
            # uniqueness.
            for record in query_hits:
                gene_node_hits[record["g1"]["geneId"]] = \
                    [record["g1"][item] for item in ["species", " chromosome", "contig_name", " strand",
                                                     "start", "stop", "gene_name"]]
                if record["rel"]:
                    gene_node_rel.append((record["g1"]["geneId"], record["rel"].type, record["g2"]["geneId"]))
        # Search for protein nodes and protein-protein relationships
        # Proteins are always coded for by genes. The keyword query is therefore matched against the gene name, the
        # protein name and the protein description.
        if query_type in ["protein", "both"]:
            query_hits = project_db_conn.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
                                             "CONTAINS {query_species} AND (LOWER(prot.protein_name) CONTAINS "
                                             "{query_keyword} OR LOWER(prot.protein_descr) CONTAINS {query_keyword} "
                                             "OR LOWER(gene.gene_name) CONTAINS {query_keyword}) WITH "
                                             "COLLECT(prot) AS prots UNWIND prots as p1 UNWIND prots as p2 "
                                             "OPTIONAL MATCH (p1)-[rel]->(p2) RETURN p1,rel,p2",
                                             {"query_species":query_species, "query_keyword":query_keyword})
            for record in query_hits:
                protein_node_hits[record["p1"]["proteinId"]] = \
                    [record["p1"]["protein_name"], record["p1"]["protein_descr"]]
                # Check if protein p1 has a relationship to protein p2
                # Possible types of relationship: HOMOLOG or SYNTENY,
                # both with the additional attribute "sensitivity" (of clustering)
                if record["rel"]:
                    protein_node_rel.append((record["p1"]["proteinId"], record["rel"].type,
                                             record["rel"]["sensitivity"], record["p2"]["proteinId"]))


        # Search for gene-protein relationships (only if looking for both protein and gene nodes)
        # i.e. relations between both gene and protein nodes found above (which can only be CODING relations)
        # Since both genes and proteins need to be found, it is sufficient that the species term and the gene_name
        # term are found (the search for protein nodes also checks the gene_name of the coding gene)
        if query_type == "both":
            query_hits = project_db_conn.run("MATCH coding_path = (gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
                                             "CONTAINS {query_species} AND LOWER(gene.gene_name) CONTAINS {query_keyword} "
                                             "RETURN gene.geneId, prot.proteinId",
                                             {"query_species": query_species, "query_keyword": query_keyword})
            for record in query_hits:
                protein_gene_node_rel.append((record["gene.geneId"], "CODING", record["prot.proteinId"]))
        print("Nr. of gene nodes: "+str(len(list(gene_node_hits.keys()))))
        print("Nr. of gene-gene rel: " + str(len(gene_node_rel)))
        print("Nr. of protein nodes: " + str(len(list(protein_node_hits.keys()))))
        print("Nr. of prot-prot rel: " + str(len(protein_node_rel)))
        print("Nr. of gene-prot rel: " + str(len(protein_gene_node_rel)))
        # Transfer gene node and protein node dicts into list structures
        # Sort gene node list by species,chromosome, contig, start
        gene_node_hits = [[item[0]]+item[1] for item in gene_node_hits.items()]
        gene_node_hits.sort(key=lambda x: (x[1],x[2],x[3],x[5]))
        protein_node_hits = [[item[0]]+item[1] for item in protein_node_hits.items()]
        print(gene_node_hits[:10])
        print(protein_node_hits[:10])
        # Match geneIDs and proteinIds to their position in the node lists
        gene_id_index = {}
        gene_counter = 0
        for gene_node in gene_node_hits:
            gene_id_index[gene_node[0]]=gene_counter
            gene_counter+=1
        protein_id_index = {}
        protein_counter = 0
        for protein_node in protein_node_hits:
            protein_id_index[protein_node[0]] = protein_counter
            protein_counter += 1
        print(gene_id_index)
        print(protein_id_index)
        self.send_data("Working on it")


        # Close connection to the project-db
        project_db_conn.close()
