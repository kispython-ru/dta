let ws = new WebSocket(window.location.href + "/ws");
ws.onmessage = (e) => {
	document.getElementById("task-status").innerHTML = e.data
}
