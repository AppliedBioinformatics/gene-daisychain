# Convert gene node information into CSV file format
# This includes: CSV file describing the gene nodes itself
# Plus two CSV files describing the 5' and 3' relations
# CSV files can be loaded fast and easy into Neo4j DB
# Input: List with paths to gene annotation files, path to output file, project ID,
#  annotation file format (e.g.NCBI_refseq)
# Output file names have this format:
# [Path]_gene_node.csv
# [Path]_gene_5nb.csv
# [Path]_gene_3nb.csv
import Parser.annotation_parser as anno_parser
import pickle


class GeneToCSV:
    def __init__(self, anno_file_path_list, output_file_path, project_id, anno_file_type):
        self.anno_file_path_list = anno_file_path_list
        self.output_file_path = output_file_path
        self.anno_parser = anno_parser.AnnotationParser()
        self.project_id = project_id
        self.anno_file_type = anno_file_type
        # Retrieve project dump or create a new dict in
        # case this a new project id
        try:
            self.project_dump_dict= pickle.load(open("project_dump_"+str(self.project_id)+".pkl", "rb"))
        except FileNotFoundError:
            self.project_dump_dict = {}

    def __dump_project_dict(self):
        pickle.dump(self.project_dump_dict, open("project_dump_"+str(self.project_id)+".pkl","wb"),
                    pickle.HIGHEST_PROTOCOL)

    def create_csv(self, connect_nb):
        # Retrieve project-id dependent first gene_id
        last_gene_id = self.project_dump_dict.get("last_gene_id",0)
        # Retrieve project-id dependent dict of all previous assigned gene-ids
        gene_id_dict = self.project_dump_dict.get("gene_id_dict",{})
        # Create output files
        gene_node_output = open(self.output_file_path+"_gene_node.csv","w")
        gene_rel5nb_output = open(self.output_file_path + "_gene_5nb.csv", "w")
        gene_rel3nb_output = open(self.output_file_path + "_gene_3nb.csv", "w")
        # Parse anno files into one gene list
        # Format [(Organism,Chromosome,Strand_orientation,Start_index,End_index, Gene_name),...]
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
            if (connect_nb and prev_org == cur_org and prev_chrom == cur_chrom and prev_start and cur_start):
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
