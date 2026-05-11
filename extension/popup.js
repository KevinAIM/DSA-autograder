// Check if the Flask server is running
fetch('http://localhost:5000/ping')
    .then(r => r.json())
    .then(data => {
        const el = document.getElementById('server-status');
        el.textContent = 'Server connected';
        el.className = 'status connected';
    })
    .catch(() => {
        const el = document.getElementById('server-status');
        el.textContent = 'Server not running — start app.py';
        el.className = 'status disconnected';
    });