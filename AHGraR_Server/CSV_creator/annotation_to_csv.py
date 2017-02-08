# Convert gene annotation information into CSV file format
# This includes: CSV file describing the gene properties itself
# plus two CSV files describing the 5' and 3' relations
# CSV files are used to build a new Neo4j graph DB
# Init. params: Project-ID
# The function create_csv is called multiple times, once for each annotation file.
# with file_type being either GFF3 or CSV
# Each annotation file thus generates a set of three CSV files:
# Species_variant_gene_node.csv
# Species_variant_gene_5nb.csv
# Species_variant_gene_3nb.csv
# Plus a dict mapping protein names to [protein_id, protein_description, coding_gene_id]
# Dict is saved in json format in CSV directory and used at a later stage while parsing the
# BLAST/MCL clustering results
from Parser.GFF3_parser_gffutils import GFF3Parser
from Parser.CSV_parser import CSVParser
import os
import json


class AnnoToCSV:
    def __init__(self, proj_id):
        self.file_path =  os.path.join("Projects", proj_id, "Files")
        self.CSV_path = os.path.join("Projects", proj_id, "CSV")
        self.gene_node_id = 0
        self.protein_node_id = 0

    def create_csv(self, species_name, annofile_name, annofile_type, anno_mapping, feat_hierarchy):
        # Define and create output files
        # For each species, a set of three CSV files is created.
        gene_node_output = open(os.path.join(self.CSV_path, "gene_nodes.csv"),"a")
        gene_rel5nb_output = open(os.path.join(self.CSV_path, "gene_5nb.csv"),"a")
        gene_rel3nb_output = open(os.path.join(self.CSV_path, "gene_3nb.csv"),"a")
        # Parse gene annotation file into one list:
        # [(gene_id, species_name, contig_name, start_index, stop_index, gene_name,
        #                           chromosome, strand_orientation, coding_frame),...]
        # Decicion which parser to use depends on annotation file type: GFF3 or CSV
        if annofile_type == "gff3":
            # Parse a GFF3 file
            anno_parser = GFF3Parser(os.path.join(self.file_path, annofile_name),
                                     self.gene_node_id, self.protein_node_id)
            # Set the annotation mapping string
            anno_parser.set_annotation_mapper(anno_mapping)
            # Set the feature hierarchy
            anno_parser.set_feature_hierarchy(feat_hierarchy)
        elif annofile_type == "csv":
            # Parse a CSV file
            anno_parser = CSVParser(os.path.join(self.file_path, annofile_name),
                                    self.gene_node_id, self.protein_node_id)
        # Parse the file
        anno_parser.parse_gff3_file()
        # Retrieve gene annotation as list
        gene_list = anno_parser.get_gene_list()
        # Retrieve protein annotation as dict
        protein_dict = anno_parser.get_protein_dict()
        # Set gene_node_id and protein_node_id to id last assigned while parsing
        self.gene_node_id = anno_parser.get_gene_node_id()
        self.protein_node_id = anno_parser.get_protein_node_id()
        # Save protein_dict as json-file
        # This will be used at a later stage following the homology clustering of proteins
        # File is stored temporarily in the CSV folder
        with open(os.path.join(self.CSV_path, species_name+"_protein_dict.json"), "w") as json_file:
            json.dump(protein_dict, json_file)
        # Format for Gene node CSV:
        # geneId:ID(Gene),species,contig_name,start:INT,stop:INT,gene_name, chromosome, strand_orientation, coding_frame
        #gene_node_output.write("geneId:ID(Gene),species,contig_name,start:INT,stop:INT,gene_name, chromosome, strand, frame\n")
        # Format for (Gene)-[5'-nb]->(Gene)
        # :START_ID(Gene),:END_ID(Gene)
        #gene_rel5nb_output.write(":START_ID(Gene),:STOP_ID(Gene)\n")
        # Format for (Gene)-[3'-nb]->(Gene)
        # :START_ID(Gene),:END_ID(Gene)
        #gene_rel3nb_output.write(":START_ID(Gene),:STOP_ID(Gene)\n")
        # Gene list has to be sorted at this stage (!!!)
        # Walk through gene list:
        prev_contig = ""
        prev_id = 0
        prev_start = None
        for gene in gene_list:
            cur_contig = gene[2]
            cur_id = gene[0]
            cur_start = gene[3]
            # Only connect genes on the same contig
            # Only connect genes if both have a defined start index
            if (prev_contig == cur_contig and prev_start and cur_start):
                gene_rel3nb_output.write(str(prev_id) + "," + str(cur_id) + "\n")
                gene_rel5nb_output.write(str(cur_id) + "," + str(prev_id) + "\n")
            # In all cases: create an entry in the CSV to create a Gene node
            # Format:
            # geneId:ID(Gene),species,contig_name,start:INT,stop:INT,gene_name, chromosome, strand_orientation, coding_frame
            # [(gene_id, species_name, contig_name, start_index, stop_index, gene_name, chromosome, strand_orientation, coding_frame),...]
            gene_node_output.write(
                ",".join([str(cur_id), gene[1], gene[2], str(gene[3]), str(gene[4]), gene[5], gene[6], gene[7],gene[8] + "\n"]))
            prev_start = cur_start
            prev_id = cur_id
            prev_contig = cur_contig
        # Close files
        gene_node_output.close()
        gene_rel5nb_output.close()
        gene_rel3nb_output.close()

