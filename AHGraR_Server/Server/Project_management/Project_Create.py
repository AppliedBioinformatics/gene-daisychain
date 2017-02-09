# This class provides the functionality to create a project and is part of the project management package
# 1. Add project to AHGraR DB
# 2. Trigger the project creation function
# 3. Mark project in AHGraR DB as successfully created (or not)
import os
import shutil


class CreateProject:
    def __init__(self, project_name, neo4j_path, main_db_connection, send_data):
        self.proj_name = project_name
        self.neo4j_path = neo4j_path
        self.main_db_conn = main_db_connection
        self.send_data = send_data


    def run(self):
        # Create a new entry in the main-db for the new project and retrieve the project ID
        # Also add three subnodes to project node: Files, Tasks and Edits
        proj_id = self.main_db_conn.run("CREATE (new_proj:Project {name: {name}, status:{status}}) "
                                        "CREATE (new_proj)-[:has_tasks]->(:Task_Manager) "
                                        "CREATE (new_proj)-[:has_files]->(:File_Manager) "
                                        "CREATE (new_proj)-[:has_edits]->(:Edit_Manager) "
                                        "RETURN(ID(new_proj))",
                                 {"name": self.proj_name, "status": "INIT"}).single()[0]
        # Return project ID to gateway -> user-app
        self.send_data(proj_id)
        # Extract project port nr. from server reply
        # Reply either contains a port nr. or, if there is no free port left,
        # extracting the port nr. will fail
        # In the latter case the project will not be assigned a port nr.
        # and initialization of the project fails
        try:
            # Retrieve a BOLT port to access the project graph db (only accessible from localhost)
            request_bolt_port_nr = self.main_db_conn.run(
                "MATCH(:Port_Manager)-[:has_port]->(port:Port {status:'inactive'}) RETURN (port.nr) LIMIT(1)")
            project_bolt_port = request_bolt_port_nr.single()[0]
            # Mark BOLT port-nr in AHGRaR main DB as active
            self.main_db_conn.run("MATCH(:Port_Manager)-[:has_port]->(port:Port {nr: {port_nr}}) SET port = $props",
                                  {"props": {"status": "active", "project": proj_id, "nr": project_bolt_port},
                                   "port_nr": project_bolt_port})
            # Add project BOLT port nr to project in AHGRaR main DB
            self.main_db_conn.run("MATCH(proj:Project) WHERE ID(proj) = {project_id} SET proj.bolt_port = {port_nr}",
                                  {"project_id": proj_id, "port_nr": project_bolt_port})
            # Retrieve a HTTP port to access the project graph db (only accessible from localhost)
            request_http_port_nr = self.main_db_conn.run(
                "MATCH(:Port_Manager)-[:has_port]->(port:Port {status:'inactive'}) RETURN (port.nr) LIMIT(1)")
            project_http_port = request_http_port_nr.single()[0]
            # Mark HTTP port-nr in AHGRaR main DB as active
            self.main_db_conn.run("MATCH(:Port_Manager)-[:has_port]->(port:Port {nr: {port_nr}}) SET port = $props",
                                  {"props": {"status": "active", "project": proj_id, "nr": project_http_port},
                                   "port_nr": project_http_port})
            # Add project HTTP port nr to project in AHGRaR main DB
            self.main_db_conn.run("MATCH(proj:Project) WHERE ID(proj) = {project_id} SET proj.http_port = {port_nr}",
                                  {"project_id": proj_id, "port_nr": project_http_port})
            project_path = os.path.join("Projects", str(proj_id))
            os.makedirs(project_path)
            os.makedirs(os.path.join(project_path, "Files"))
            os.makedirs(os.path.join(project_path, "CSV"))
            os.makedirs(os.path.join(project_path, "BlastDB"))
            shutil.copytree(self.neo4j_path, os.path.join(project_path, "proj_graph_db"))
            # Edit project neo4j graph database config file
            self.edit_neo4j_config(project_path, project_bolt_port, project_http_port)
            # Mark project in DB as successfully initialized INIT_SUCCESS
            self.main_db_conn.run(
                "MATCH (proj:Project) WHERE ID(proj) = {proj_id} SET proj.status = {new_status}"
                , {"proj_id": proj_id, "new_status": "INIT_SUCCESS"})
        except:
            # In case of an error, set project status to INIT_FAILED
            self.main_db_conn.run(
                "MATCH (proj:Project) WHERE ID(proj) = {proj_id} SET proj.status = {new_status}"
                , {"proj_id": proj_id, "new_status": "INIT_FAILED"})
            # TODO Delete any remainings of the project in case INIT_FAILED
        # Always close connection to AHGRaR DB before finishing
        finally:
            self.main_db_conn.close()

    # Edit project neo4j graph database
    # Set BOLT port and HTTP port to ports assigned by main-db
    def edit_neo4j_config(self, project_path, project_bolt_port, project_http_port):
        neo4j_conf_content = []
        with open(os.path.join(project_path, "proj_graph_db", "conf", "neo4j.conf"), "r") as conf_file:
            for line in conf_file:
                if line == "#dbms.connector.bolt.listen_address=:7687\n":
                    neo4j_conf_content.append("dbms.connector.bolt.listen_address=:" + str(project_bolt_port) + "\n")
                elif line == "#dbms.connector.http.listen_address=:7474\n":
                    neo4j_conf_content.append("dbms.connector.http.listen_address=:" + str(project_http_port) + "\n")
                elif line == "dbms.connector.https.enabled=true\n":
                    neo4j_conf_content.append("dbms.connector.https.enabled=false\n")
                else:
                    neo4j_conf_content.append(line)
        with open(os.path.join(project_path,  "proj_graph_db", "conf", "neo4j.conf"), "w") as conf_file:
            for line in neo4j_conf_content:
                conf_file.write(line)




