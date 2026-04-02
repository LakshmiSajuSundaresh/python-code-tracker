// --- TIMER: starts from previous time if resuming ---
let seconds = RESUME_TIME_SPENT * 60;

function updateTimerDisplay() {
  const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
  const secs = String(seconds % 60).padStart(2, '0');
  document.getElementById('timerDisplay').textContent = `${mins}:${secs}`;
}

updateTimerDisplay();

let timerInterval = setInterval(() => {
  seconds++;
  updateTimerDisplay();
}, 1000);

// --- RUN CODE ---
document.getElementById('runBtn').addEventListener('click', async () => {
  const code = document.getElementById('codeEditor').value;
  const outputEl = document.getElementById('output');
  outputEl.textContent = 'Running...';
  try {
    const res = await fetch('/run_code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    const data = await res.json();
    outputEl.textContent = data.output || data.error;
  } catch (e) {
    outputEl.textContent = 'Error: Could not connect to server.';
  }
});

// --- SAVE / UPDATE SESSION ---
document.getElementById('saveBtn').addEventListener('click', async () => {
  const topic = document.getElementById('topic').value.trim();
  const msg = document.getElementById('saveMsg');
  if (!topic) {
    msg.textContent = '⚠ Please enter a topic name.';
    msg.className = 'save-msg error';
    return;
  }

  clearInterval(timerInterval);
  const minutesTaken = Math.ceil(seconds / 60);

  const payload = {
    session_id: RESUME_SESSION_ID,
    challenge_id: CHALLENGE_ID,
    topic,
    difficulty: document.getElementById('difficulty').value,
    status: document.getElementById('status').value,
    time_spent: minutesTaken,
    notes: document.getElementById('notes').value,
    code: document.getElementById('codeEditor').value
  };

  try {
    const res = await fetch('/save_session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      const action = RESUME_SESSION_ID ? 'updated' : 'saved';
      msg.textContent = `✅ Session ${action}! Total time: ${minutesTaken} min`;
      msg.className = 'save-msg success';
    }
  } catch (e) {
    msg.textContent = '❌ Failed to save.';
    msg.className = 'save-msg error';
  }
});