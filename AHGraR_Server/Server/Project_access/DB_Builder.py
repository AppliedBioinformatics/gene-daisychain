# Provides project build functions to AHGraR-Server
# All functions return either a String or Null
# Functions directly accessible by user query always return a string via socket connection
import Parser.GFF3_parser_gffutils
import os
from itertools import islice


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
        else:
            self.send_data("-3")

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
                {"proj_id": proj_id, "file_list": file_names})
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
        self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(fileMngr:File_Manager) WHERE ID(proj)={proj_id} "
                    "MATCH (fileMngr)-[:file]->(file:File) WHERE file.filename IN {file_list} "
                    "AND file.filetype = 'gff3' AND file.hidden = 'False' "
                    "SET file.anno_mapping = {anno_map} SET file.feat_hierarchie = {feat_hier} ",
                    {"proj_id": proj_id, "file_list": file_list, "anno_map": annotation_mapping, "feat_hier": feature_hierarchy})
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
            print(file+ "_head.gff3")
            gff3_parser = Parser.GFF3_parser_gffutils.GFF3Parser(file + "_head.gff3", 0, 0)
            gff3_parser.set_annotation_mapper(annotation_mapping)
            gff3_parser.set_feature_hierarchy(feature_hierarchy)
            gff3_parser.parse_gff3_file()
            try:
                gene_node = ", ".join(str(item) for item in gff3_parser.get_gene_list()[0])
                print(gene_node)
            except IndexError:
                gene_node = "Error"
            try:
                protein_node = ", ".join(str(item) for item in gff3_parser.get_protein_list()[0])
                print(protein_node)
            except IndexError:
                protein_node = "Error"
            results.append("\t".join([os.path.basename(file), gene_node, protein_node]))
            # Delete head of file
            os.remove(file+ "_head.gff3")
        self.task_mngr.set_task_status(proj_id, task_id, "Finished")
        self.task_mngr.add_task_results(proj_id, task_id, "\n".join(results))




