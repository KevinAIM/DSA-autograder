// Runs on every Canvas page
// Detects if we're on an assignment submission page and adds the autograder button

function isAssignmentPage() {
    // Canvas assignment URLs look like:
    // /courses/204637/assignments/2371092
    return window.location.pathname.match(/\/courses\/\d+\/assignments\/\d+/);
}

function addAutograderButton() {
    // Don't add button if it already exists
    if (document.getElementById('autograder-btn')) return;

    // Find the assignment container — exists for both teachers and students
    const container = document.querySelector('#assignment_show');
    if (!container) return;

    // Create button
    const btn = document.createElement('button');
    btn.id = 'autograder-btn';
    btn.textContent = 'Get Autograder Feedback';
    btn.style.cssText = `
        margin-top: 10px;
        padding: 8px 16px;
        background-color: #8B0000;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        display: block;
    `;

    // Create feedback panel
    const panel = document.createElement('div');
    panel.id = 'autograder-panel';
    panel.style.cssText = `
        margin-top: 10px;
        padding: 12px;
        background: #f9f9f9;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-family: monospace;
        white-space: pre-wrap;
        display: none;
    `;

    btn.addEventListener('click', async () => {
        panel.style.display = 'block';
        panel.textContent = 'Running autograder...';

        try {
            const response = await fetch('http://localhost:5000/grade', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    course_id: getCourseId(),
                    assignment_id: getAssignmentId()
                })
            });

            const data = await response.json();
            panel.textContent = data.output || 'No output received.';
        } catch (err) {
            panel.textContent = 'Error: Could not connect to autograder. Make sure the local server is running.';
        }
    });

    // Append button and panel to the assignment container
    container.appendChild(btn);
    container.appendChild(panel);
}

function getCourseId() {
    const match = window.location.pathname.match(/\/courses\/(\d+)/);
    return match ? match[1] : null;
}

function getAssignmentId() {
    const match = window.location.pathname.match(/\/assignments\/(\d+)/);
    return match ? match[1] : null;
}

// Run when page loads
if (isAssignmentPage()) {
    // Wait for Canvas to finish rendering
    setTimeout(addAutograderButton, 1500);
}