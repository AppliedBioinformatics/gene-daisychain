# This class provides the functionality to delete a project and is part of the project management package
# Main function "run" sends project ID back to user to signal that deletion has started, "-1" if project was not found
# or project database could not be shutdown
# Finally, project is marked in main-db as deleted
import os, subprocess, shutil, time


class DeleteProject:
    def __init__(self, proj_id, main_db_connection, send_data):
        self.proj_id = int(proj_id)
        self.main_db_conn = main_db_connection
        self.send_data = send_data

    # Trigger the deletion of a project
    # 1. Check if project-ID is valid
    # 2. Stop project graph database
    # 3. Delete files
    # 4. Set project status to deleted
    def run(self):
        try:
            project_path = os.path.join("Projects", str(self.proj_id))
            shutdown_returncode = subprocess.run([os.path.join(project_path, "proj_graph_db", "bin", "neo4j"), "stop"]).returncode
            # If project graph shutdown was not successful, cancel project deletion
            # Return "-1" to signal failure
            if int(shutdown_returncode) != 0:
                self.send_data("-1")
                return
            # Else Send project_id back to user to signal that project was found and is now going to be deleted
            else:
                self.send_data(str(self.proj_id))
            # Delete main db entry for project
            # this includes the entries for files, edits and tasks
            # Delete project file manager and files
            self.main_db_conn.run(
                "MATCH (proj:Project)-[:has_files]->(fileMngr:File_Manager) WHERE ID(proj)={proj_id} "
                "OPTIONAL MATCH (fileMngr)-[:files]->(file:File) "
                "DETACH DELETE (file) "
                "DETACH DELETE (fileMngr)", {"proj_id": self.proj_id})

            # Delete project task manager and tasks
            self.main_db_conn.run(
                "MATCH (proj:Project)-[:has_tasks]->(taskMngr:Task_Manager) WHERE ID(proj)={proj_id} "
                "OPTIONAL MATCH (taskMngr)-[:tasks]->(task:Task) "
                "DETACH DELETE (task) "
                "DETACH DELETE (taskMngr)", {"proj_id": self.proj_id})

            # Delete project edit manager and edits
            self.main_db_conn.run(
                "MATCH (proj:Project)-[:has_edits]->(editMngr:Edit_Manager) WHERE ID(proj)={proj_id} "
                "OPTIONAL MATCH (editMngr)-[:edits]->(edit:Edit) "
                "DETACH DELETE (edit) "
                "DETACH DELETE (editMngr)", {"proj_id": self.proj_id})

            try:
                proj_bolt_port_nr = int(self.main_db_conn.run("MATCH(del_proj:Project) WHERE ID(del_proj) = {proj_id} "
                                                              "RETURN del_proj.bolt_port",
                                                              {"proj_id": int(self.proj_id)}).single()[0])
                proj_http_port_nr = int(self.main_db_conn.run("MATCH(del_proj:Project) WHERE ID(del_proj) = {proj_id} "
                                                              "RETURN del_proj.http_port",
                                                              {"proj_id": int(self.proj_id)}).single()[0])
                # Set ports used for project graph db as inactive
                self.main_db_conn.run(
                    "MATCH (:Port_Manager)-[:has_port]->(projPort:Port) WHERE projPort.nr = {proj_port} "
                    "REMOVE projPort.project "
                    "SET projPort.status='inactive'", {"proj_port": proj_bolt_port_nr})

                self.main_db_conn.run(
                    "MATCH (:Port_Manager)-[:has_port]->(projPort:Port) WHERE projPort.nr = {proj_port} "
                    "REMOVE projPort.project "
                    "SET projPort.status='inactive'", {"proj_port": proj_http_port_nr})
            except:
                # If project or project port cannot be found, signal failure by sending -1 back to user
                pass

            # Delete project main db entry
            self.main_db_conn.run("MATCH(del_proj:Project) WHERE ID(del_proj) = {proj_id} "
                        "DETACH DELETE del_proj "
                        , {"proj_id": self.proj_id})

            # Finally delete project folder
            # Wait 60 seconds for Neo4j shutdown
            time.sleep(60)
            shutil.rmtree(project_path, ignore_errors=True)
        except:
            pass
        finally:
            self.main_db_conn.close()
