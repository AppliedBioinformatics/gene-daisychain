# Provides file management functions to AHGraR-Server
# All functions return either a String or Null
# Functions directly accessible by user send back a string via socket connection
import os
import urllib.request
import shutil


class FileManagement:

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
        if user_request[0]=="DWNF" and len(user_request)==6 and user_request[1].isdigit():
            self.download_file(user_request[1],user_request[2],user_request[3],user_request[4],user_request[5])
        if user_request[0]=="LIST" and len(user_request)==2 and user_request[1].isdigit():
            self.file_list(user_request[1])
        if user_request[0] == "HIDF" and len(user_request) == 3 and user_request[1].isdigit():
            self.file_hide(user_request[1], user_request[2])
        if user_request[0] == "UHIF" and len(user_request) == 3 and user_request[1].isdigit():
            self.file_unhide(user_request[1], user_request[2])
        if user_request[0] == "DELF" and len(user_request) == 3 and user_request[1].isdigit():
            self.file_remove(user_request[1], user_request[2])
        if user_request[0] == "IMPO" and len(user_request) == 3 and user_request[1].isdigit():
            self.file_import(user_request[1], user_request[2])
        else:
            self.send_data("-3")

    # Download a file
    # Format: [ProjectID, species, variant, filetype, url]
    def download_file(self, proj_id, species, variant, filetype, url):
        # Check if filetype is set correct:
        # If not, send "-1" to user and return
        if filetype not in ["gff3", "nt", "prot"]:
            self.send_data("-4")
            return
        # Call task_manager to define a new task
        task_id = self.task_mngr.define_task(proj_id, "Download file")
        # Send task-id to user
        self.send_data(task_id)
        # Restore URL by replacing "\t" with "_"
        url = url.replace("\t","_")
        download_folder = os.path.join("Projects", proj_id, "Files")
        # Start download
        self.task_mngr.set_task_status(proj_id, task_id, "downloading")
        file_ending = ".gff3" if filetype == "gff3" else ".faa"
        file_name = "_".join([species, variant]) + file_ending
        try:
            with urllib.request.urlopen(url) as request_response, \
                    open (os.path.join(download_folder, file_name), 'wb') as new_file:
                shutil.copyfileobj(request_response, new_file)
        except:
            self.task_mngr.set_task_status(proj_id, task_id, "failed")
            os.remove(os.path.join(download_folder, file_name), ignore_errors=True)
            return
        self.file_manager_add_file(proj_id, species, variant, file_name, filetype)
        self.task_mngr.set_task_status(proj_id, task_id, "finished")

    def file_manager_add_file(self, proj_id, species, variant, file_name, filetype):
        self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(fileMngr:File_Manager) WHERE ID(proj)={proj_id} "
                              "MERGE (fileMngr)-[:file]->(newFile:File{species:{species},"
                              "variant:{variant},"
                              "filetype:{filetype},"
                              "filename:{file_name}"
                              "}) "
                              "SET newFile.hidden = 'False' ",
                              {"proj_id": int(proj_id), "variant": variant, "filetype": filetype,
                               "file_name":file_name, "species":species})

    # Return a list of all files associated with a project
    # Function requires only the project ID as parameter
    def file_list(self, proj_id):
        files_list = list(self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                          "WHERE ID(proj)={proj_id} RETURN file.filename, "
                          "file.hidden ORDER BY file.filename",
                          {"proj_id":int(proj_id)}))
        self.send_data("\n".join(["\t".join([item[0],item[1]]) for item in files_list]))

    # Hide a file in a project so that file is not used in future database builds
    # File can be unhided anytime again
    # Function requires project ID and file_name as parameter
    # file_name is sufficient since file names have to be unique
    def file_hide(self, proj_id, file_name):
        # Call task_manager to define a new task
        task_id = self.task_mngr.define_task(proj_id, "Hide file "+file_name)
        # Send task-id to user
        self.send_data(task_id)
        # Restore file_name by replacing "\t" with "_"
        file_name = file_name.replace("\t", "_")
        try:
            hide_file = self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                          "WHERE ID(proj)={proj_id} AND file.filename={file_name} "
                                  "SET file.hidden='True' "
                                              "RETURN(file)", {"proj_id":int(proj_id), "file_name":file_name})
            # Evaluate whether file was found
            # If file is not found, an exception is thrown
            result = hide_file.single()[0]
            # Store result of unhide in main-db
            self.task_mngr.add_task_results(proj_id, task_id, "hidden")
        except:
            # If file was not found, set task_status to failed
            self.task_mngr.set_task_status(proj_id, task_id, "failed")
            return
        # Otherwise, set task_status to finished
        self.task_mngr.set_task_status(proj_id, task_id, "finished")

        # Unhide a file in a project so that file is used in future database builds
        # File can be hided anytime again
        # Function requires project ID and file_name as parameter
        # file_name is sufficient since file names have to be unique
    def file_unhide(self, proj_id, file_name):
        # Call task_manager to define a new task
        task_id = self.task_mngr.define_task(proj_id, "Unhide file " + file_name)
        # Send task-id to user
        self.send_data(task_id)
        # Restore file_name by replacing "\t" with "_"
        file_name = file_name.replace("\t", "_")
        try:
            unhide_file = self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                                              "WHERE ID(proj)={proj_id} AND file.filename={file_name} "
                                              "SET file.hidden='False' "
                                              "RETURN(file)", {"proj_id": int(proj_id), "file_name": file_name})
            # Evaluate whether file was found
            # If file is not found, an exception is thrown
            result = unhide_file.single()[0]
            # Store result of unhide in main-db
            self.task_mngr.add_task_results(proj_id, task_id, "unhidden")
        except:
            # If file was not found, set task_status to failed
            self.task_mngr.set_task_status(proj_id, task_id, "failed")
            return
        # Otherwise, set task_status to finished
        self.task_mngr.set_task_status(proj_id, task_id, "finished")

    # Remove a file from the project folder and
    # delete its entry in the main-db
    def file_remove(self, proj_id, file_name):
        # Call task_manager to define a new task
        task_id = self.task_mngr.define_task(proj_id, "Remove file " + file_name)
        # Send task-id to user
        self.send_data(task_id)
        # Restore file_name by replacing "\t" with "_"
        file_name = file_name.replace("\t", "_")
        file_path = os.path.join("Projects", proj_id, "Files", file_name)
        try:
            os.remove(file_path)
            remove_file = self.main_db_conn.run("MATCH(proj:Project)-[:has_files]->(:File_Manager)-[:file]->(file:File) "
                                              "WHERE ID(proj)={proj_id} AND file.filename={file_name} "
                                              "DETACH DELETE (file) "
                                              "RETURN(file)", {"proj_id": int(proj_id), "file_name": file_name})
            # Evaluate whether file was found
            # If file is not found, an exception is thrown
            result = remove_file.single()[0]
            # Store result of remove action in main-db
            self.task_mngr.add_task_results(proj_id, task_id, "deleted")
        except:
            # If file was not found, set task_status to failed
            self.task_mngr.set_task_status(proj_id, task_id, "failed")
            return
        # Otherwise, set task_status to finished
        self.task_mngr.set_task_status(proj_id, task_id, "finished")

    # Batch import files from Import directory
    # Import file describes the files:
    # species,variant,filetype,filepath
    def file_import(self, proj_id, import_file_path):
        # Restore file_name by replacing "\t" with "_"
        import_file_path = import_file_path.replace("\t", "_")
        # Call task_manager to define a new task
        task_id = self.task_mngr.define_task(proj_id, "Import files from " + import_file_path)
        # Send task-id to user
        self.send_data("Importing files. Task-ID: "+str(task_id))
        # Try to open import file
        try:
            import_file = open(import_file_path, "r")
        except FileNotFoundError:
            self.task_mngr.set_task_status(proj_id, task_id, "failed")
            return
        imported_file_counter = 0
        project_file_path = os.path.join("Projects", proj_id, "Files")
        self.task_mngr.set_task_status(proj_id, task_id, "running")
        for line in import_file:
            # Remove whitespaces
            line = "".join(line.split(" "))
            new_file_desc = line.strip().split(",")
            if len(new_file_desc) != 4: continue
            new_file_path = new_file_desc[3]
            # Check if next file has valid file_type
            if new_file_desc[2] not in ["annotation", "genome", "transcript"]:
               continue
            if new_file_desc[2] == "annotation":
                file_ending = ".gff3"
            else:
                file_ending = ".faa"
            file_name = "_".join([new_file_desc[0], new_file_desc[1]]) + file_ending
            try:
                shutil.copy2(new_file_path, os.path.join(project_file_path, file_name))
                self.file_manager_add_file(proj_id, new_file_desc[0], new_file_desc[1], file_name, new_file_desc[2])
                imported_file_counter+=1
                self.task_mngr.set_task_status(proj_id, task_id, "imported "+str(imported_file_counter))
            except:
                continue
        self.task_mngr.add_task_results(proj_id, task_id, "imported "+str(imported_file_counter))
        self.task_mngr.set_task_status(proj_id, task_id, "finished ")




