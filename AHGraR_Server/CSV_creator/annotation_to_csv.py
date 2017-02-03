# Convert gene annotation information into CSV file format
# This includes: CSV file describing the gene properties itself
# plus two CSV files describing the 5' and 3' relations
# CSV files are used to build a new Neo4j graph DB
# Init. params: Project-ID
# The function create_csv is the called with a tuple: (file_name, file_type)
# with file_type being either GFF3 or CSV
# Each annotation file thus generates a set of three CSV files:
# Species_variant_gene_node.csv
# Species_variant_gene_5nb.csv
# Species_variant_gene_3nb.csv
from Parser.GFF3_parser_gffutils import GFF3Parser
from Parser.CSV_parser import CSVParser
import os


class AnnoToCSV:
    def __init__(self, proj_id):
        self.file_path =  os.path.join("Projects", proj_id, "Files")
        self.CSV_path = os.path.join("Projects", proj_id, "CSV")
        self.gene_node_id = 0
        self.protein_node_id = 0


    def create_csv(self, species_name, annofile_name, annofile_type, anno_mapping, feat_hierarchy):
        # Define and create output files
        # For each species, a set of three CSV files is created.
        gene_node_output = open(os.path.join(self.CSV_path, species_name+"_gene_node.csv"),"w")
        gene_rel5nb_output = open(os.path.join(self.CSV_path, species_name+"_gene_5nb.csv"),"w")
        gene_rel3nb_output = open(os.path.join(self.CSV_path, species_name+"_gene_3nb.csv"),"w")
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
        protein_list = anno_parser.get_protein_dict()
        # Set gene_node_id and protein_node_id to id last assigned while parsing
        self.gene_node_id = anno_parser.get_gene_node_id()
        self.protein_node_id = anno_parser.get_protein_node_id()
        print(self.gene_node_id)
        print(self.protein_node_id)
        return
        gene_list = []
        for anno_file_path in self.anno_file_path_list:
            gene_list.extend(anno_parser.parse_annotation(self.anno_file_type, anno_file_path))
        # Format for Gene node CSV:
        # geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name
        gene_node_output.write("geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name\n")
        # Format for (gene)-[5'-nb]->(gene)
        # :START_ID(Gene),:END_ID(Gene)
        gene_rel5nb_output.write(":START_ID(Gene),:END_ID(Gene)\n")
        # Format for (gene)-[3'-nb]->(gene)
        # :START_ID(Gene),:END_ID(Gene)
        gene_rel3nb_output.write(":START_ID(Gene),:END_ID(Gene)\n")
        # Gene list has to be sorted at this stage (!!!)
        # Walk through gene list:
        # Append gene lists from multiple organisms
        prev_org = ""
        prev_chrom = ""
        prev_start = ""
        prev_id = last_gene_id
        for gene in gene_list:
            cur_org = gene[0]
            cur_chrom = gene[1]
            cur_strand = gene[2]
            cur_start = gene[3]
            cur_name = gene[5]
            cur_id = prev_id + 1
            # Add entry to gene - 2 - ID dict:
            gene_id_dict[(cur_org, cur_chrom, cur_strand, cur_start, cur_name)] = cur_id
            # Only connect genes if connect_nb = TRUE
            # Only connect genes from the same organism and same chromosome
            # Only connect genes if prev and cur gene have a chromosome index position
            if (prev_org == cur_org and prev_chrom == cur_chrom and prev_start and cur_start):
                # print("Connecting"+str((prev_id, cur_id)))
                gene_rel3nb_output.write(str(prev_id) + "," + str(cur_id) + "\n")
                gene_rel5nb_output.write(str(cur_id) + "," + str(prev_id) + "\n")
            # In all cases: create an entry in the CSV to create a Gene node
            # Format:
            # geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name
            gene_node_output.write(
                ",".join([str(cur_id), cur_org, cur_chrom, cur_strand, cur_start, gene[4], cur_name + "\n"]))
            prev_org = cur_org
            prev_chrom = cur_chrom
            prev_start = cur_start
            prev_id = cur_id
        # Close files
        gene_node_output.close()
        gene_rel5nb_output.close()
        gene_rel3nb_output.close()
        # Store last gene-id and updated gene-id-2-nodes dict in dump
        self.project_dump_dict["last_gene_id"] = prev_id
        self.project_dump_dict["gene_id_dict"] = gene_id_dict
