# Provides project build functions to AHGraR-Server
# All functions return either a String or Null
# Functions directly accessible by user query always return a string via socket connection
import Parser.GFF3_parser_gffutils
import os
from itertools import islice
from CSV_creator.annotation_to_csv import AnnoToCSV
from Parser.FASTA_parser import FastaParser


class DBBuilder:
    def __init__(self, main_db_connection, task_manager, send_data):
        self.main_db_conn = main_db_connection
        self.task_mngr = task_manager
        self.send_data = send_data

    # Close connection to main-DB
    def close_connection(self):
        self.main_db_conn.close()

    # Reply to request send from a user app
    # User_request is a list produced by the "_" split command
    # e.g. [STAT, ProjectID, TaskID1, TaskID2]
    def evaluate_user_request(self, user_request):
        # Set GFF3 parser for some or all GFF3 files in a project
        if user_request[0] == "GFF3" and len(user_request) >= 4 and user_request[1].isdigit():
            # Call format: ProjectID, annotation_mapping, feature_hierarchy, file_names
            self.set_gff3_parser(user_request[1],user_request[2], user_request[3], user_request[4:]
                if len(user_request) > 4 else [])
        # Build the neo4j-based project database from the previously added files
        if user_request[0] == "DB" and len(user_request) == 2 and user_request[1].isdigit():
            self.build_db(user_request[1])
        else:
            self.send_data("-3")

    # Build a neo4j graph database of the genes and proteins in the project data files
    # Two types of input for each species are possible:
    # (1.) Protein-fasta plus Gene annotation in GFF3 or CVS format
    # (2.) Nucleotide-fasta plus Gene annotation in GFF3 format
    # For (2.) a Protein-fasta is generated from the nucleotide sequence and then GFF3 gene annotation
    # Afterwards, the approach is the same as for (1.)
    # The build_db functions consists of multiple parts
    # After finishing each part, the task status is updated.
    # If one part fails, an error message is stored in the task result output.
    # (1.) Check for valid file combinations/input
    # (2.)
    def build_db(self, proj_id):
        # First, define a new task for the db build and return task-id to user
        task_id = self.task_mngr.define_task(proj_id, "Building project DB")
        # Send task-id to user
        self.send_data(task_id)
        # Then, retrieve the list of files in this project (excluding hidden files)
        # Only GFF3 files have the anno_mapping and feat_hierarchie field
        # For all other files, the return value for this field is None
        self.task_mngr.set_task_status(proj_id, task_id, "Collecting files")
        file_list = list(self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                              "WHERE ID(proj)={proj_id} AND file.hidden = 'False' "
                              "RETURN file.filename, file.filetype, file.species, file.variant, file.anno_mapping, "
                                               "file.feat_hierarchie ORDER BY file.filename",
                          {"proj_id":int(proj_id)}))
        # Convert file_list into a dictionary:
        file_dict = {}
        # Keys are (Species, Variant) and entries are a list of files
        for file in file_list:
            file_dict[(file[2],file[3])] = []
        for file in file_list:
            file_dict[(file[2],file[3])].append((file[0],file[1],file[4],file[5]))
        # Check if each entry in the database consists of exactly two files, one fasta and one annotation file
        # If not, remove that entry from the database
        # Also, search for gff3+nt combinations
        # The nt-fasta needs to be translated to prot-fasta guided by the GFF3-file
        # TODO: Implement this
        # Until then: Just delete nt/gff3 file combinations
        for file in file_list:
            try:
                file_combination = file_dict[(file[2],file[3])]
            # Since there are two files per db-entry, a file could belong to an entry that is already deleted
            except KeyError:
                continue
            if len(file_combination) != 2:
                del file_dict[(file[2],file[3])]
                continue
            if sorted([file_combination[0][1],file_combination[1][1]]) \
                    not in [["gff3","prot"],("gff3","nt"), ["cvs","prot"]]:
                del file_dict[(file[2], file[3])]
                continue
            if sorted([file_combination[0][1], file_combination[1][1]]) == ["gff3","nt"]:
                del file_dict[(file[2], file[3])]
                continue
        # Initialize the annotation to csv format parser
        self.task_mngr.set_task_status(proj_id, task_id, "Parsing annotation data")
        anno_to_csv_parser = AnnoToCSV(proj_id)
        # Then convert every annotation file into a Neo4j-specific CSV file format
        for species in file_dict:
            try:
                # Identify the GFF/CSV annotation file in the file_dict list by sorting the list alphabetically
                # gff < prot and csv < prot
                anno_file = sorted(file_dict[species], key=lambda x: x[1])[0]
                print(anno_file)
                anno_to_csv_parser.create_csv("_".join([species[0],species[1]]),anno_file[0], anno_file[1],
                                              anno_file[2],anno_file[3])
            except (IndexError, KeyError):
                self.task_mngr.set_task_status(proj_id, task_id, "Failed")
                self.task_mngr.add_task_results(proj_id, task_id, "Failed: Annotation parsing")
                return
        # Load the FASTA files: Modify header so that protein-ID gets recognized by BLAST+ and
        # combine all FASTA files into one large file from which the Blast-DB is build
        fasta_parser = FastaParser(proj_id)
        for species in file_dict:
            # Identify the GFF/CSV annotation file in the file_dict list by sorting the list alphabetically
            # gff < prot and csv < prot
            fasta_file = sorted(file_dict[species], key=lambda x: x[1])[0]
            print(fasta_file)




    # For one GFF3 file (or all GFF3 files) in a project, set the annotation mapper and the feature hierarchy
    # Function initializes an instance of the GFF3-parser to check the validity of the annotation mapper string
    # and the feature hierarchy string and then uses the GFF3-parser to parse the beginning of one GFF3 file.
    # Result returned by this function is the first gene and protein node retrieved by the parsing test.
    def set_gff3_parser(self, proj_id, annotation_mapping, feature_hierarchy, file_names):
        # Create a new task and return task-id to user
        task_id = self.task_mngr.define_task(proj_id, "Configure GFF3 parser")
        # Send task-id to user
        self.send_data(task_id)
        # If no file names were specified, set the GFF3 parser for all GFF3 files that are not hidden
        if not file_names:
            file_list = list(
                self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                                      "WHERE ID(proj)={proj_id} AND file.filetype = 'gff3' AND file.hidden = 'False' "
                                      "RETURN (file.filename)",
                                      {"proj_id": int(proj_id)}))
        # If file names were specified, check if they point to existing, non-hidden gff3 files
        else:
            file_list = self.main_db_conn.run(
                "MATCH(proj:Project)-[:has_files]->(fileMngr:File_Manager) WHERE ID(proj)={proj_id} "
                "MATCH (fileMngr)-[:file]->(file:File) WHERE file.filename IN {file_list} "
                "AND file.filetype = 'gff3' AND file.hidden = 'False' RETURN file.filename",
                {"proj_id": int(proj_id), "file_list": file_names})
        # Add relative path to file_list
        file_list = [os.path.join("Projects", str(proj_id), "Files", item[0]) for item in file_list]
        # First, test whether the annotation_mapping and the feature_hierarchy fulfill or formal requirements
        # For this, initialize an GFF3_parser instance
        # Do not provide a file path here as this class is used only to verify
        # the correctness of the annotation mapping and the feature hierarchy
        gff3_parser = Parser.GFF3_parser_gffutils.GFF3Parser("",0,0)
        valid_annotation_mapper = gff3_parser.set_annotation_mapper(annotation_mapping)
        valid_feature_hierarchy = gff3_parser.set_feature_hierarchy(feature_hierarchy)
        # If the gff3 parser rejects one or both of the strings, put these failure into the task status / results
        # and exit here
        if not (valid_annotation_mapper and valid_feature_hierarchy):
            self.task_mngr.set_task_status(proj_id, task_id, "failed: invalid syntax")
            self.task_mngr.add_task_results(proj_id, task_id, "Correct Annotation: " + str(valid_annotation_mapper)+ " Correct Hierarchy: "+ str(valid_feature_hierarchy))
            return
        # Else add them to the main-db
        print([os.path.basename(path) for path in file_list])
        self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(fileMngr:File_Manager) WHERE ID(proj)={proj_id} "
                    "MATCH (fileMngr)-[:file]->(file:File) WHERE file.filename IN {file_list} "
                    "AND file.filetype = 'gff3' AND file.hidden = 'False' "
                    "SET file.anno_mapping = {anno_map} SET file.feat_hierarchie = {feat_hier} ",
                    {"proj_id": int(proj_id), "file_list": [os.path.basename(path) for path in file_list],
                     "anno_map": annotation_mapping, "feat_hier": feature_hierarchy})
        self.task_mngr.set_task_status(proj_id, task_id, "Added annotation to main-db")
        # Test the parsing of each GFF3 file
        # Make a copy of all gff3-files, copying only the first 100 lines
        # For each file, try to retrieve one gene and one protein node
        # Append these nodes to final result list
        results = []
        for file in file_list:
            with open(file, "r") as original_gff3_file:
                    head = list(islice(original_gff3_file, 100))
            with open(file + "_head.gff3", "w") as head_gff3_file:
                for line in head:
                    head_gff3_file.write(line)
            gff3_parser = Parser.GFF3_parser_gffutils.GFF3Parser(file + "_head.gff3", 0, 0)
            gff3_parser.set_annotation_mapper(annotation_mapping)
            gff3_parser.set_feature_hierarchy(feature_hierarchy)
            gff3_parser.parse_gff3_file()
            try:
                gene_node = ", ".join(str(item) for item in gff3_parser.get_gene_list()[0])
            except IndexError:
                gene_node = "Error"
            try:
                protein_node = ", ".join(str(item) for item in gff3_parser.get_protein_list()[0])
            except IndexError:
                protein_node = "Error"
            results.append("\t".join([os.path.basename(file), gene_node, protein_node]))
            # Delete head of file
            os.remove(file+ "_head.gff3")
        self.task_mngr.set_task_status(proj_id, task_id, "Finished")
        self.task_mngr.add_task_results(proj_id, task_id, "\n".join(results))




