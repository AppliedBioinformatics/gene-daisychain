# This class retrieves and returns information about one or all projects
# It is part of the project management package

import neo4j.v1

class ProjectInfo:
    def __init__(self, project_id, main_db_driver, send_data):
        self.proj_id = project_id
        self.main_db_driver = main_db_driver
        self.send_data = send_data

    def run(self):
        # If a specific project id was submitted, return the status
        # of that project
        if self.proj_id:
            try:
                with self.main_db_driver.session() as session_a:
                    proj_status = session_a.run("MATCH(proj:Project) WHERE ID(proj)={proj_id} RETURN proj.status",
                                          {"proj_id": int(self.proj_id)}).single()[0]
                self.send_data(proj_status)
            except:
  
                self.send_data("-1")
        # If no specific project id was submitted, return a list of all projects
        else:
            try:
                with self.main_db_driver.session() as session_a:
                    proj_list = list(session_a.run(
                        "MATCH(proj:Project) RETURN proj.name AS name,ID(proj)as ID, proj.status AS status ORDER BY name "))
                # Send list of projects back to gateway->user
                self.send_data("\n".join(["\t".join([item[0], str(item[1]), item[2]]) for item in proj_list]))
            except:
                self.send_data('-1')
