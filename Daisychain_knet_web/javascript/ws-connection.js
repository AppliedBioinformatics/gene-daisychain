// Create a WebSocket connection to Daisychain-client
function get_wsconn(){
  // Do we support websockets?
  if (!('WebSocket' in window) ){
    alert('Your browser does not support web-sockets, so the main functionality of this web page will not work. Please update your browser.');
  };
  // First check if there is currently an active connection, if so, close it
  if (typeof(ws_conn) != "undefined"){
    console.log("Closing old ws connection");
    ws_conn.close()
  };
  ws_conn = new WebSocket("ws://146.118.64.101:7687/");
  // Ensure websocket is closed properly upon window reload
  window.onbeforeunload = function() {
    ws_conn.onclose = function(){};
      ws_conn.close()
    };
    return ws_conn;
}

function close_wsconn(){
  ws_conn.close();
}
