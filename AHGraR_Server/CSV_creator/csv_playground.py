import itertools as iter

import Outdated.protein_parser as prot_2_gene_parser
import Parser.annotation_parser as anno_parser
import Parser.cluster_Parser as ClusterParser

# Create CSV for genes
anno_parser = anno_parser.AnnotationParser()
anno_files = ["/mnt/oliver/data/BraNapus/GCF_000686985.1_Brassica_napus_assembly_v1.0_genomic.gff",
              "/mnt/oliver/data/BraOlea/GCF_000695525.1_BOL_genomic.gff",
              "/mnt/oliver/data/BraRapus/GCF_000309985.1_Brapa_1.0_genomic.gff",
              "/mnt/oliver/data/TAIR10/GCF_000001735.3_TAIR10_genomic.gff"]
gene_list = []

for anno_file in anno_files:
    print(anno_file)
    gene_list.extend(anno_parser.parse_annotation("NCBI_refseq",anno_file))
#prot_2_gene_mapper = prot_2_gene_parser.ProteinParser()
#prot_2_gene_map_list = prot_2_gene_mapper.parse_protein("NCBI_refseq","/home/oliver/Dokumente/Internship Perth/Pycharm_WD/Playground/GCF_000686985.1_Brassica_napus_assembly_v1.0_genomic_head.gff")

gene_node_csv = "gene_node.csv"
gene_3nb_gene_rel_csv = "gene_3nb_gene_rel.csv"
gene_5nb_gene_rel_csv = "gene_5nb_gene_rel.csv"
# Format for Gene node CSV:
# geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name
gene_node_csv_file = open(gene_node_csv, "w")
gene_node_csv_file.write("geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name\n")
# Format for (gene)-[3'-nb]->(gene)
# :START_ID(Gene),:END_ID(Gene)
gene_3nb_gene_rel_csv_file = open(gene_3nb_gene_rel_csv, "w")
gene_3nb_gene_rel_csv_file.write(":START_ID(Gene),:END_ID(Gene)\n")
# Format for (gene)-[5'-nb]->(gene)
# :START_ID(Gene),:END_ID(Gene)
gene_5nb_gene_rel_csv_file = open(gene_5nb_gene_rel_csv, "w")
gene_5nb_gene_rel_csv_file.write(":START_ID(Gene),:END_ID(Gene)\n")
connect_nb=True
gene_id_dict = {}

# Gene list has to be sorted at this stage
# Walk thru gene list:
# Append gene lists from multiple organisms
prev_org = ""
prev_chrom = ""
prev_strand = ""
prev_start = ""
prev_name = ""
prev_id = 0
for gene in gene_list:
    cur_org = gene[0]
    cur_chrom = gene[1]
    cur_strand = gene[2]
    cur_start = gene[3]
    cur_name = gene[5]
    cur_id = prev_id+1
    # Add entry to gene - 2 - ID dict:
    gene_id_dict[(cur_org,cur_chrom, cur_strand,cur_start, cur_name)] = cur_id
    # Only connect genes if connect_nb = TRUE
    # Only connect genes from the same organism and same chromosome
    # Only connect genes if prev and cur gene have a chromosome index position
    if (connect_nb and prev_org == cur_org and prev_chrom == cur_chrom and prev_start and cur_start):
        #print("Connecting"+str((prev_id, cur_id)))
        gene_3nb_gene_rel_csv_file.write(str(prev_id)+","+str(cur_id)+"\n")
        gene_5nb_gene_rel_csv_file.write(str(cur_id) + "," + str(prev_id) + "\n")
    # In all cases: create an entry in the CSV to create a Gene node
    # Format:
    # geneId:ID(Gene),organism,chromosome,strand,start:INT,end:INT,name
    gene_node_csv_file.write(",".join([str(cur_id),cur_org,cur_chrom,cur_strand,cur_start,gene[4],cur_name+"\n"]))
    prev_org = cur_org
    prev_chrom = cur_chrom
    prev_strand = cur_strand
    prev_start = cur_start
    prev_name = cur_name
    prev_id = cur_id
gene_node_csv_file.close()
gene_3nb_gene_rel_csv_file.close()
gene_5nb_gene_rel_csv_file.close()

# Do the same for proteins
protein_node_csv = "protein_node.csv"
gene_coding_protein_csv = "gene_coding_protein_rel.csv"
protein_node_csv_file = open(protein_node_csv, "w")
gene_coding_protein_csv_file = open(gene_coding_protein_csv, "w")
gene_coding_protein_csv_file.write(":START_ID(Gene),:END_ID(Protein)\n")
protein_node_csv_file.write("proteinId:ID(Protein),name,description\n")
prot_2_gene_mapper = prot_2_gene_parser.ProteinParser()
prot_id_dict = {}
prot_id = 0
for anno_file in anno_files:
    print(anno_file)
    prot_2_gene_map_list = prot_2_gene_mapper.parse_protein("NCBI_refseq",anno_file)
    for prot in prot_2_gene_map_list:
        prot_id += 1
        prot_id_dict[prot[0]]=prot_id
        protein_node_csv_file.write(str(prot_id)+","+prot[0]+","+prot[1]+"\n")
        #(Organism,Chromosome,Strand_orientation,Start_index,End_index, Gene_name)
        matching_gene_props = prot[2]
        matching_gene_id = gene_id_dict[(matching_gene_props[0],matching_gene_props[1], matching_gene_props[2],matching_gene_props[3], matching_gene_props[5])]
        gene_coding_protein_csv_file.write(str(matching_gene_id)+","+str(prot_id)+"\n")
protein_node_csv_file.close()
gene_coding_protein_csv_file.close()

# Same thing for the homolog cluster
protein_hmlg_protein_csv = "protein_hmlg_protein_rel.csv"
protein_hmlg_protein_csv_file = open(protein_hmlg_protein_csv,"w")
protein_hmlg_protein_csv_file.write(":START_ID(Protein),sensitivity,:END_ID(Protein)\n")
# First we have to do a workaround for this annoying acc.version problem
prot_id_dict[prot[0]]=prot_id
prot_id_dict_no_version = {}
for key in prot_id_dict.keys():
    no_version_key = key[:key.rfind(".")]
    prot_id_dict_no_version[no_version_key]=prot_id_dict[key]
cluster_files = [("/mnt/oliver/projects/MCL/out.ALL_SPECIES_proteins_vs_Plant_prots_fast_noversion.mci.I14", 1.4),
                 ("/mnt/oliver/projects/MCL/out.ALL_SPECIES_proteins_vs_Plant_prots_fast_noversion.mci.I20", 2.0),
                 ("/mnt/oliver/projects/MCL/out.ALL_SPECIES_proteins_vs_Plant_prots_fast_noversion.mci.I40", 4.0),
                 ("/mnt/oliver/projects/MCL/out.ALL_SPECIES_proteins_vs_Plant_prots_fast_noversion.mci.I60", 6.0),
                 ("/mnt/oliver/projects/MCL/out.ALL_SPECIES_proteins_vs_Plant_prots_fast_noversion.mci.I200", 20.0),]

for cluster_file in cluster_files:
    # Get a new instance of the cluster parser for each cluster file
    cluster_parser = ClusterParser.ClusterParser()
    cluster_list = cluster_parser.parse_cluster("MCL", cluster_file[0])
    for cluster in cluster_list:
        # Map protein IDs to protein names in cluster
        cluster = [prot_id_dict_no_version[prot_name[:prot_name.rfind(".")]] for prot_name in cluster]
        # Make all possible pairwise combinations between IDs
        # i.e. [1,2,3] --> [(1,1),(1,2),(1,3),(2,1),(2,2),(2,3),(3,1),(3,2),(3,3)]
        cluster_pw_comb= iter.product(cluster, repeat=2)
        # Write pw combinations to relationship CSV file
        # Add clustering sensitivity as property
        for comb in cluster_pw_comb:
            protein_hmlg_protein_csv_file.write(",".join([str(comb[0]), str(cluster_file[1]), str(comb[1]) + "\n"]))

protein_hmlg_protein_csv_file.close()