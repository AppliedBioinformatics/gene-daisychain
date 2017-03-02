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
# Return a list of species associated with a project
# Return a list of chromosomes found in one or all species of a project
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
        if user_request[0] == "SEAR" and user_request[1].isdigit() and len(user_request) == 7:
            self.find_node(user_request[1:])
        elif user_request[0] == "RELA" and user_request[1].isdigit() and len(user_request) == 6:
            self.find_node_relations(user_request[1:])
        elif user_request[0] == "LIST" and user_request[1].isdigit() and 3 <=len(user_request) <= 4:
            self.list_items(user_request[1:])
        else:
            self.send_data("-8")

    # List properties of data stored in project db:
    # 1. List all species in a project
    # 2. List chromsome labels of one or all species in a project
    def list_items(self, user_request):
        # Connect to the project-db
        project_db_conn = self.get_project_db_connection(user_request[0])
        # Init the return value container
        reply_container = []
        if user_request[1] == "SPECIES":
            query_hits = project_db_conn.run("MATCH(gene:Gene) RETURN DISTINCT gene.species ORDER BY gene.species")
            for record in query_hits:
                reply_container.append(record["gene.species"])
        if user_request[1] == "CHROMOSOME" and 2 <= len(user_request) <= 3:
            # If no species was defined, return the distinct chromosome names of all species
            # Else return only the chromosomes of the selected species
            # Replace any tabs in species name with underscores
            if len(user_request) == 2:
                query_hits = project_db_conn.run("MATCH (gene:Gene)  RETURN DISTINCT gene.chromosome "
                                                 "ORDER BY gene.chromosome")
            elif len(user_request) == 3:
                query_hits = project_db_conn.run("MATCH (gene:Gene)  WHERE gene.species = {species_name} RETURN "
                                                 "DISTINCT gene.chromosome ORDER BY gene.chromosome",
                                                 {"species_name":user_request[2].replace("\t", "_")})
            else:
                query_hits = []
            for record in query_hits:
                reply_container.append(record["gene.chromosome"])
        self.send_data("\n".join(reply_container))



    # Find a nodes relation(s)
    # Input: Node-ID plus type of relation
    # i,e. 5NB,3NB,CODING,HOMOLOG,SYNTENY
    def find_node_relations(self, user_request):
        # Connect to the project-db
        project_db_conn = self.get_project_db_connection(user_request[0])
        # Determine requested return format
        # Format is either optimized for AHGraR-cmd or AHGraR-web
        return_format = user_request[1]
        if not return_format in ["CMD", "WEB"]:
            self.send_data("-9")
            return
        # Determine node type and ID, first letter of ID determines whether node is a gene or protein
        node_type = user_request[2]
        if not node_type in ["Gene", "Protein"]:
            self.send_data("-10")
            return
        node_id = user_request[3]
        relationship_type = user_request[4]
        # Modify 5NB and 3NB to 5_NB and 3_NB
        if relationship_type == "5NB":
            relationship_type = "5_NB"
        if relationship_type == "3NB":
            relationship_type = "3_NB"
        if not relationship_type in ["5_NB", "3_NB", "CODING", "HOMOLOG", "SYNTENY"]:
            self.send_data("-12")
            return
        # Collect nodes and relationships in two lists
        gene_node_hits = {}
        gene_node_rel = []
        protein_node_hits = {}
        protein_node_rel = []
        protein_gene_node_rel = []
        # Search for a "5_NB" pr "3_NB" relationship between gene node and gene node
        if relationship_type in ["5_NB", "3_NB"]and node_type == "Gene":
            query_hits = project_db_conn.run("MATCH(gene:Gene)-[rel:`"+relationship_type+"`]->(targetGene:Gene) "
                                             "WHERE gene.geneId = {geneId} RETURN gene, rel, targetGene",
                                             {"geneId": node_id} )
            for record in query_hits:
                gene_node_hits[record["targetGene"]["geneId"]] = \
                    [record["targetGene"][item] for item in ["species", "chromosome", "contig_name", "strand",
                                                       "start", "stop", "gene_name", "gene_descr"]]
                if relationship_type == "5_NB":
                    gene_node_rel.append((record["gene"]["geneId"], "5_NB", record["targetGene"]["geneId"]))
                    gene_node_rel.append((record["targetGene"]["geneId"], "3_NB", record["gene"]["geneId"]))
                else:
                    gene_node_rel.append((record["gene"]["geneId"], "3_NB", record["targetGene"]["geneId"]))
                    gene_node_rel.append((record["targetGene"]["geneId"], "5_NB", record["gene"]["geneId"]))
        # Search for a "CODING" relationship between a gene node and a protein node
        if relationship_type == "CODING" and node_type == "Gene":
            query_hits = project_db_conn.run("MATCH(gene:Gene)-[rel:CODING]->(targetProt:Protein) "
                                             "WHERE gene.geneId = {geneId} RETURN gene, rel, targetProt",
                                             {"geneId": node_id})
            for record in query_hits:
                protein_node_hits[record["targetProt"]["proteinId"]] = \
                    [record["targetProt"]["protein_name"], record["targetProt"]["protein_descr"],
                     record["gene"]["species"], record["gene"]["chromosome"]]
                protein_gene_node_rel.append((record["gene"]["geneId"], "CODING", record["targetProt"]["proteinId"]))
        # Search for a "CODING" relationship between a protein node and a gene node
        if relationship_type == "CODING" and node_type == "Protein":
            query_hits = project_db_conn.run("MATCH(targetGene:Gene)-[rel:CODING]->(prot:Protein) "
                                             "WHERE prot.proteinId = {protId} RETURN gene, rel, prot",
                                             {"protId": node_id})
            for record in query_hits:
                gene_node_hits[record["targetGene"]["geneId"]] = \
                    [record["targetGene"][item] for item in ["species", "chromosome", "contig_name", "strand",
                                                       "start", "stop", "gene_name", "gene_descr"]]
                protein_gene_node_rel.append((record["targetGene"]["geneId"], "CODING", record["prot"]["proteinId"]))
        # Search for a "HOMOLOG" or "SYNTENY" relationship between a protein node and other protein nodes
        if relationship_type in ["HOMOLOG", "SYNTENY"] and node_type == "Protein":
            query_hits = project_db_conn.run("MATCH (prot:Protein)-[:"+relationship_type+"]->(prot_new:Protein) WHERE "
                                             "prot.proteinId = {protId} MATCH "
                                             "(gene_new:Gene)-[:CODING]->(prot_new)-[rel:"+relationship_type+"]->"
                                             "(prot_new_homolog:Protein) RETURN DISTINCT gene_new.species, "
                                             "gene_new.chromosome, prot_new, rel, prot_new_homolog.proteinId",
                                             {"protId": node_id})

            # query_hits = project_db_conn.run("MATCH(prot:Protein)-[rel:"+relationship_type+"]->(targetProt:Protein) "
            #                                  "WHERE prot.proteinId = {protId} RETURN prot, rel, targetProt",
            #                                  {"protId": node_id})
            for record in query_hits:
                protein_node_hits[record["prot_new"]["proteinId"]] = \
                    [record["prot_new"]["protein_name"], record["prot_new"]["protein_descr"],
                     record["gene_new.species"], record["gene_new.chromosome"]]
                protein_node_rel.append((record["prot_new"]["proteinId"], record["rel"].type,
                                         record["rel"]["sensitivity"], record["prot_new_homolog.proteinId"]))
        # Reformat the node and edge data for either AHGraR-web or AHGraR-cmd
        if return_format == "CMD":
            self.send_data_cmd(gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
                               protein_gene_node_rel)
        else:
            self.send_data_web(gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
                               protein_gene_node_rel)
        # Close connection to the project-db
        project_db_conn.close()

    # Reformat node and edge data to fit the format expected by AHGraR-cmd
    def send_data_cmd(self, gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
     protein_gene_node_rel):
        # Transfer gene node and protein node dicts into list structures
        # Sort gene node list by species,chromosome, contig, start
        gene_node_hits = [[item[0]] + item[1] for item in gene_node_hits.items()]
        gene_node_hits.sort(key=lambda x: (x[1], x[2], x[3], x[5]))
        protein_node_hits = [[item[0]] + item[1] for item in protein_node_hits.items()]
        # Build return string
        reply = "Gene node(s):\n"
        for gene_node in gene_node_hits:
            reply += "\t".join(str(x) for x in gene_node) + "\n"
        reply += "Protein node(s):\n"
        for protein_node in protein_node_hits:
            reply += "\t".join(str(x) for x in protein_node) + "\n"
        reply += "Relations:\n"
        for gene_gene_rel in gene_node_rel:
            reply += "\t".join(str(x) for x in gene_gene_rel) + "\n"
        for prot_prot_rel in protein_node_rel:
            reply += "\t".join(str(x) for x in prot_prot_rel) + "\n"
        for gene_prot_rel in protein_gene_node_rel:
            reply += "\t".join(str(x) for x in gene_prot_rel) + "\n"
        self.send_data(reply)

    # Reformat node and edge data to fit the format expected by AHGraR-web
    # Each node and each edge gets an unique and reproducible ID
    def send_data_web(self, gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
                      protein_gene_node_rel):
        # Transfer gene node and protein node dicts into list structures
        # Sort gene node list by species,chromosome, contig, start
        gene_node_hits = [[item[0]] + item[1] for item in gene_node_hits.items()]
        gene_node_hits.sort(key=lambda x: (x[1], x[2], x[3], x[5]))
        protein_node_hits = [[item[0]] + item[1] for item in protein_node_hits.items()]
        # Reformat data into json format:
        gene_node_json = ['{"data": {"id":"g' + gene_node[0] + '", "type":"Gene", "species":"' + gene_node[1] +
                          '", "chromosome":"' + gene_node[2] + '", "contig":"' + gene_node[3] + '", "strand":"' +
                          gene_node[4] +
                          '", "start":' + str(gene_node[5]) + ', "stop":' + str(gene_node[6]) + ', "name":"' +
                          gene_node[7] + '", "description":"' + gene_node[8]+ '"}}'
                          for gene_node in gene_node_hits]
        protein_node_json = ['{"data": {"id":"p' + protein_node[0] + '", "type":"Protein", "name":"' + protein_node[1] +
                             '", "description":"' + protein_node[2] +
                             '", "species":"' + protein_node[3] +
                             '", "chromosome":"' + protein_node[4] +'"}}' for protein_node in protein_node_hits]
        nodes_json = '"nodes": [' + ', '.join(gene_node_json + protein_node_json) + ']'
        gene_gene_rel_json = ['{"data": {"id":"g'+gene_gene_rel[0]+'_g'+gene_gene_rel[2]+'", "source":"g' +
                              gene_gene_rel[0] + '", "type":"' + gene_gene_rel[1] +
                              '", "target":"g' + gene_gene_rel[2] + '"}}' for gene_gene_rel in gene_node_rel]
        # Remove self-Homology loops
        protein_node_rel = [prot_prot_rel for prot_prot_rel in protein_node_rel if prot_prot_rel[0] != prot_prot_rel[3]]
        # Reduce protein-protein relations to one edge per pairwise relation
        # Always keep the relation from the lexico. smaller node to the lexico. bigger node
        # e.g., always keep p123 to p456 and always remove p456 to p123
        for rel in protein_node_rel:
            try:
                protein_node_rel.remove((rel[3], rel[1], rel[2], rel[0]))
            except ValueError:
                continue
        protein_protein_rel_json = ['{"data": {"id":"p'+prot_prot_rel[0]+'_'+prot_prot_rel[1]+prot_prot_rel[2]+'_p'+prot_prot_rel[3]+'", "source":"p' +
                                    prot_prot_rel[0] + '", "type":"' + prot_prot_rel[1] +
                                    '", "sensitivity":"' + prot_prot_rel[2] + '", "target":"p' + prot_prot_rel[
                                        3] + '"}}'
                                    for prot_prot_rel in protein_node_rel]
        gene_protein_rel_json = ['{"data": {"id":"g'+prot_gene_rel[0]+'_p'+prot_gene_rel[2]+'", "source":"g' + prot_gene_rel[0] + '", "type":"CODING", "target":"p' +
                                 prot_gene_rel[2] + '"}}' for prot_gene_rel in protein_gene_node_rel]
        edges_json = '"edges": [' + ', '.join(
            gene_gene_rel_json + protein_protein_rel_json + gene_protein_rel_json) + ']'
        self.send_data('{' + nodes_json + ',' + edges_json + '}')



    #Find node(s) based on search terms
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
        # Also replace any question marks with "" as question marks are used in the project graph db
        # to represent missing data, i.e. could cause false hits
        query_term = [item.strip().replace("\t", "_").replace("?", "") for item in user_request[2:]]
        # Replace * placeholders with empty string
        query_term = [item if item != "*" else "" for item in query_term]

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
        if query_type not in ["gene", "prot", "both"]:
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
        # Gene nodes are matched by species, chromosome location and a keyword that is searched against in
        # gene name and gene description
        if query_type in ["gene", "both"]:
            # query_hits = project_db_conn.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
            #                                  "AND LOWER(gene.chromosome) CONTAINS {query_chromosome} "
            #                                  "AND (LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
            #                                  "LOWER(gene.gene_descr) CONTAINS {query_keyword}) WITH COLLECT(gene) AS "
            #                                  "genes UNWIND genes AS g1 UNWIND genes AS g2 "
            #                                  "OPTIONAL MATCH (g1)-[rel]->(g2) RETURN g1,rel,g2",
            #                                  {"query_species": query_species, "query_keyword": query_keyword,
            #                                   "query_chromosome": query_chromosome, "query_anno": query_keyword})
            query_hits = project_db_conn.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
                                             "AND LOWER(gene.chromosome) CONTAINS {query_chromosome} "
                                             "AND (LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
                                             "LOWER(gene.gene_descr) CONTAINS {query_keyword}) "
                                             "OPTIONAL MATCH (gene)-[rel]->(gene_nb:Gene) RETURN gene,rel,gene_nb",
                                             {"query_species": query_species, "query_keyword": query_keyword,
                                              "query_chromosome": query_chromosome})
            # The record format lists every node matching the query together with one relationship to another gene node.
            # Multiple relationships are split into separate rows, e.g. row 1 contains the 5` relation of g1 with g2,
            # row 2 contains the 3` relation of g1 with g3. If there is no gene-gene relationship going out from g1
            # there is only one unique row for g1 with rel= None.
            # First column is gene node 1, third is gene node 2 and the middle column is the relationship between
            # g1 and g2. This relationship can be None, i.e. there is no relationship.
            # The overall set of matching gene nodes is extracted from column 1 and stored in a dict to enforce
            # uniqueness.
            for record in query_hits:
                gene_node_hits[record["gene"]["geneId"]] = \
                    [record["gene"][item] for item in ["species", "chromosome", "contig_name", "strand",
                                                       "start", "stop", "gene_name", "gene_descr"]]
                if record["rel"] is not None:
                    gene_node_rel.append((record["gene"]["geneId"], record["rel"].type, record["gene_nb"]["geneId"]))
        # Search for protein nodes and protein-protein relationships
        # Proteins are always coded for by genes. The keyword query is matched against the protein name and
        # the protein description. Species and chromosome information is retrieved from the gene node.
        # As for genes, for every matched node all its relations are returned in a separate row (if there are no
        # relations there will be a single row with rel=None)
        # Matched protein nodes are initially stored in a dict to enforce uniqueness
        # Query also returns information about the species and the chromosome coding for this protein
        if query_type in ["prot", "both"]:
            # query_hits = project_db_conn.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
            #                                  "CONTAINS {query_species} AND (LOWER(prot.protein_name) CONTAINS "
            #                                  "{query_keyword} OR LOWER(prot.protein_descr) CONTAINS {query_keyword} "
            #                                  ") WITH "
            #                                  "COLLECT(prot) AS prots UNWIND prots as p1 UNWIND prots as p2 "
            #                                  "OPTIONAL MATCH (p1)-[rel]->(p2) RETURN p1,rel,p2",
            #                                  {"query_species":query_species, "query_keyword":query_keyword})
            query_hits = project_db_conn.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
                                             "CONTAINS {query_species} AND LOWER(gene.chromosome) CONTAINS "
                                             "{query_chromosome} AND (LOWER(prot.protein_name) CONTAINS "
                                             "{query_keyword} OR LOWER(prot.protein_descr) CONTAINS {query_keyword}) "
                                             "OPTIONAL MATCH (prot)-[rel]->(prot_nb:Protein) "
                                             "RETURN prot,rel,prot_nb,gene.species,gene.chromosome",
                                             {"query_species": query_species, "query_keyword": query_keyword,
                                              "query_chromosome": query_chromosome})
            for record in query_hits:
                protein_node_hits[record["prot"]["proteinId"]] = \
                    [record["prot"]["protein_name"], record["prot"]["protein_descr"],
                     record["gene.species"], record["gene.chromosome"]]
                # Check if protein p1 has a relationship to protein p2
                # Possible types of relationship: HOMOLOG or SYNTENY,
                # both with the additional attribute "sensitivity" (of clustering)
                if record["rel"] is not None:
                    protein_node_rel.append((record["prot"]["proteinId"], record["rel"].type,
                                             record["rel"]["sensitivity"], record["prot_nb"]["proteinId"]))


        # Search for gene-protein relationships (only if looking for both protein and gene nodes)
        # i.e. relations between both gene and protein nodes found above (which can only be CODING relations)
        # Since both genes and proteins need to be found, it is sufficient that the species term and the gene_name
        # term are found (the search for protein nodes also checks the gene_name of the coding gene)
        if query_type == "both":
            # query_hits = project_db_conn.run("MATCH coding_path = (gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
            #                                  "CONTAINS {query_species} AND (LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
            #                                  "LOWER(gene.gene_descr)  CONTAINS {query_keyword} )"
            #                                  "RETURN gene.geneId, prot.proteinId",
            #                                  {"query_species": query_species, "query_keyword": query_keyword})
            query_hits = project_db_conn.run("MATCH coding_path = (gene:Gene)-[:CODING]->(prot:Protein) "
                                             "WHERE LOWER(gene.species) CONTAINS {query_species} "
                                             "AND LOWER(gene.chromosome) CONTAINS {query_chromosome} AND "
                                             "(LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
                                             "LOWER(gene.gene_descr)  CONTAINS {query_keyword}) AND "
                                             "(LOWER(prot.protein_name) CONTAINS {query_keyword} OR "
                                             "LOWER(prot.protein_descr) CONTAINS {query_keyword}) "
                                             "RETURN gene.geneId, prot.proteinId",
                                             {"query_species": query_species, "query_chromosome": query_chromosome,
                                              "query_keyword": query_keyword})
            for record in query_hits:
                protein_gene_node_rel.append((record["gene.geneId"], "CODING", record["prot.proteinId"]))
        print("Gene nodes: "+str(len(gene_node_hits)))
        print("Protein nodes: "+str(len(protein_node_hits)))
        print("Gene-gene relations: "+str(len(gene_node_rel)))
        print("Prot-prot relations: "+str(len(protein_node_rel)))
        print("Gene-prot relations: "+str(len(protein_gene_node_rel)))
        # Reformat the node and edge data for either AHGraR-web or AHGraR-cmd
        if return_format == "CMD":
            self.send_data_cmd(gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
                               protein_gene_node_rel)
        else:
            self.send_data_web(gene_node_hits, protein_node_hits, gene_node_rel, protein_node_rel,
                               protein_gene_node_rel)
        # Close connection to the project-db
        project_db_conn.close()
