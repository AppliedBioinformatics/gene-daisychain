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
from Parser.GFF3_parser_gffutils_v2 import GFF3Parser_v2
import os



class AnnoToCSV:
    def __init__(self, CSV_path, nt_transcript_path, prot_translation_path):
        self.CSV_path = CSV_path
        # Initialize GFF3/annotation parser
        # Parameters: Output path for transcript and translation sequences
        self.anno_parser = GFF3Parser_v2(nt_transcript_path, prot_translation_path)
        # Initialize output files
        # Data from each parsed species will be appended to the following three files
        # Write header lines
        # Format for Gene node CSV:
        # geneId:ID(Gene),species,contig_name,start:INT,stop:INT,strand_orientation,name, descr, nt_seq
        with open(os.path.join(self.CSV_path, "gene_nodes.csv"), "w") as gene_node_output:
            gene_node_output.write("geneId:ID(Gene),species,contig,start,stop,strand,name,descr,nt_seq\n")
        # Format for (Gene)-[5'-nb]->(Gene)
        # :START_ID(Gene),:END_ID(Gene)
        with open(os.path.join(self.CSV_path, "gene_5nb.csv"), "w") as gene_rel5nb_output:
            gene_rel5nb_output.write(":START_ID(Gene),:END_ID(Gene)\n")
        # Format for (Gene)-[3'-nb]->(Gene)
        # :START_ID(Gene),:END_ID(Gene)
        with open(os.path.join(self.CSV_path, "gene_3nb.csv"), "w") as gene_rel3nb_output:
            gene_rel3nb_output.write(":START_ID(Gene),:END_ID(Gene)\n")
        # Format for Protein node CSV:
        # proteinId:ID(Protein),protein_name,protein_descr
        with open(os.path.join(self.CSV_path, "protein_nodes.csv"), "w") as protein_node_output:
            protein_node_output.write("proteinId:ID(Protein),prot_seq\n")
        # Format for (Gene)-[:CODING]->(Protein)
        with open(os.path.join(self.CSV_path, "gene_protein_coding.csv"), "w") as gene_protein_coding_output:
            gene_protein_coding_output.write(":START_ID(Gene),:END_ID(Protein)\n")

    def create_csv(self, anno_file, genome_file, parent_feature_type, subfeatures, name_attribute, descr_attribute):


        # Parse the file and retrieve gene annotation as list
        gene_list = self.anno_parser.parse_gff3_file(anno_file, genome_file, True,
                                                     parent_feature_type, subfeatures, name_attribute, descr_attribute)

          # Gene list has to be sorted at this stage (!!!)
        # Walk through gene list and write content to CSV files
        with open(os.path.join(self.CSV_path, "gene_nodes.csv"), "a") as gene_node_output:
            with open(os.path.join(self.CSV_path, "protein_nodes.csv"), "a") as protein_node_output:
                with open(os.path.join(self.CSV_path, "gene_5nb.csv"), "a") as gene_rel5nb_output:
                    with open(os.path.join(self.CSV_path, "gene_3nb.csv"), "a") as gene_rel3nb_output:
                        with open(os.path.join(self.CSV_path, "gene_protein_coding.csv"),
                                  "a") as gene_protein_coding_output:
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
                                    gene_rel3nb_output.write("g"+str(prev_id) + "," + "g"+str(cur_id) + "\n")
                                    gene_rel5nb_output.write("g"+str(cur_id) + "," + "g"+str(prev_id) + "\n")
                                # In all cases: create an entry in the CSV to create a Gene node
                                # Format:geneId:ID(Gene),species,contig_name,start:INT,stop:INT,strand_orientation,
                                # name, descr, nt_seq
                                gene_node_output.write(
                                    ",".join(["g"+str(cur_id), gene[1], cur_contig, str(gene[3]), str(gene[4]), gene[5],
                                              gene[6], gene[7],gene[8] + "\n"]))
                                # If there is a protein sequence, create a protein node and a gene->prot CODING relation
                                if gene[9]:
                                    protein_node_output.write(
                                        ",".join(["p"+str(cur_id),gene[9] + "\n"]))
                                    gene_protein_coding_output.write(
                                        ",".join(["g"+str(cur_id), "p"+str(cur_id) + "\n"]))
                                prev_start = cur_start
                                prev_id = cur_id
                                prev_contig = cur_contig


