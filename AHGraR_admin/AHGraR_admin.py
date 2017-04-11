# Local admin access to AHGraR server
# Must be run on the same host than AHGraR Server
# Provides functionality to create and delete projects
# Add files to a project and build a projects graph database
# from these files.
import configparser
import os
import socket
import time
import re


class AHGraRAdmin:

    def __init__(self, server_app_ip, server_app_port):
        self.server_app_ip = server_app_ip
        self.server_app_port = server_app_port

    def cmdline_menu(self):
        while True:
            self.clear_console()
            print("Welcome to AHGraR")
            # Print options
            self.print_options()
            # Wait for cmdline input
            user_input = input(">: ").strip()
            # Check if a number between 0-5 was entered
            # If so, perform an action
            # If not, show options again
            if not user_input.isdigit() or int(user_input) not in range(0, 8):
                continue
            # Else, perform an action
            if user_input == "0":
                exit(0)
            actions = {"1": self.list_projects,
                       "2": self.create_project,
                       "3": self.change_project_files,
                       "4": self.build_project_db,
                       "5": self.delete_project,
                       "6": self.query,
                       "7": self.show_tasks}
            self.clear_console()
            actions[user_input]()


    def print_options(self):
        print("(1) to list available projects")
        print("(2) to create a new project")
        print("(3) to add/remove data from a project")
        print("(4) to build a projects database")
        print("(5) to delete a project")
        print("(6) to test queries")
        print("(7) to show active tasks")
        print("(0) to exit")

    def query(self):
        while True:
            query = input("[Query]>: ").strip()
            if query == "exit":
                break
            print(self.send_data(query))

    def send_data(self, reply):
        # Add length of message to header
        message = str(len(reply)) + "|" + reply
        # Open up a connection to AHGraR-server main database
        maindb_conn = socket.create_connection((self.server_app_ip, self.server_app_port))
        # Send message
        try:
            maindb_conn.sendall(message.encode())
            return self.receive_data(maindb_conn)
        except UnicodeDecodeError as e:
            return "Error while communicating with the server: \n"+e.str(e)
        finally:
            maindb_conn.close()


    # Receive data coming in from server
    def receive_data(self, connection):
        # First, determine the length of the message
        # The message has a header containing the length
        # of the actual message:
        # e.g. 123|Data bla bla
        # First, receive data bytewise until the "|" is detected
        msg_header = ""
        while True:
            incoming_data = connection.recv(1).decode()
            if incoming_data == "|":
                break
            else:
                msg_header += incoming_data
        # Store length of the actual message
        msg_length = int(msg_header)
        # Start to build up the actual message
        msg = ""
        # Receive chunks of data until the length of the received message equals the expected length
        while msg_length > 0:
            # Receive a max. of 1024 bytes
            rcv_length = 1024 if msg_length >= 1024 else msg_length
            msg_chunk = connection.recv(rcv_length).decode(errors='replace')
            # Subtract the actual length of the received message from the overall message length
            msg_length -= len(msg_chunk)
            msg += msg_chunk
        return(msg)


    def list_projects(self):
        proj_list = self.send_data("PMINFO")
        proj_list_rows = proj_list.split("\n")
        proj_list_rows = [item.split("\t") for item in proj_list_rows]
        proj_names = ["Name"]+[item[0] for item in proj_list_rows]
        max_name_length = len(max(proj_names))
        print(proj_names)
        print(max_name_length)
        return
        proj_names = [item.ljust(max_name_length) for item in proj_names]
        proj_ids = ["ID"]+[item[1] for item in proj_list_rows]
        max_id_length = len(max(proj_ids))
        proj_ids = [item.ljust(max_id_length) for item in proj_ids ]
        proj_status = ["Status"]+[item[2] for item in proj_list_rows]
        max_status_length = len(max(proj_status))
        proj_status = [item.ljust(max_status_length) for item in proj_status]
        proj_list_formated =  zip(proj_names, proj_ids, proj_status)
        proj_list_formated = [" ".join(item) for item in proj_list_formated]
        row_length = max_name_length+max_id_length+max_status_length+2
        print(row_length*"-")
        print(row_length * "-")
        print("Available projects: ")
        print(row_length * "-")
        print(row_length * "-")
        for row in proj_list_formated:
            print(row)
            print(row_length * "-")
        # Wait for cmdline input
        print("Press enter to continue")
        user_input = input(">: ").strip()


    def create_project(self):
        print("Enter name for new project")
        print("Enter '0' to cancel")
        proj_name = input("[Create]>: ").strip()
        if proj_name == "0":
            return
        # Remove any special characters from future project name
        proj_name = "".join(char for char in proj_name if char.isalnum())
        if proj_name:
            new_proj_id = self.send_data("PMCREA_"+proj_name)
            print("Created new project "+proj_name+ " with ID "+new_proj_id)
        else:
            print("Invalid project name")


    def change_project_files(self):
        self.list_projects()
        print("\n\nEnter ID of project to access files")
        print("Enter '0' to cancel")
        proj_id = input("[Project-ID]>: ").strip()
        if proj_id == "0":
            return
        self.clear_console()
        file_list = self.send_data("PAFILE_LIST_"+proj_id)
        self.clear_console()
        print(file_list)
        while True:
            # Wait for cmdline input
            print(5*"\n")
            print("(1) to batch import files")
            print("(2) to delete a file")
            print("(0) to return")
            user_input = input("[File]>: ").strip()
            if user_input == "0":
                return
            if user_input == "1":
                print("File import requires a CSV file describing each file")
                print("The columns are:")
                print("Species_name, Variant, filetype, file_path")
                print("Filetypes are either 'genome' for genomic sequences in FASTA format")
                print("or 'annotation' for GFF3 annotation files")
                print("Example:")
                print("E.coli,K12,genome,/path/to/genome.fa")
                print("E.coli,K12,annotation,/path/to/annotation.gff3")
                user_input = input("[File]>: ").strip()
                if os.path.isfile(user_input):
                    print("valid file")
                    with open(user_input, "r") as file:
                        file_content = file.read()
                    # Replace any underscores by "\t"
                    file_content = file_content.replace("_","\t")
                    print(self.send_data("PAFILE_IMPO_"+str(proj_id)+"_"+file_content))
                    time.sleep(20)
                else:
                    print("try again")



    # Build a projects database
    # There is some user input required to correctly parse the GFF3 annotation file
    # This can be done in a semi-automatic mode or more manually
    def build_project_db(self):
        # First, let user select a project
        self.list_projects()
        print(3*"\n")
        print("Enter ID of project")
        print("\n")
        print("Enter '0' to cancel")
        proj_id = input("[Project-ID]>: ").strip()
        # Get file list for current project
        file_list = self.send_data("PAFILE_LIST_"+str(proj_id))
        files = [item.split("\t") for item in file_list.split("\n")]
        # Count number of genome and annotation files
        genome_files = [item for item in files if item[1]=="genome"]
        anno_files  = [item for item in files if item[1]=="annotation"]
        print("Found "+ str(len(genome_files))+" genome files")
        print("Found " + str(len(anno_files)) + " annotation files")
        # Check if each annotation file has a matching genome file
        # If not, ignore that annotation file for the database build
        genome_file_species_names = [item[0][:item[0].rfind(".")] for item in genome_files]
        anno_files = [item for item in anno_files if item[0][:item[0].rfind(".")] in genome_file_species_names]
        # Iterate over all annotation files
        # Sometimes a loop might need to be repeated. Work therefore with index numbers for the loop iterations
        anno_file_index = 0
        while anno_file_index < len(anno_files):
            # Get current annotation file
            anno_file = anno_files[anno_file_index]
            self.clear_console()
            print(3*"\n")
            print(5*"-")
            # Recover species name from file name
            species = anno_file[0][:anno_file[0].rfind(".")].split("_")
            print("Parsing annotation file for "+" ".join(species[:2]))
            print(5 * "-")
            # Use automatic parsing or manual parsing?
            print("Parsing the annotation file is rocket science. Use automatic (a) or manual (m) mode?")
            while True:
                mode = input(">:").strip()
                if mode not in ["a", "m"]:
                    continue
                manual_mode = mode == "m"
                break
            # Manual mode
            if manual_mode:
                # Retrieve all features and their attributes from the current GFF3 file
                feat_attr= [item.split("§") for item in anno_file[2].split("$")]
                features = [item[0] for item in feat_attr]
                # If there are no features, continue with next file
                if len(features) == 0:
                    anno_file_index += 1
                    continue
                print("First, we need to know which features in the annotation file represent whole genes.")
                print("This is most likely some feature called 'gene' or 'mRNA'")
                print("Available features: ")
                print(",".join(features))
                parent_feature = ""
                # Loop until a valid feature name for highest-level gene featurewas entered
                while parent_feature not in features:
                    parent_feature = input("[Feature name]>:").strip()
                # Collect subfeatures of gene feature
                self.clear_console()
                print(3 * "\n")
                print("A gene can consist of multiple subfeatures.")
                print("Next, we need to know which features build up the gene and which of them you want to include.")
                print("Examples: 'CDS' and 'UTR'. Sometimes there are no subfeatures.")
                print("Select subfeatures from list of available features.")
                # Don't show gene feature again
                reduced_features = [item for item in features if item != parent_feature]
                print("Available features: ")
                print(",".join(reduced_features))
                print("Select features to include, one at a time, type 'done' to go to the next step")
                subfeature_list = []
                while True:
                    sub_feature = input(">:").strip()
                    if sub_feature == "done":
                        break
                    else:
                        subfeature_list.append(sub_feature)
                # Filter out typos and non-existing subfeatures subfeatures
                subfeature_list = [item for item in subfeature_list if item in reduced_features]
                self.clear_console()
                print(3 * "\n")
                print("The annotation parser automatically derives a name for each gene. Sometimes a more common gene name\n "
                      "is stored in the attributes section of the annotation file. Each feature can hold different\n "
                      "attributes. Next, select a feature and an attribute of that feature that carries the genes name.")
                print("Enter in this format: feature:attribute, e.g. gene:Name")
                print("If unsure which attribute to take, type 'skip'.")
                selected_features = [parent_feature]
                selected_features.extend(subfeature_list)
                available_attributes = [item for item in feat_attr if item[0] in selected_features]
                # Print all selected features together with their attributes
                for available_attribute in available_attributes:
                    print("["+available_attribute[0]+"]"+": "+",".join(available_attribute[1:]))
                while True:
                    name_feat_attr = input(">:").strip()
                    # If skipped, take a dummy feature/attribute combination as parser config
                    # This feature/attribute combination is unlikely to be in the GFF3 file
                    # The parser skips the name attribute and takes the standard ID field as name
                    if name_feat_attr == "skip":
                        name_feat_attr = ("skip","skip")
                        break
                    if ":" in name_feat_attr:
                        name_feat_attr = name_feat_attr.split(":")
                    else:
                        continue
                    # Check if entered feature is in the list of selected features
                    if name_feat_attr[0] not in selected_features:
                        continue
                    else:
                        selected_feat_attr = [item for item in available_attributes if item[0] == name_feat_attr[0]][0][1:]
                        # Ensure that selected attribute is an attribute of the selected feature
                        if name_feat_attr[1] not in selected_feat_attr:
                            continue
                        else:
                            break
                self.clear_console()
                print(3 * "\n")
                # As for the name attribute, set the feature/attribute tuple of where to find the gene annotation
                print("Finally, we need to know where a gene's description is stored. Select one attribute from one feature.")
                print("Enter in this format: feature:attribute, e.g. gene:Name")
                print("If unsure, enter 'skip'")
                for available_attribute in available_attributes:
                    print("["+available_attribute[0]+"]"+": "+",".join(available_attribute[1:]))
                while True:
                    descr_feat_attr = input(">:").strip()
                    if descr_feat_attr == "skip":
                        descr_feat_attr = ("skip","skip")
                        break
                    if ":" in descr_feat_attr:
                        descr_feat_attr = descr_feat_attr.split(":")
                    else:
                        continue
                    # Check if entered feature is in the list of selected features
                    if descr_feat_attr[0] not in selected_features:
                        continue
                    else:
                        selected_feat_attr = [item for item in available_attributes if item[0] == descr_feat_attr[0]][0][1:]
                        # Ensure that selected attribute is an attribute of the selected feature
                        if descr_feat_attr[1] not in selected_feat_attr:
                            continue
                        else:
                            break
                self.clear_console()
                print(3 * "\n")
                # Send this parsing information to server
                msg_string = [proj_id, parent_feature, ",".join(subfeature_list),
                              ":".join(name_feat_attr),":".join(descr_feat_attr),anno_file[0]]
                msg_string = [item.replace("_","\t") for item in msg_string]
                # Receive feedback from server: (At max.) three genes that were extracted from the annotation file
                test_parsing = (self.send_data("PABULD_GFF3_"+"_".join(msg_string)))
                test_parsing = test_parsing.split("\n")
                print("Preview of annotation file parsing showing three genes extracted from the annotation file:")
                gene_count = 1
                for gene in test_parsing:
                    print(3*"\n")
                    print(5*"-"+"Gene nr. "+str(gene_count)+5*"-")
                    gene = gene.split("\t")
                    if len(gene) != 8:
                        print("Parsing failed")
                        continue
                    print("Gene name: "+gene[4])
                    print("Description: " + gene[5])
                    print("Contig name: " + gene[0])
                    print("Start: "+gene[1]+ " Stop: "+gene[2]+" Strand: "+gene[3])
                    nt_seq = gene[6]
                    if len(nt_seq) <= 30:
                        print("Transcript:  "+nt_seq)
                    else:
                        print("Transcript:  "+nt_seq[:15]+"...["+str(len(nt_seq)-30)+"]..."+nt_seq[-15:])
                    prot_seq = gene[7]
                    if len(prot_seq) <= 30:
                        print("Translation: "+prot_seq)
                    else:
                        print("Translation: "+prot_seq[:15]+"...["+str(len(prot_seq)-30)+"]..."+prot_seq[-15:])
                    print(20*"-")
                    gene_count +=1
                print(3*"\n")
            # Automatic mode: Try to guess feature names for gene feature and coding feature
            if not manual_mode:
                # First compare all features contained in this GFF against a list of known gene or coding features
                known_gene_features = re.compile("mrna|gene", re.IGNORECASE)
                known_coding_features = re.compile("cds|exon", re.IGNORECASE)
                known_name_attributes = re.compile("name", re.IGNORECASE)
                known_descr_attributes = re.compile("product|description|annotation|note", re.IGNORECASE)
                gff_feat_attr= [item.split("§") for item in anno_file[2].split("$")]
                gff_features = [item[0] for item in gff_feat_attr]
                potential_gene_features = [item for item in gff_features if known_gene_features.match(item)]
                potential_coding_features = [item for item in gff_features if known_coding_features.match(item)]
                # Iterate through every combination, until test parsing returns a good result
                parser_config = 1
                parser_dict = {}
                for potential_gene_feature in potential_gene_features:
                    for potential_coding_feature in potential_coding_features:
                        # Try to find a matching attribute for gene name in one of the features attributes
                        current_gene_feat_attr = [item for item in gff_feat_attr if item[0]==potential_gene_feature][0][1:]
                        current_coding_feat_attr = [item for item in gff_feat_attr if item[0] == potential_coding_feature][
                                                     0][1:]
                        # Filter for known gene name attributes
                        current_gene_feat_name_attr = [item for item in current_gene_feat_attr if known_name_attributes.match(item)]
                        current_coding_feat_name_attr = [item for item in current_coding_feat_attr if known_name_attributes.match(item)]
                        potential_name_feat_attr = [(potential_gene_feature, item) for item in current_gene_feat_name_attr]+\
                                                   [(potential_coding_feature, item) for item in current_coding_feat_name_attr]
                        # Try to find a matching attribute for gene description in one of the features attributes
                        current_gene_feat_descr_attr = [item for item in current_gene_feat_attr if
                                                       known_descr_attributes.match(item)]
                        current_coding_feat_descr_attr = [item for item in current_coding_feat_attr if
                                                         known_descr_attributes.match(item)]
                        potential_descr_feat_attr = [(potential_gene_feature, item) for item in
                                                    current_gene_feat_descr_attr] + \
                                                   [(potential_coding_feature, item) for item in
                                                    current_coding_feat_descr_attr]
                        # Find a placeholder if a feature/attribute tuple for the name and/or description field
                        # could not be found
                        if not potential_name_feat_attr:
                            potential_name_feat_attr = [("skip","skip")]
                        if not potential_descr_feat_attr:
                            potential_descr_feat_attr = [("skip","skip")]
                        # Iterate over all name/description combinations (part of the overall iteration over all
                        # potential gene features and coding features
                        for pnfa in potential_name_feat_attr:
                            for pdfa in potential_descr_feat_attr:
                                # For each parser config combination, retrieve a test parsing result
                                msg_string = [proj_id, potential_gene_feature, potential_coding_feature,
                                              ":".join(pnfa), ":".join(pdfa), anno_file[0]]
                                msg_string = [item.replace("_", "\t") for item in msg_string]
                                # Receive feedback from server: (At max.) three genes that were extracted from the annotation file
                                test_parsing = (self.send_data("PABULD_GFF3_" + "_".join(msg_string)))
                                test_parsing = test_parsing.split("\n")
                                # Show the first gene of the parsing result retrieved for this parser config
                                for gene in test_parsing[:1]:
                                    gene = gene.split("\t")
                                    # Skip parser configurations that failed
                                    if len(gene) != 8:
                                        continue
                                    if (not gene[0] or not gene[1] or not gene[2] or not gene[3] or not gene[4]
                                        or not gene[6] or not gene[7]):
                                        continue
                                    # Show each successfull parser configuration together with a number
                                    print(5 * "-" + "Parser config nr. " + str(parser_config) + 5 * "-")
                                    print("Gene name: " + gene[4])
                                    print("Description: " + gene[5])
                                    print("Contig name: " + gene[0])
                                    print("Start: " + gene[1] + " Stop: " + gene[2] + " Strand: " + gene[3])
                                    nt_seq = gene[6]
                                    if len(nt_seq) <= 30:
                                        print("Transcript:  " + nt_seq)
                                    else:
                                        print("Transcript:  " + nt_seq[:15] + "...[" + str(
                                            len(nt_seq) - 30) + "]..." + nt_seq[-15:])
                                    prot_seq = gene[7]
                                    if len(prot_seq) <= 30:
                                        print("Translation: " + prot_seq)
                                    else:
                                        print("Translation: " + prot_seq[:15] + "...[" + str(
                                            len(prot_seq) - 30) + "]..." + prot_seq[-15:])
                                    print(20 * "-")
                                    # Store this parser configuration together with its number
                                    # user selects one parser configuration at the end of this step
                                    parser_dict[parser_config] = [potential_gene_feature, potential_coding_feature,
                                                                pnfa, pdfa]
                                    parser_config += 1
                # If all parser configurations failed, go back to first step (decision between automatic and manual mode)
                # and offer the choice to return to the main menu
                if len(parser_dict) == 0:
                    print("Unable to retrieve a parser configuration.")
                    print("Try manual mode.")
                    print("Type ok to continue, exit to return to main menu")
                    user_selection = input(">:").strip()
                    if user_selection == "ok":
                        continue
                    else:
                        return
                # Else, let user select a parser configuration
                print("Select a parser configuration:")
                while True:
                    parser_selection = input(">:").strip()
                    if not parser_selection.isdigit():
                        continue
                    if not 0 < int(parser_selection) < parser_config:
                        continue
                    else:
                        selected_parser_config = parser_dict[int(parser_selection) ]
                        break
                # Send this parsing information to server
                msg_string = [proj_id, selected_parser_config[0], selected_parser_config[1],
                              ":".join(selected_parser_config[2]), ":".join(selected_parser_config[3]), anno_file[0]]
                msg_string = [item.replace("_", "\t") for item in msg_string]
                # Receive feedback from server: (At max.) three genes that were extracted from the annotation file
                test_parsing = (self.send_data("PABULD_GFF3_" + "_".join(msg_string)))
                test_parsing = test_parsing.split("\n")
                self.clear_console()
                print(3 * "\n")
                print(
                    "Preview of annotation file parsing showing three genes extracted from the annotation file:")
                gene_count = 1
                for gene in test_parsing:
                    print(3 * "\n")
                    print(5 * "-" + "Gene nr. " + str(gene_count) + 5 * "-")
                    gene = gene.split("\t")
                    if len(gene) != 8:
                        print("Parsing failed")
                        continue
                    print("Gene name: " + gene[4])
                    print("Description: " + gene[5])
                    print("Contig name: " + gene[0])
                    print("Start: " + gene[1] + " Stop: " + gene[2] + " Strand: " + gene[3])
                    nt_seq = gene[6]
                    if len(nt_seq) <= 30:
                        print("Transcript:  " + nt_seq)
                    else:
                        print("Transcript:  " + nt_seq[:15] + "...[" + str(len(nt_seq) - 30) + "]..." + nt_seq[
                                                                                                        -15:])
                    prot_seq = gene[7]
                    if len(prot_seq) <= 30:
                        print("Translation: " + prot_seq)
                    else:
                        print("Translation: " + prot_seq[:15] + "...[" + str(
                            len(prot_seq) - 30) + "]..." + prot_seq[-15:])
                    print(20 * "-")
                    gene_count += 1
                print(3 * "\n")

            print("Do you like what you see?")
            print("Enter 'a' to keep this parser configuration and continue with next annotation file")
            print("Enter 'r' to redo the parser configuration")
            print("Enter 'x' to exit")
            while True:
                selection = input(">:").strip()
                if selection == "x":
                    return
                elif selection == "r":
                    break
                elif selection == "a":
                    anno_file_index += 1
                    break
                else:
                    continue
        # All information required to build the project DB is now collected
        print("Starting DB build now")
        self.send_data("PABULD_DB_"+str(proj_id))



    def delete_project(self):
        self.clear_console()
        self.list_projects()
        print("Enter ID of project to delete it")
        print("Enter '0' to cancel")
        proj_id = input("[Delete]>: ").strip()
        if proj_id == "0" or not proj_id.isdigit():
            return
        print("Deleting project with ID "+proj_id)
        print("To continue, enter 'delete'")
        user_input = input("[Delete]>: ").strip()
        if user_input != "delete":
            return
        self.clear_console()
        print("Deleting project now")
        status = self.send_data("PMDELE_" + proj_id)
        if status == proj_id:
            print("Deleted project ID "+proj_id)
        else:
            print("Deletion of project ID " + proj_id + " failed")

    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_tasks(self):
        self.clear_console()
        self.list_projects()
        print("Enter ID of project to show tasks it")
        print("Enter '0' to cancel")
        proj_id = input("[Tasks]>: ").strip()
        if proj_id == "0" or not proj_id.isdigit():
            return
        while True:
            self.clear_console()
            tasks = self.send_data("PATASK_LIST_" + proj_id)
            task_list = tasks.split("\n")
            task_list = [item.split("_") for item in task_list]
            for task in task_list:
                print("\t".join(task[1:]))
            print("Enter 'clear' to remove finished tasks\n"
                  "Enter 'update' to update list")
            user_entry = input("[Tasks]>: ").strip()
            if user_entry == "clear":
                try:
                    for task in task_list:
                        if "finished" in task[2].lower():
                            self.send_data("PATASK_DELE_"+proj_id+"_"+task[0])
                except IndexError:
                    pass
                continue
            elif user_entry == "update":
                continue
            else:
                break





if __name__ == '__main__':
    # Load config file
    ahgrar_config = configparser.ConfigParser()
    ahgrar_config.read('AHGraR_config.txt')
    # Initialize new class of AHGraR-admin
    ahgrar_admin = AHGraRAdmin("localhost", ahgrar_config['AHGraR_Server']['server_app_port'])
    ahgrar_admin.cmdline_menu()







