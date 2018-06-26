# Parse gene and protein annotation from CSV file
# CSV file has to contain these mandatory fields:
# seq_name, start_index, stop_index, gene_name, protein_name
# These fields are optional:
# coding_frame, strand_orientation, chromosome_name, protein_description
# First line in the csv file must contain the header names as stated above
# Each gene annotation line can contain multiple proteins that gene is coding for
# In that case, the protein_name field has this format: protein_a;protein_b;protein_c,...
# There must be either a single protein description for all proteins in a row or
# individual protein descriptions for all proteins in one row
# Example:
# protein_a;protein_b,protein_description, (one description for all proteins)
# protein_a;protein_b,protein_description_a;protein_description_b, (individual description for each protein)
# protein_a;protein_b,, (no description for any protein)
# Rows/Genes do not need to be ordered
# Class return function returns gene and protein node information in list format:
# [(gene_id,species_name,seq_name,start_index,stop_index,gene_name,chromosome_name,strand_orientation,coding_frame),...]
# [(protein_id, protein_name, protein_description, gene_id),...]
import csv
import os


class CSVParser:
    def __init__(self, csv_file_path, gene_id, protein_id):
        self.csv_file_path = csv_file_path
        self.species_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        self.gene_id = gene_id
        self.protein_id = protein_id
        self.gene_annotation_list = []
        self.protein_annotation_list = []

    def parse_csv(self):
        csv_reader = csv.DictReader(open(self.csv_file_path,"r"))
        try:
            for gene_row in csv_reader:
                self.gene_id += 1
                gene_data = [self.gene_id, self.species_name, gene_row["seq_name"], int(gene_row["start_index"]),
                             int(gene_row["stop_index"]), gene_row["gene_name"], gene_row.get("chromosome_name","?"),
                             gene_row.get("strand_orientation", "?"), gene_row.get("coding_frame", "?")]
                protein_names = gene_row["protein_name"].split(";")
                protein_descr = gene_row.get("protein_description", "?").split(";")
                if len(protein_descr) != len(protein_names):
                    protein_descr = len(protein_names)*[protein_descr[0]]
                for protein_node in list(zip(protein_names,protein_descr)):
                    self.protein_id+=1
                    protein_data = [self.protein_id, protein_node[0], protein_node[1], self.gene_id]
                    self.protein_annotation_list.append(protein_data)
                self.gene_annotation_list.append(gene_data)
            # Sort the gene_list
            self.gene_annotation_list = sorted(self.gene_annotation_list, key=lambda x: (x[2], x[3], x[4]))
        except (KeyError, IndexError):
            exit(1)

    # Retrieve the sorted gene list
    def get_gene_list(self):
        return (self.gene_annotation_list)

    # Retrieve the protein list
    def get_protein_list(self):
        return (self.protein_annotation_list)

    # Retrieve protein nodes as dict
    # dict[prot_name] = (protein_id, protein_desc, gene_id)
    def get_protein_dict(self):
        protein_dict = {}
        for protein in self.protein_annotation_list:
            protein_dict[protein[1]]=(protein[0],protein[2],protein[3])
        return (protein_dict)

    # Retrieve current gene_node id
    def get_gene_node_id(self):
        return (self.gene_id)

    # Retrieve current protein_node id
    def get_protein_node_id(self):
        return (self.protein_id)







