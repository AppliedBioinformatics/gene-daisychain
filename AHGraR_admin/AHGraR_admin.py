# Local admin access to AHGraR server
# Must be run on the same host than AHGraR Server
# Provides functionality to create and delete projects
# Add files to a project and build a projects graph database
# from these files.
import configparser
import os
import socket
import time


class AHGraRAdmin:

    def __init__(self, server_app_ip, server_app_port):
        self.server_app_ip = server_app_ip
        self.server_app_port = server_app_port

    def cmdline_menu(self):
        print("Welcome to AHGraR")
        # Print options
        self.print_options()
        while True:
            # Wait for cmdline input
            user_input = input(">: ").strip()
            # Check if a number between 0-5 was entered
            # If so, perform an action
            # If not, show options again
            if not user_input.isdigit() or int(user_input) not in range(0, 6):
                self.clear_console()
                self.print_options()
                continue
            # Else, perform an action
            if user_input == "0":
                exit(0)
            actions = {"1": self.list_projects,
                       "2": self.create_project,
                       "3": self.change_project_files,
                       "4": self.build_project_db,
                       "5": self.delete_project}
            self.clear_console()
            actions[user_input]()


    def print_options(self):
        print("(1) to list available projects")
        print("(2) to create a new project")
        print("(3) to add/remove data from a project")
        print("(4) to build a projects database")
        print("(5) to delete a project")
        print("(0) to exit")


    def send_data(self, reply):
        # Add length of message to header
        message = str(len(reply)) + "|" + reply
        # Open up a connection to AHGraR-server main database
        maindb_conn = socket.create_connection((self.server_app_ip, self.server_app_port))
        # Send message
        try:
            maindb_conn.sendall(message.encode())
            return self.receive_data(maindb_conn)
        except:
            return "-1"
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
            msg_chunk = connection.recv(rcv_length).decode()
            # Subtract the actual length of the received message from the overall message length
            msg_length -= len(msg_chunk)
            msg += msg_chunk
        return(msg)


    def list_projects(self):
        proj_list = self.send_data("PMINFO")
        print(5*"\n")
        print(20*"#")
        print("Available projects: ")
        print(20 * "#")
        print("\t".join(["Name", "ID", "Status"]))
        print(20 * "-")
        print(proj_list)


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
        print(5*"\nFile list:")
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




    def build_project_db(self):
        self.list_projects()
        print("Enter ID of project")
        print("Enter '0' to cancel")
        proj_id = input("[Project-ID]>: ").strip()
        # Get file list for current project
        file_list = self.send_data("PAFILE_LIST_"+str(proj_id))
        files = [item.split("\t") for item in file_list.split("\n")]
        genome_files = [item for item in files if item[1]=="genome"]
        anno_files  = [item for item in files if item[1]=="annotation"]
        print("Found "+ str(len(genome_files))+" genome files")
        print("Found " + str(len(anno_files)) + " annotation files")
        print("We need to collect some information to parse the annotation files, is that ok?")
        for anno_file in anno_files:
            print(5*"-")
            print(anno_file[0])
            print(5 * "-")
            feat_attr= [item.split("§") for item in anno_file[2].split("$")]
            features = [item[0] for item in feat_attr]
            print("First, we need to know which feature represents whole genes (e.g. 'gene' or 'mRNA')")
            print("Available features: ")
            print(",".join(features))
            parent_feature = ""
            while parent_feature not in features:
                parent_feature = input(">:").strip()
            print("Next, we need to know which features build up a gene and which of them you want to include")
            print("Examples: 'CDS' and 'UTR'")
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
            # Filter out wrong subfeatures
            subfeature_list = [item for item in subfeature_list if item in reduced_features]
            print("Next, we need to know where a gene's name is stored. Select one attribute from one feature.")
            print("Enter in this format: feature:attribute, e.g. gene:Name")
            print("If unsure which attribute to take, select ID")
            selected_features = [parent_feature]
            selected_features.extend(subfeature_list)
            available_attributes = [item for item in feat_attr if item[0] in selected_features]
            for available_attribute in available_attributes:
                print("["+available_attribute[0]+"]"+": "+",".join(available_attribute[1:]))
            while True:
                name_feat_attr = input(">:").strip()
                if ":" in name_feat_attr:
                    name_feat_attr = name_feat_attr.split(":")
                else:
                    continue
                if name_feat_attr[0] not in selected_features:
                    continue
                else:
                    selected_feat_attr = [item for item in available_attributes if item[0] == name_feat_attr[0]][0][1:]
                    if name_feat_attr[1] not in selected_feat_attr:
                        continue
                    else:
                        break
            print(name_feat_attr)
            print("Finally, we need to know where a gene's description is stored. Select one attribute from one feature.")
            print("Enter in this format: feature:attribute, e.g. gene:Name")
            print("If you don't want this, enter 'skip'")
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
                if descr_feat_attr[0] not in selected_features:
                    continue
                else:
                    selected_feat_attr = [item for item in available_attributes if item[0] == descr_feat_attr[0]][0][1:]
                    if descr_feat_attr[1] not in selected_feat_attr:
                        continue
                    else:
                        break
            print(descr_feat_attr)
            # Send this data
            #PABULD_GFF3_ProjectID_annotationmapping_featurehierarchy_file1_file2
            msg_string = [proj_id, parent_feature, ",".join(subfeature_list),
                          ":".join(name_feat_attr),":".join(descr_feat_attr),anno_file[0]]
            msg_string = [item.replace("_","\t") for item in msg_string]
            print(self.send_data("PABULD_GFF3_"+"_".join(msg_string)))









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

if __name__ == '__main__':
    # Load config file
    ahgrar_config = configparser.ConfigParser()
    ahgrar_config.read('AHGraR_config.txt')
    # Initialize new class of AHGraR-admin
    ahgrar_admin = AHGraRAdmin("localhost", ahgrar_config['AHGraR_Server']['server_app_port'])
    ahgrar_admin.cmdline_menu()







