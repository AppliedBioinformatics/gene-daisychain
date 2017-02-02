# Parser for clusters, e.g. produced with MCL
# Returns a list of clusters:
# [[A,B], [C,D,E],[F],...]
# with A,B,C...corresponding to the gene or protein name used in the Graph-DB
import sys, statistics


class ClusterParser:

    # Initialize instance parameters
    def __init__(self):
        self.cluster_list = []

    # Interface function, keyword decides which file format is to be parsed
    # Parameter: format := tool used to cluster
    #            file := path to cluster result
    def parse_cluster(self, clstr_format, clstr_file):
        switch = {"MCL": self.__parse_mcl_cluster}
        switch[clstr_format](clstr_file)
        return self.cluster_list

    # Parse cluster results created with MCL
    # Command:
    # mcl BLAST_result.mci [-te 8] -I 6.0 -use-tab BLAST_result.tab
    # Each line is a cluster, each line contains tab-separated names
    # Output has no header lines
    def __parse_mcl_cluster(self, clstr_file):
        with open(clstr_file, "r") as mcl_cluster_file:
            for line in mcl_cluster_file:
                line = line.strip().split("\t")
                if not line: continue
                # Append regex to each protein ID to circumvent .version problem
                line = [ele + ".*" for ele in line]
                self.cluster_list.append(line)

# For cluster stats only, remove before flight
if __name__ == "__main__":
    print("Testing cluster parse")
    format = sys.argv[1]
    type = sys.argv[2]
    file = sys.argv[3]
    cluster_parse = ClusterParser()
    result = cluster_parse.parse_protein(format, type, file)
    median = statistics.median([len(res) for res in result])
    print(median)
