let statusPath = window.location.href + "/status";
let f = () => fetch(statusPath).then(res => {
	if(res.status == 418) {
		return new Promise(r => setTimeout(r, 2000)).then(f)
	}
	if(!res.ok) {
		return
	}
	return res.text().then(b => {
		document.getElementById("task-status").innerHTML = b;
	})
});
f()
