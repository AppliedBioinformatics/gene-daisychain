# Provides database query functionality to Daisychain-server
# Connects to a project-specific graphDB (not the Main-DB!)
# This database can only by accessed from localhost on the server-side
# User name is neo4j, the password is stored in file "access" in project folder
# Class returns query results as returned by cypher without much editing
# Any postprocessing is performed by Daisychain-cmd or Daisychain-web
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
import subprocess


class QueryManagement:
    def __init__(self,  main_db_driver, send_data, ahgrar_config):
        self.main_db_driver = main_db_driver
        self.send_data = send_data
        self.ahgrar_config = ahgrar_config

    # Establish a connection to project-specific graph db
    def get_project_db_driver(self, proj_id):
        # Retrieve bolt port nr from main-db
        # Project is either identified by unique ID (easy) or
        # by matching project name to a search term (still easy)
        if proj_id.isdigit():
            with self.main_db_driver.session() as session_a:
                bolt_port = session_a.run("MATCH(proj:Project) WHERE ID(proj)={proj_id} "
                                                   "RETURN proj.bolt_port",{"proj_id": int(proj_id)}).single()[0]
        else:
            with self.main_db_driver.session() as session_b:
                bolt_port = session_b.run("MATCH(proj:Project) WHERE LOWER(proj.name) contains LOWER({proj_id}) "
                                              "RETURN proj.bolt_port LIMIT(1)", {"proj_id": str(proj_id.strip())}).single()[0]
        with open(os.path.join("Projects", str(proj_id), "access"), "r") as pw_file:
            bolt_pw = pw_file.read()
        project_db_driver = GraphDatabase.driver("bolt://localhost:" + str(bolt_port),
                                      auth=("neo4j", bolt_pw))
        return project_db_driver





    # React to request send from a user app
    # User_request is a list of the "_" split command
    # e.g. [SEAR, ProjectID, Organism:Chromosome:Name:Annotation:Gene/Protein(Both]
    def evaluate_user_request(self, user_request):
        print('user request is %s'%user_request)
        if user_request[0] == "SEAR" and user_request[1].isdigit() and len(user_request) == 7 \
                and user_request[6] != "BLAST":
            self.find_node(user_request[1:])
        elif user_request[0] == "SEAR" and user_request[1].isdigit() and len(user_request) == 8 \
                and user_request[-1] == "BLAST":
            self.blast(user_request[1:])
        elif user_request[0] == "RELA" and user_request[1].isdigit() and len(user_request) == 5:
            self.find_node_relations(user_request[1:])
        elif user_request[0] == "LIST" and user_request[1].isdigit() and 3 <=len(user_request) <= 4:
            self.list_items(user_request[1:])
        else:
            self.send_data("-8")

    # BLAST a protein sequence against the project-specific BLAST protein database
    # to find matching proteins
    # 1. Blast
    # 2. Retrieve list of hits
    # 3. Filter for target organisms (one or all)
    # 4. Retrieve nodes for hits + their relations
    # 5. Return
    def blast(self, user_request):
        user_request = [item.replace("\t", "_") for item in user_request]
        print('in blast, user request is ' , user_request)
        proj_id = user_request[0]
        return_format = user_request[1]
        if not return_format in ["CMD", "WEB"]:
            self.send_data("-9")
            return
        query_species = user_request[2] if user_request[2] != "*" else ""
        print('query species is', query_species)
        query_contig = user_request[3] if user_request[3] != "*" else ""
        print('query contig is', query_contig)
        evalue = user_request[4]
        query_seq = user_request[5].upper().split('\n')
        # do we have an ID line in this?
        newq = []
        for subseq in query_seq:
            if '>' in subseq: continue
            newq.append(subseq)
        query_seq = ''.join(newq)
        print('query seq is', query_seq)
        BlastDB_path = os.path.join("Projects", str(proj_id), "BlastDB")
        cpu_cores = self.ahgrar_config["Daisychain_Server"]["cpu_cores"]
        project_db_driver = self.get_project_db_driver(proj_id)
        # Detect whether we are dealing with a nucleotide or protein sequence
        is_nucleotide = True
        for res in query_seq:
            if res not in ["A","C","G","T","U"]:
                is_nucleotide = False
                break
        # Write sequence to temp. file
        with open(os.path.join(BlastDB_path, "query_seq.faa"), "w") as tmp_fasta_file:
            tmp_fasta_file.write(">query_seq\n" + query_seq)
        if is_nucleotide:
            blastn_path = os.path.join(self.ahgrar_config["Daisychain_Server"]["blast+_path"], "blastn")
            subprocess.run([blastn_path, "-query", os.path.join(BlastDB_path, "query_seq.faa"), "-db",
                            os.path.join(BlastDB_path, "transcript_db"), "-outfmt", "6 sseqid",
                            "-out", os.path.join(BlastDB_path, "query_res.tab"), "-evalue", evalue,
                            "-num_threads", cpu_cores, "-parse_deflines"])
            with open(os.path.join(BlastDB_path, "query_res.tab"), "r") as tmp_res_file:
                gene_ids = ["g"+line.strip().lower() for line in tmp_res_file]
            print("Query species: "+query_species)
            print("GeneIds: "+str(gene_ids[:20]))
            print("Contig: "+query_contig)
            with project_db_driver.session() as session_a:
                query_hits = session_a.run(
                    "MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
                    "AND LOWER(gene.contig) CONTAINS {query_contig} "
                    "AND LOWER(gene.geneId) in {gene_id_list} "
                    "OPTIONAL MATCH (gene)-[rel]->(gene_nb:Gene) RETURN gene,rel,gene_nb",
                    {"query_species": query_species.lower(), "gene_id_list": gene_ids[:20],
                     "query_contig": query_contig.lower()})
        else: # If not nucleotide i.e. proteins eq
            blastp_path = os.path.join(self.ahgrar_config["Daisychain_Server"]["blast+_path"], "blastp")
            subprocess.run([blastp_path, "-query", os.path.join(BlastDB_path, "query_seq.faa"), "-db",
                            os.path.join(BlastDB_path, "translation_db"), "-outfmt", "6 sseqid",
                            "-out", os.path.join(BlastDB_path, "query_res.tab"), "-evalue", evalue,
                            "-num_threads", cpu_cores, "-parse_deflines"])
            with open(os.path.join(BlastDB_path, "query_res.tab"), "r") as tmp_res_file:
                protein_ids = ["p"+line.strip().lower() for line in tmp_res_file]
            with project_db_driver.session() as session_b:
                query_hits = session_b.run(
                    "MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) CONTAINS {query_species} "
                    "AND LOWER(gene.contig) CONTAINS {query_contig} "
                    "AND LOWER(prot.proteinId) in {prot_id_list} "
                    "OPTIONAL MATCH (gene)-[rel]->(gene_nb:Gene) RETURN gene,rel,gene_nb",
                    {"query_species": query_species.lower(), "prot_id_list": protein_ids[:20],
                     "query_contig": query_contig.lower()})

        gene_node_hits = {}
        gene_node_nb_rel = []
        gene_node_hmlg_rel = []
        for record in query_hits:
            gene_node_hits[record["gene"]["geneId"]] = \
                [record["gene"][item] for item in ["species", "contig",
                                                   "start", "stop", "name", "descr", "nt_seq"]]
            if record["rel"] is not None:
                if record["rel"].type in ["5_NB", "3_NB"]:
                    gene_node_nb_rel.append(
                        (record["gene"]["geneId"], record["rel"].type, record["gene_nb"]["geneId"]))
                elif record["rel"].type == "HOMOLOG":
                    gene_node_hmlg_rel.append(
                        (record["gene"]["geneId"], record["rel"].type, record["rel"]["clstr_sens"],
                         record["rel"]["perc_match"], record["gene_nb"]["geneId"]))
        print("Gene nodes: " + str(len(gene_node_hits)))
        print("Gene-gene NB relations: " + str(len(gene_node_nb_rel)))
        print("Gene-gene hmlg relations: " + str(len(gene_node_hmlg_rel)))
        # Reformat the node and edge data for either Daisychain-web or Daisychain-cmd
        # Close connection to the project-db
        project_db_driver.close()
        if return_format == "CMD":
            self.send_data_cmd(gene_node_hits, {}, gene_node_nb_rel, gene_node_hmlg_rel, [],
                               [])
        else:
            self.send_data_web(gene_node_hits, {}, gene_node_nb_rel, gene_node_hmlg_rel, [],
                               [])



    # List properties of data stored in project db:
    # 1. List all species in a project
    # 2. List chromsome labels of one or all species in a project
    def list_items(self, user_request):
        # Connect to the project-db
        project_db_driver = self.get_project_db_driver(user_request[0])
        # Init the return value container
        reply_container = []
        if user_request[1] == "SPECIES":
            with project_db_driver.session() as session_c:
                query_hits = session_c.run("MATCH(gene:Gene) RETURN DISTINCT gene.species ORDER BY gene.species")
            for record in query_hits:
                reply_container.append(record["gene.species"])
        if user_request[1] == "CONTIG" and 2 <= len(user_request) <= 3:
            # If no species was defined, return the distinct chromosome names of all species
            # Else return only the chromosomes of the selected species
            # Replace any tabs in species name with underscores
            if len(user_request) == 2:
                with project_db_driver.session() as session_d:
                    query_hits = session_d.run("MATCH (gene:Gene)  RETURN DISTINCT gene.contig "
                                                     "ORDER BY gene.contig")
            if len(user_request) == 3 and user_request[2]=="*":
                with project_db_driver.session() as session_e:
                    query_hits = session_e.run("MATCH (gene:Gene)  RETURN DISTINCT gene.contig "
                                                     "ORDER BY gene.contig")
            elif len(user_request) == 3:
                with project_db_driver.session() as session_f:
                    query_hits = session_f.run("MATCH (gene:Gene)  WHERE gene.species = {species_name} RETURN "
                                                     "DISTINCT gene.contig ORDER BY gene.contig",
                                                      {"species_name":user_request[2].replace("\t", "_")})
            else:
                query_hits = []
            for record in query_hits:
                reply_container.append(record["gene.contig"])
        self.send_data("\n".join(reply_container))



    # Find a nodes relation(s)
    # Input:ProjectID_CMD/WEB_NodeID_Relationship
    def find_node_relations(self, user_request):
        # Connect to the project-db
        project_db_driver = self.get_project_db_driver(user_request[0])
        # Determine requested return format
        # Format is either optimized for Daisychain-cmd or Daisychain-web
        return_format = user_request[1]
        if not return_format in ["CMD", "WEB"]:
            self.send_data("-9")
            return
        # Determine node type and ID, first letter of ID determines whether node is a gene or protein
        if not user_request[2][0] in ["g","p"]:
            self.send_data("-10")
            return
        else:
            node_type = "Gene" if user_request[2][0]=="g" else "Protein"
        node_id = user_request[2]
        relationship_type = user_request[3]
        # Modify 5NB and 3NB to 5_NB and 3_NB
        if relationship_type == "5NB":
            relationship_type = "5_NB"
        if relationship_type == "3NB":
            relationship_type = "3_NB"
        if not relationship_type in ["5_NB", "3_NB", "HOMOLOG", "CODING", "53NB"]:
            self.send_data("-12")
        # Collect nodes and relationships in two lists
        gene_node_hits = {}
        protein_node_hits = {}
        gene_node_nb_rel = []
        gene_node_hmlg_rel = []
        protein_node_hmlg_rel = []
        gene_protein_coding_rel = []

        # Retrieve gene coding for a protein
        if relationship_type == "CODING" and node_type == "Protein":
            with project_db_driver.session() as session_g:
                query_hits = session_g.run("MATCH(coding_gene:Gene)-[:CODING]->(prot:Protein) WHERE prot.proteinId={protId} "
                                             "OPTIONAL MATCH (coding_gene)-[gen_Rel]->(geneRel:Gene) "
                                             "RETURN  coding_gene, gen_Rel, geneRel.geneId",
                                             {"protId": node_id})
            for record in query_hits:
                gene_node_hits[record["coding_gene"]["geneId"]] = \
                    [record["coding_gene"][item] for item in ["species", "contig",
                                                   "start", "stop", "name", "descr", "nt_seq"]]
                if (record["coding_gene"]["geneId"], "CODING", node_id) not in gene_protein_coding_rel:
                    gene_protein_coding_rel.append((record["coding_gene"]["geneId"], "CODING", node_id))
                try:
                    coding_gene_rel = record["gen_Rel"].type
                except:
                    coding_gene_rel = "None"
                if coding_gene_rel == "5_NB":
                    gene_node_nb_rel.append(
                        (record["coding_gene"]["geneId"], "5_NB", record["geneRel.geneId"]))
                    gene_node_nb_rel.append(
                        (record["geneRel.geneId"], "3_NB", record["coding_gene"]["geneId"]))
                if coding_gene_rel == "3_NB":
                    gene_node_nb_rel.append(
                        (record["coding_gene"]["geneId"], "3_NB", record["geneRel.geneId"]))
                    gene_node_nb_rel.append(
                        (record["geneRel.geneId"], "5_NB", record["coding_gene"]["geneId"]))
                if coding_gene_rel == "HOMOLOG":
                    gene_node_hmlg_rel.append((record["coding_gene"]["geneId"],
                                               "HOMOLOG",
                                               record["gen_Rel"]["clstr_sens"],
                                               record["gen_Rel"]["perc_match"],
                                               record["geneRel.geneId"]))
                    gene_node_hmlg_rel.append((record["geneRel.geneId"],
                                               "HOMOLOG",
                                               record["gen_Rel"]["clstr_sens"],
                                               record["gen_Rel"]["perc_match"],
                                               record["coding_gene"]["geneId"]))

        # Retrieve protein coded by gene
        if relationship_type == "CODING" and node_type == "Gene":
            with project_db_driver.session() as session_h:
                query_hits = session_h.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE gene.geneId={geneId} "
                                             "OPTIONAL MATCH (prot)-[hmlg_rel:HOMOLOG]->(protH) "
                                             "RETURN  gene.species, gene.name, prot, hmlg_rel, protH.proteinId",
                                             {"geneId": node_id})
            for record in query_hits:
                protein_node_hits[record["prot"]["proteinId"]] = [record["prot"]["prot_seq"], record["gene.species"],
                                                                  record["gene.name"]]
                if (node_id, "CODING", record["prot"]["proteinId"]) not in gene_protein_coding_rel:
                    gene_protein_coding_rel.append((node_id, "CODING", record["prot"]["proteinId"]))
                try:
                    rel_type = record["hmlg_rel"].type
                except:
                    rel_type = "None"
                if rel_type == "HOMOLOG":
                    protein_node_hmlg_rel.append((record["prot"]["proteinId"],
                                               "HOMOLOG",
                                               record["hmlg_rel"]["clstr_sens"],
                                               record["hmlg_rel"]["perc_match"],
                                               record["protH.proteinId"]))
                    protein_node_hmlg_rel.append((record["protH.proteinId"],
                                               "HOMOLOG",
                                               record["hmlg_rel"]["clstr_sens"],
                                               record["hmlg_rel"]["perc_match"],
                                               record["prot"]["proteinId"]))



        # Search for a "5_NB" pr "3_NB" relationship between gene node and gene node
        if relationship_type in ["53NB"] and node_type == "Gene":
            for reltype in ['3_NB', '5_NB']:
                with project_db_driver.session() as session_i:
                    query_hits = session_i.run("MATCH(gene:Gene)-[rel:`"+reltype+"`]->(targetGene:Gene) "
                                                "WHERE gene.geneId = {geneId} "
                                                "OPTIONAL MATCH (targetGene)-[targetGene_rel]->(secondary_node) "
                                                "RETURN gene, rel, targetGene, targetGene_rel, "
                                                "secondary_node.geneId, secondary_node.proteinId",
                                                {"geneId": node_id} )
                for record in query_hits:
                    gene_node_hits[record["targetGene"]["geneId"]] = \
                        [record["targetGene"][item] for item in ["species", "contig",
                                                    "start", "stop", "name", "descr", "nt_seq"]]
                    if reltype == "5_NB":
                        gene_node_nb_rel.append((record["gene"]["geneId"], "5_NB", record["targetGene"]["geneId"]))
                        #gene_node_nb_rel.append((record["targetGene"]["geneId"], "3_NB", record["gene"]["geneId"]))
                    else:
                        gene_node_nb_rel.append((record["gene"]["geneId"], "3_NB", record["targetGene"]["geneId"]))
                        #gene_node_nb_rel.append((record["targetGene"]["geneId"], "5_NB", record["gene"]["geneId"]))
                    # Now add secondary relations of new nodes to list of relations

                    try:
                        target_gene_rel_type = record["targetGene_rel"].type
                    except:
                        target_gene_rel_type = "None"
                    if target_gene_rel_type == "5_NB":
                        gene_node_nb_rel.append(
                            (record["targetGene"]["geneId"], "5_NB", record["secondary_node.geneId"]))
                        gene_node_nb_rel.append(
                            (record["secondary_node.geneId"], "3_NB", record["targetGene"]["geneId"]))
                    if target_gene_rel_type == "3_NB":
                        gene_node_nb_rel.append(
                            (record["targetGene"]["geneId"], "3_NB", record["secondary_node.geneId"]))
                        gene_node_nb_rel.append(
                            (record["secondary_node.geneId"], "5_NB", record["targetGene"]["geneId"]))
                    if target_gene_rel_type == "HOMOLOG":
                        gene_node_hmlg_rel.append((record["targetGene"]["geneId"],
                                                "HOMOLOG",
                                                record["targetGene_rel"]["clstr_sens"],
                                                record["targetGene_rel"]["perc_match"],
                                                record["secondary_node.geneId"]))
                        gene_node_hmlg_rel.append((record["secondary_node.geneId"],
                                                "HOMOLOG",
                                                record["targetGene_rel"]["clstr_sens"],
                                                record["targetGene_rel"]["perc_match"],
                                                record["targetGene"]["geneId"]))
                    if target_gene_rel_type == "CODING":
                        gene_protein_coding_rel.append((record["targetGene"]["geneId"],
                                                        "CODING",
                                                        record["secondary_node.proteinId"]))

        # # Search for a "CODING" relationship between a gene node and a protein node
        # if relationship_type == "CODING" and node_type == "Gene":
        #     query_hits = project_db_driver.run("MATCH(gene:Gene)-[rel:CODING]->(targetProt:Protein) "
        #                                      "WHERE gene.geneId = {geneId} RETURN gene, rel, targetProt",
        #                                      {"geneId": node_id})
        #     for record in query_hits:
        #         protein_node_hits[record["targetProt"]["proteinId"]] = \
        #             [record["targetProt"]["protein_name"], record["targetProt"]["protein_descr"],
        #              record["gene"]["species"], record["gene"]["chromosome"]]
        #         protein_gene_node_rel.append((record["gene"]["geneId"], "CODING", record["targetProt"]["proteinId"]))
        # # Search for a "CODING" relationship between a protein node and a gene node
        # if relationship_type == "CODING" and node_type == "Protein":
        #     query_hits = project_db_driver.run("MATCH(targetGene:Gene)-[rel:CODING]->(prot:Protein) "
        #                                      "WHERE prot.proteinId = {protId} RETURN targetGene, rel, prot",
        #                                      {"protId": node_id})
        #     for record in query_hits:
        #         gene_node_hits[record["targetGene"]["geneId"]] = \
        #             [record["targetGene"][item] for item in ["species", "chromosome", "contig_name", "strand",
        #                                                "start", "stop", "gene_name", "gene_descr"]]
        #         protein_gene_node_rel.append((record["targetGene"]["geneId"], "CODING", record["prot"]["proteinId"]))
        # Search for a "HOMOLOG" or "SYNTENY" relationship between a protein node and other protein nodes

        # Retrieve all homologs for a certain Protein ID. Include all relations going out from each homolog gene, i.e.
        # all HOMOLOG and all CODING edges.
        if relationship_type == "HOMOLOG" and node_type == "Protein":
            with project_db_driver.session() as session_j:
                query_hits = session_j.run("MATCH(protein:Protein)-[rel:HOMOLOG]->(protH:Protein)<-[:CODING]-(geneH:Gene) "
                                             "WHERE protein.proteinId = {protId} "
                                             "OPTIONAL MATCH (protH)-[secRel]-(secNode) "
                                             "RETURN rel, protH, geneH.species, geneH.name, "
                                             "secRel, secNode.geneId, secNode.proteinId", {"protId": node_id})
            for record in query_hits:
                try:
                    rel_type = record["rel"].type
                except:
                    rel_type = "None"
                if rel_type == "HOMOLOG":
                    # Don't add the node for which we are searching homologs to the list of nodes
                    if record["protH"]["proteinId"] != node_id:
                        protein_node_hits[record["protH"]["proteinId"]] = \
                            [record["protH"]["prot_seq"], record["geneH.species"], record["geneH.name"]]
                    protein_node_hmlg_rel.append(
                        (node_id, rel_type, record["rel"]["clstr_sens"],
                         record["rel"]["perc_match"], record["protH"]["proteinId"]))
                # Analyse relation going out from this homologeous protein
                try:
                    relNode_rel_type = record["secRel"].type
                except:
                    relNode_rel_type = "None"
                if relNode_rel_type == "HOMOLOG":
                    protein_node_hmlg_rel.append((record["protH"]["proteinId"],
                                               "HOMOLOG",
                                               record["secRel"]["clstr_sens"],
                                               record["secRel"]["perc_match"],
                                               record["secNode.proteinId"]))
                    protein_node_hmlg_rel.append((record["secNode.proteinId"],
                                               "HOMOLOG",
                                               record["secRel"]["clstr_sens"],
                                               record["secRel"]["perc_match"],
                                               record["protH"]["proteinId"]))
                if relNode_rel_type == "CODING":
                    gene_protein_coding_rel.append((record["secNode.geneId"],
                                                    "CODING",
                                                    record["protH"]["proteinId"]))


        #  Retrieve all homologs of a certain Gene-ID. Include all relations going out from each homolog gene. Also
        # include each relation of the Gene-ID as there might be new 5 or 3 prime relations with the extended set of
        # genes. We therefore search for all Gene nodes related to our node of interest but return only homologeous gene
        # nodes but all possible relations. For each new gene we also retrieve the complete set of relations, incl.
        # CODING to proteins.
        if relationship_type =="HOMOLOG" and node_type == "Gene":
            with project_db_driver.session() as session_k:
                 query_hits = session_k.run("MATCH (gene:Gene)-[rel]->(relNode:Gene) WHERE "
                                             "gene.geneId = {geneId} "
                                             "OPTIONAL MATCH (relNode)-[relNode_rel]->(relrelNode) "
                                             "RETURN rel, relNode, relNode_rel, relrelNode.geneId, relrelNode.proteinId",
                                             {"geneId": node_id})

            for record in query_hits:
                try:
                    rel_type = record["rel"].type
                except:
                    rel_type = "None"
                # First retrieve the set of homologeous genes
                # and the set of HOMOLOG edges starting from this gene to all homologeous genes
                if rel_type == "HOMOLOG":
                    # Don't add the node for which we are searching homologs to the list of nodes
                    if record["relNode"]["geneId"] != node_id:
                        gene_node_hits[record["relNode"]["geneId"]] = \
                            [record["relNode"][item] for item in ["species", "contig",
                                                               "start", "stop", "name", "descr", "nt_seq"]]
                    gene_node_hmlg_rel.append(
                        (node_id, rel_type, record["rel"]["clstr_sens"],
                         record["rel"]["perc_match"], record["relNode"]["geneId"]))
                # Retrieve 5' and 3' edges starting from this gene
                if rel_type == "5_NB":
                    gene_node_nb_rel.append((node_id, "5_NB", record["relNode"]["geneId"]))
                    gene_node_nb_rel.append((record["relNode"]["geneId"], "3_NB", node_id))
                if rel_type == "3_NB":
                    gene_node_nb_rel.append((node_id, "3_NB", record["relNode"]["geneId"]))
                    gene_node_nb_rel.append((record["relNode"]["geneId"], "5_NB", node_id))
                # Analyse relation going out from this homologeous gene
                try:
                    relNode_rel_type = record["relNode_rel"].type
                except:
                    relNode_rel_type = "None"
                if relNode_rel_type == "5_NB":
                    gene_node_nb_rel.append((record["relNode"]["geneId"], "5_NB", record["relrelNode.geneId"]))
                    gene_node_nb_rel.append((record["relrelNode.geneId"], "3_NB", record["relNode"]["geneId"]))
                if relNode_rel_type == "3_NB":
                    gene_node_nb_rel.append((record["relNode"]["geneId"], "3_NB", record["relrelNode.geneId"]))
                    gene_node_nb_rel.append((record["relrelNode.geneId"], "5_NB", record["relNode"]["geneId"]))
                if relNode_rel_type == "HOMOLOG":
                    gene_node_hmlg_rel.append((record["relNode"]["geneId"],
                                               "HOMOLOG",
                                               record["relNode_rel"]["clstr_sens"],
                                               record["relNode_rel"]["perc_match"],
                                               record["relrelNode.geneId"]))
                    gene_node_hmlg_rel.append((record["relrelNode.geneId"],
                                               "HOMOLOG",
                                               record["relNode_rel"]["clstr_sens"],
                                               record["relNode_rel"]["perc_match"],
                                               record["relNode"]["geneId"]))
                if relNode_rel_type == "CODING":
                    gene_protein_coding_rel.append((record["relNode"]["geneId"],
                                                    "CODING",
                                                    record["relrelNode.proteinId"]))

        print("Gene nodes: " + str(len(gene_node_hits)))
        print("Protein nodes: "+ str(len(protein_node_hits)))
        print("Gene-gene NB relations: " + str(len(gene_node_nb_rel)))
        print("Gene-gene hmlg relations: " + str(len(gene_node_hmlg_rel)))
        print("Protein-protein hmlg relations: " + str(len(protein_node_hmlg_rel)))
        print("Gene-protein coding relations: "+str(len(gene_protein_coding_rel)))

        if return_format == "CMD":
            self.send_data_cmd(gene_node_hits, protein_node_hits, gene_node_nb_rel, gene_node_hmlg_rel, protein_node_hmlg_rel, gene_protein_coding_rel)
        else:
            self.send_data_web(gene_node_hits, protein_node_hits, gene_node_nb_rel, gene_node_hmlg_rel, protein_node_hmlg_rel, gene_protein_coding_rel)
        # Close connection to the project-db
        project_db_driver.close()

    # Reformat node and edge data to fit the format expected by Daisychain-cmd
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

    # Reformat node and edge data to fit the format expected by Daisychain-web
    # Each node and each edge gets an unique and reproducible ID
    def send_data_web(self, gene_node_hits, protein_node_hits, gene_node_nb_rel,gene_node_hmlg_rel, protein_node_hmlg_rel,
                      gene_prot_coding_rel):
        # Transfer gene node and protein node dicts into list structures
        # Sort gene node list by species,chromosome, contig, start
        gene_node_hits = [[item[0]] + item[1] for item in gene_node_hits.items()]
        gene_node_hits.sort(key=lambda x: (x[1], x[2], x[3]))
        protein_node_hits = [[item[0]] + item[1] for item in protein_node_hits.items()]
        # Reformat data into json format:
        gene_node_json = ['{"data": {"id":"' + str(gene_node[0])
                          + '", "type":"Gene", "species":"' + str(gene_node[1])
                          + '", "contig":"' + str(gene_node[2])
                          + '", "start":' + str(gene_node[3])
                          + ', "stop":' + str(gene_node[4])
                          + ', "name":"' + str(gene_node[5])
                          + '", "description":"' + str(gene_node[6])
                          + '", "nt_seq":"' + str(gene_node[7])+'"}}'
                          for gene_node in gene_node_hits]
        protein_node_json = ['{"data": {"id":"' + protein_node[0] + '", "type":"Protein", "aa_seq":"' + protein_node[1]
                             + '", "species":"' + protein_node[2] +
                             '", "name":"' + protein_node[3] +
                             '"}}' for protein_node in protein_node_hits]
        nodes_json = '"nodes": [' + ', '.join(gene_node_json+protein_node_json) + ']'
        gene_gene_nb_json = ['{"data": {"id":"'+str(rel[0])+'_'+rel[1]+"_"+str(rel[2])+'", "source":"' +
                              str(rel[0]) + '", "type":"' + str(rel[1]) +
                              '", "target":"' + str(rel[2]) + '"}}' for rel in gene_node_nb_rel]
        gene_protein_coding_json = ['{"data": {"id":"'+str(rel[0])+'_'+rel[1]+"_"+str(rel[2])+'", "source":"' +
                              str(rel[0]) + '", "type":"' + str(rel[1]) +
                              '", "target":"' + str(rel[2]) + '"}}' for rel in gene_prot_coding_rel]
        # Remove self-Homology loops
        gene_node_hmlg_rel = [gene_gene_rel for gene_gene_rel in gene_node_hmlg_rel if gene_gene_rel[0] != gene_gene_rel[4]]
        #protein_node_rel = [prot_prot_rel for prot_prot_rel in protein_node_rel if prot_prot_rel[0] != prot_prot_rel[3]]
        # Reduce protein-protein relations to one edge per pairwise relation
        # Always keep the relation from the lexico. smaller node to the lexico. bigger node
        # e.g., always keep p123 to p456 and always remove p456 to p123
        gene_node_hmlg_rel_unidirectional = []
        for rel in gene_node_hmlg_rel:
            if int(rel[0][1:]) < int(rel[4][1:]):
                gene_node_hmlg_rel_unidirectional.append(rel)
        gene_gene_hmlg_rel_json = ['{"data": {"id":"'+str(gene_gene_rel[0])+'_'+str(gene_gene_rel[1])+str(gene_gene_rel[2])+'_'+str(gene_gene_rel[4])+'", "source":"' +
                                   str(gene_gene_rel[0]) + '", "type":"' + str(gene_gene_rel[1]) +
                                    '", "sensitivity":"' + str(gene_gene_rel[2]) +
                                   '", "perc_match":"' + str(gene_gene_rel[3]) +
                                   '", "target":"' + str(gene_gene_rel[
                                        4]) + '"}}'
                                    for gene_gene_rel in gene_node_hmlg_rel_unidirectional]
        # Do the same for protein-protein hmlg relations
        # Remove self-Homology loops
        protein_node_hmlg_rel = [prot_prot_rel for prot_prot_rel in protein_node_hmlg_rel if
                                 prot_prot_rel[0] != prot_prot_rel[4]]
        protein_node_hmlg_rel_unidirectional = []
        for rel in protein_node_hmlg_rel:
            if int(rel[0][1:]) < int(rel[4][1:]):
                protein_node_hmlg_rel_unidirectional.append(rel)
        prot_prot_hmlg_rel_json = ['{"data": {"id":"' + str(prot_prot_rel[0]) + '_' + str(prot_prot_rel[1]) + str(
            prot_prot_rel[2]) + '_' + str(prot_prot_rel[4]) + '", "source":"' +
                                   str(prot_prot_rel[0]) + '", "type":"' + str(prot_prot_rel[1]) +
                                   '", "sensitivity":"' + str(prot_prot_rel[2]) +
                                   '", "perc_match":"' + str(prot_prot_rel[3]) +
                                   '", "target":"' + str(prot_prot_rel[
                                                             4]) + '"}}'
                                   for prot_prot_rel in protein_node_hmlg_rel_unidirectional]



        # protein_protein_rel_json = [
        #     '{"data": {"id":"p' + prot_prot_rel[0] + '_' + prot_prot_rel[1] + prot_prot_rel[2] + '_p' + prot_prot_rel[
        #         3] + '", "source":"p' +
        #     prot_prot_rel[0] + '", "type":"' + prot_prot_rel[1] +
        #     '", "sensitivity":"' + prot_prot_rel[2] + '", "target":"p' + prot_prot_rel[
        #         3] + '"}}'
        #     for prot_prot_rel in protein_node_rel]
        # gene_protein_rel_json = ['{"data": {"id":"g'+prot_gene_rel[0]+'_p'+prot_gene_rel[2]+'", "source":"g' + prot_gene_rel[0] + '", "type":"CODING", "target":"p' +
        #                          prot_gene_rel[2] + '"}}' for prot_gene_rel in protein_gene_node_rel]
        edges_json = '"edges": [' + ', '.join(
            gene_gene_nb_json + gene_gene_hmlg_rel_json+gene_protein_coding_json+prot_prot_hmlg_rel_json) + ']'
        self.send_data('{' + nodes_json + ',' + edges_json + '}')



    #Find node(s) based on search terms
    def find_node(self, user_request):
        # Connect to the project-db
        project_db_driver = self.get_project_db_driver(user_request[0])
        # Determine requested return format
        # Format is either optimized for Daisychain-cmd or Daisychain-web
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

        # Check if query term has expected length: ["Organism", "Chromosome", "Keyword"]
        # Fields can be left empty, i.e. being ""
        # Keyword looks in both gene/protein name and gene/protein annotation
        if len(query_term) != 4:
            self.send_data("-10")
            return
        # Species name or gene/protein name to query for can be empty
        query_species = str(query_term[0]).lower()
        query_contig = str(query_term[1]).lower()
        # Separate keywords by whitespace
        query_keyword = str(query_term[2]).lower().split(" ")
        # Remove keywords that are empty, i.e. ""
        print("Keyword before: "+str(query_keyword))
        query_keyword = [item for item in query_keyword if item]
        print("Keyword after: "+str(query_keyword))
        match_all_any = str(query_term[3]).upper()
        # If there are no query keywords, set match_all_any to "none"
        if len(query_keyword)==0:
            match_all_any = "none"
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
        gene_node_nb_rel = []
        gene_node_hmlg_rel = []
        #protein_node_hits = {}
        #protein_node_rel = []
        #protein_gene_node_rel = []
        # Search for gene node(s) and gene-gene relationships
        # Gene nodes are matched by species, chromosome location and a keyword that is searched against in
        # gene name and gene description

            # query_hits = project_db_driver.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
            #                                  "AND LOWER(gene.chromosome) CONTAINS {query_chromosome} "
            #                                  "AND (LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
            #                                  "LOWER(gene.gene_descr) CONTAINS {query_keyword}) WITH COLLECT(gene) AS "
            #                                  "genes UNWIND genes AS g1 UNWIND genes AS g2 "
            #                                  "OPTIONAL MATCH (g1)-[rel]->(g2) RETURN g1,rel,g2",
            #                                  {"query_species": query_species, "query_keyword": query_keyword,
            #                                   "query_chromosome": query_chromosome, "query_anno": query_keyword}) #ALL(x in ["conserve"] WHERE gene.descr contains x)
        # Each term in keyword has to match in either description or name
        if match_all_any == "ALL":
            with project_db_driver.session() as session_a:
                query_hits = session_a.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
                                                 "AND LOWER(gene.contig) CONTAINS {query_contig} "
                                                 "AND (ALL(term in {query_keyword} WHERE LOWER(gene.name) CONTAINS term) OR "
                                                 "ALL(term in {query_keyword} WHERE LOWER(gene.descr) CONTAINS term)) "
                                                 "OPTIONAL MATCH (gene)-[rel]->(gene_nb:Gene) RETURN gene,rel,gene_nb",
                                                 {"query_species": query_species, "query_keyword": query_keyword,
                                                  "query_contig": query_contig})
        # One term in keyword has to match in either description or name
        elif match_all_any == "ANY":
            with project_db_driver.session() as session_b:
                query_hits = session_b.run("MATCH(gene:Gene) WHERE LOWER(gene.species) CONTAINS {query_species} "
                                                 "AND LOWER(gene.contig) CONTAINS {query_contig} "
                                                 "AND (ANY(term in {query_keyword} WHERE LOWER(gene.name) CONTAINS term) OR "
                                                 "ANY(term in {query_keyword} WHERE LOWER(gene.descr) CONTAINS term)) "
                                                 "OPTIONAL MATCH (gene)-[rel]->(gene_nb:Gene) RETURN gene,rel,gene_nb",
                                                 {"query_species": query_species, "query_keyword": query_keyword,
                                                  "query_contig": query_contig})
        else:
            query_hits = []
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
                [record["gene"][item] for item in ["species", "contig",
                                                   "start", "stop", "name", "descr", "nt_seq"]]
            if record["rel"] is not None:
                if record["rel"].type in ["5_NB", "3_NB"]:
                    gene_node_nb_rel.append((record["gene"]["geneId"], record["rel"].type, record["gene_nb"]["geneId"]))
                elif record["rel"].type == "HOMOLOG":
                    gene_node_hmlg_rel.append((record["gene"]["geneId"], record["rel"].type, record["rel"]["clstr_sens"],
                                               record["rel"]["perc_match"], record["gene_nb"]["geneId"]))
        # Search for protein nodes and protein-protein relationships
        # Proteins are always coded for by genes. The keyword query is matched against the protein name and
        # the protein description. Species and chromosome information is retrieved from the gene node.
        # As for genes, for every matched node all its relations are returned in a separate row (if there are no
        # relations there will be a single row with rel=None)
        # Matched protein nodes are initially stored in a dict to enforce uniqueness
        # Query also returns information about the species and the chromosome coding for this protein
        # if query_type in ["prot", "both"]:
        #     # query_hits = project_db_driver.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
        #     #                                  "CONTAINS {query_species} AND (LOWER(prot.protein_name) CONTAINS "
        #     #                                  "{query_keyword} OR LOWER(prot.protein_descr) CONTAINS {query_keyword} "
        #     #                                  ") WITH "
        #     #                                  "COLLECT(prot) AS prots UNWIND prots as p1 UNWIND prots as p2 "
        #     #                                  "OPTIONAL MATCH (p1)-[rel]->(p2) RETURN p1,rel,p2",
        #     #                                  {"query_species":query_species, "query_keyword":query_keyword})
        #     query_hits = project_db_driver.run("MATCH(gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
        #                                      "CONTAINS {query_species} AND LOWER(gene.chromosome) CONTAINS "
        #                                      "{query_chromosome} AND (LOWER(prot.protein_name) CONTAINS "
        #                                      "{query_keyword} OR LOWER(prot.protein_descr) CONTAINS {query_keyword}) "
        #                                      "OPTIONAL MATCH (prot)-[rel]->(prot_nb:Protein) "
        #                                      "RETURN prot,rel,prot_nb,gene.species,gene.chromosome",
        #                                      {"query_species": query_species, "query_keyword": query_keyword,
        #                                       "query_chromosome": query_chromosome})
        #     for record in query_hits:
        #         protein_node_hits[record["prot"]["proteinId"]] = \
        #             [record["prot"]["protein_name"], record["prot"]["protein_descr"],
        #              record["gene.species"], record["gene.chromosome"]]
        #         # Check if protein p1 has a relationship to protein p2
        #         # Possible types of relationship: HOMOLOG or SYNTENY,
        #         # both with the additional attribute "sensitivity" (of clustering)
        #         if record["rel"] is not None:
        #             protein_node_rel.append((record["prot"]["proteinId"], record["rel"].type,
        #                                      record["rel"]["sensitivity"], record["prot_nb"]["proteinId"]))


        # Search for gene-protein relationships (only if looking for both protein and gene nodes)
        # i.e. relations between both gene and protein nodes found above (which can only be CODING relations)
        # Since both genes and proteins need to be found, it is sufficient that the species term and the gene_name
        # # term are found (the search for protein nodes also checks the gene_name of the coding gene)
        # if query_type == "both":
        #     # query_hits = project_db_driver.run("MATCH coding_path = (gene:Gene)-[:CODING]->(prot:Protein) WHERE LOWER(gene.species) "
        #     #                                  "CONTAINS {query_species} AND (LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
        #     #                                  "LOWER(gene.gene_descr)  CONTAINS {query_keyword} )"
        #     #                                  "RETURN gene.geneId, prot.proteinId",
        #     #                                  {"query_species": query_species, "query_keyword": query_keyword})
        #     query_hits = project_db_driver.run("MATCH coding_path = (gene:Gene)-[:CODING]->(prot:Protein) "
        #                                      "WHERE LOWER(gene.species) CONTAINS {query_species} "
        #                                      "AND LOWER(gene.chromosome) CONTAINS {query_chromosome} AND "
        #                                      "(LOWER(gene.gene_name) CONTAINS {query_keyword} OR "
        #                                      "LOWER(gene.gene_descr)  CONTAINS {query_keyword}) AND "
        #                                      "(LOWER(prot.protein_name) CONTAINS {query_keyword} OR "
        #                                      "LOWER(prot.protein_descr) CONTAINS {query_keyword}) "
        #                                      "RETURN gene.geneId, prot.proteinId",
        #                                      {"query_species": query_species, "query_chromosome": query_chromosome,
        #                                       "query_keyword": query_keyword})
        #     for record in query_hits:
        #         protein_gene_node_rel.append((record["gene.geneId"], "CODING", record["prot.proteinId"]))
        print("Gene nodes: "+str(len(gene_node_hits)))
        #print("Protein nodes: "+str(len(protein_node_hits)))
        print("Gene-gene NB relations: "+str(len(gene_node_nb_rel)))
        print("Gene-gene hmlg relations: "+str(len(gene_node_hmlg_rel)))


        #print("Prot-prot relations: "+str(len(protein_node_rel)))
        #print("Gene-prot relations: "+str(len(protein_gene_node_rel)))
        # Reformat the node and edge data for either Daisychain-web or Daisychain-cmd
        # Close connection to the project-db
        project_db_driver.close()
        if return_format == "CMD":
            self.send_data_cmd(gene_node_hits, {}, gene_node_nb_rel,gene_node_hmlg_rel, [],
                               [])
        else:
            self.send_data_web(gene_node_hits, {}, gene_node_nb_rel,gene_node_hmlg_rel, [],
                               [])

