# Provides task management functions to Daisychain-Server
# send_data function is handed over from Daisychain_Server
# Functions directly accessible by user query always return a string
# Some functions are used to evaluate user requests, some
# are for internal use
# Functions access the main-db
# The main-db handler is handed over in __init__
#


class TaskManagement:
    def __init__(self, main_db_driver, send_data):
        self.main_db_driver = main_db_driver
        self.send_data = send_data

    # Reply to request send from a user app
    # User_request is a list of the "_" split command
    # e.g. [STAT, ProjectID, TaskID1, TaskID2]
    def evaluate_user_request(self, user_request):
        if user_request[0]=="STAT":
            self.send_data(self.get_task_status(user_request[1], user_request[2:]))
        if user_request[0]=="RESU" and len(user_request)==3:
            self.send_data(self.get_task_result(user_request[1], user_request[2]))
        if user_request[0]=="DELE" and len(user_request)==3:
            self.send_data(self.delete_task(user_request[1], user_request[2]))
        else:
            self.send_data("-1")

    # Get the status of one or multiple tasks
    # Input format: proj_id, taskID1_taskID2_taskID3...
    # Return format: statusID1\tstatusID2\tstatusID3...
    # Returns "Unknown" for every status that could not be determined
    def get_task_status(self, project_id, task_ids):
        tasks_status = []
        for task_id in task_ids:
            try:
                with self.main_db_driver.session() as session_a:
                    task_status = session_a.run(
                        "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                        "RETURN task.status",
                        {"proj_id": int(project_id), "task_id": int(task_id)}).single()[0]
                    tasks_status.append(task_status)
            except:
                tasks_status.append("Unknown")
        return("\t".join(tasks_status))

    # Return the result of one task
    def get_task_result(self, project_id, task_id):
        try:
            with self.main_db_driver.session() as session_b:
                task_result = session_b.run(
                    "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                    "RETURN task.results",
                    {"proj_id": int(project_id), "task_id": int(task_id)}).single()[0]
            # Delete task from database
            with self.main_db_driver.session() as session_c:
                session_c.run(
                    "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                    "DETACH DELETE task",
                    {"proj_id": int(project_id), "task_id": int(task_id)})
            return(task_result)
        except:
            return("-1")

    # Delete task from database
    # Input format: proj_id, task_id
    # Returns "Deleted" or "-1" in case of success/failure
    def delete_task(self, proj_id, task_id):
        try:
            with self.main_db_driver.session() as session_d:
                session_d.run(
                    "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                    "DETACH DELETE task",
                    {"proj_id": int(proj_id), "task_id": int(task_id)})
            return("Deleted")
        except:
            return("-1")


    # Define a new task
    # Adds an entry into the main-db
    # Function returns the task-ID in string format
    # The task node in the main-db has this format:
    # ID:task-id, desc:task_desc, status:task_status
    # Task-nodes are childnodes of the Task_Manager node
    # which is a childnode of the project node
    def define_task(self, project_id, task_desc):
        try:
            with self.main_db_driver.session() as session_e:
                task_id = session_e.run("MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager) WHERE ID(proj)={proj_id} "
                            "CREATE (taskMngr)-[:has_tasks]->(newTask:Task{desc:{task_desc},status:'started'})"
                            "RETURN(ID(newTask))", {"proj_id": int(project_id), "task_desc": task_desc}).single()[0]
            return (str(task_id))
        except:
            return ("-1")

            # Add results to a task-id so that user apps can fetch the results

    # Add results to an existing task node
    # Function has no return value
    # Task node is identified by its ID and project-ID
    # Task node could also be identified by its ID only,
    # but it is expected to be safer (and maybe faster) to use both IDs
    def add_task_results(self, project_id, task_id, results):
        try:
            with self.main_db_driver.session() as session_f:
                session_f.run(
                    "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                    "SET task.results={results}",
                    {"proj_id": int(project_id), "task_id": int(task_id), "results": str(results)})
        except:
            pass

    # Change the status of an existing task (node)
    # Function has no return value
    # Task node is identified by its ID and project-ID
    # Task node could also be identified by its ID only,
    # but it is expected to be safer (and maybe faster) to use both IDs
    def set_task_status(self, project_id, task_id, new_status):
        try:
            with self.main_db_driver.session() as session_g:
                session_g.run(
                    "MATCH(proj:Project)-[:has_tasks]->(taskMngr:Task_Manager)-[:has_tasks]->(task:Task) WHERE ID(proj)={proj_id} AND ID(task)={task_id} "
                    "SET task.status={new_status}",
                    {"proj_id": int(project_id), "task_id": int(task_id), "new_status": str(new_status)})
        except:
            pass
