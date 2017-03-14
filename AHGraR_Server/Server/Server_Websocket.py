import asyncio
import websockets
import configparser
import socket
from Server.Project_access.Query_Management import QueryManagement
from neo4j.v1 import GraphDatabase, basic_auth

class AHGraRWebSocket():

    def get_websocket(self, ip, port):
        return websockets.serve(self.handle, ip, port)

    def handle(self, websocket, path):
        # Receive command from gateway
        request = await websocket.recv()
        if request[:2] == "PA":
            reply = self.project_access(request[2:])
            await websocket.send(reply)
        else:
            await websocket.send("Invalid Request")
        return


    def get_db_conn(self):
        with open("main_db_access", "r") as pw_file:
            driver = GraphDatabase.driver("bolt://localhost:"+self.ahgrar_config["AHGraR_Server"]["main_db_bolt_port"],
                                          auth=basic_auth("neo4j",pw_file.read()),encrypted=False)
        return(driver.session())



    def project_access(self, request):
        # Split up user request
        # Some commands may contain additional "_", e.g. in file names.
        # These are exchanged to "\t" before being send via the socket connection
        # Here, these tabs are exchanged back to underscores
        user_request = [item.replace("\t", "_") for item in request.split("_")]
        if user_request[0] == "QURY":
            # Initialize query manager
            query_manager = QueryManagement(self.get_db_conn(), None)
            # Evaluate user request
            return(query_manager.evaluate_user_request(user_request[1:]))
        else:
            return("-2")

