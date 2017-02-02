# Convert protein node information into CSV file format
# This includes: CSV file describing the protein nodes itself
# Plus a CSV file describing the (:Gene)-[:CODING]->(:Protein) relations
# CSV files can be loaded fast and easy into Neo4j DB
# Input: List with paths to GFF3 gene annotation file, path to output file, project ID,
#  annotation file format (e.g.NCBI_refseq), connect_genes_2_proteins?
# Output file names have this format:
# [Path]_protein_node.csv
# [Path]_gene_coding_protein_rel.csv
import pickle

import Outdated.protein_parser as prot_2_gene_parser
import Parser.annotation_parser as anno_parser


class ProteinToCSV:
    def __init__(self, anno_file_path_list, output_file_path, project_id, anno_file_type, connect_genes_2_proteins):
        self.anno_file_path_list = anno_file_path_list
        self.output_file_path = output_file_path
        self.anno_parser = anno_parser.AnnotationParser()
        self.project_id = project_id
        self.anno_file_type = anno_file_type
        self.connect_genes_2_proteins = connect_genes_2_proteins
        # Retrieve project dump or create a new dict in
        # case this a new project id
        try:
            self.project_dump_dict= pickle.load(open("project_dump_"+str(self.project_id)+".pkl", "rb"))
        except FileNotFoundError:
            self.project_dump_dict = {}

    def __dump_project_dict(self):
        pickle.dump(self.project_dump_dict, open("project_dump_"+str(self.project_id)+".pkl","wb"),
                    pickle.HIGHEST_PROTOCOL)

    def create_csv(self, connect_genes_2_proteins):
        # Retrieve project-id dependent first gene_id
        last_protein_id = self.project_dump_dict.get("last_protein_id", 0)
        # Retrieve project-id dependent dict of all previous assigned gene-ids
        prot_id_dict = self.project_dump_dict.get("prot_id_dict", {})
        gene_id_dict = self.project_dump_dict.get("gene_id_dict", {})
        # Create output files
        protein_node_output = open(self.output_file_path + "_protein_node.csv", "w")
        gene_coding_protein_rel_output = open(self.output_file_path + "_gene_coding_protein_rel.csv", "w")
        protein_node_output.write("proteinId:ID(Protein),name,description\n")
        gene_coding_protein_rel_output.write(":START_ID(Gene),:END_ID(Protein)\n")
        prot_2_gene_mapper = prot_2_gene_parser.ProteinParser()
