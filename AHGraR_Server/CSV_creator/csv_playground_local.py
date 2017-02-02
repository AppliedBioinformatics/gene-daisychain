import Parser.cluster_Parser as ClusterParser
import itertools as iter
protein_hmlg_protein_csv_file = open("local_hmlg.csv","w")
protein_hmlg_protein_csv_file.write(":START_ID(Protein),sensitivity,:END_ID(Protein)\n")
prot_id_dict_no_version = {"XP_013660870":1,
                           "XP_009111662":2,
                           "XP_013606687":3,
                           "NP_566112":4,
                           "XP_013621297":5,
                           "XP_013685556":6,
                           "XP_009126985":7,
                           "XP_013630071":8,
                           "XP_009132355":9,
                           "XP_013682704":10,
                           "NP_200382":11,
                           "XP_013713101":12}
cluster_files = [("/home/oliver/Dokumente/Internship Perth/Pycharm_WD/CSV_creator/mcl_14_tab.txt", 1.4),
                 ("/home/oliver/Dokumente/Internship Perth/Pycharm_WD/CSV_creator/mcl_20_tab.txt", 2.0),
                 ("/home/oliver/Dokumente/Internship Perth/Pycharm_WD/CSV_creator/mcl_40_tab.txt", 4.0),
                 ("/home/oliver/Dokumente/Internship Perth/Pycharm_WD/CSV_creator/mcl_60_tab.txt", 6.0)]
cluster_parser = ClusterParser.ClusterParser()
for cluster_file in cluster_files:
    cluster_parser = ClusterParser.ClusterParser()
    cluster_list = cluster_parser.parse_cluster("MCL", cluster_file[0])
    print(len(cluster_list))
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