// --- TIMER ---
let seconds = RESUME_TIME_SPENT;

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

// --- RUN CODE WITH INPUT SUPPORT ---
let pendingInputResolve = null;

function waitForInput(promptText) {
  return new Promise((resolve) => {
    pendingInputResolve = resolve;
    const inputArea = document.getElementById('inputArea');
    const inputPromptText = document.getElementById('inputPromptText');
    inputArea.style.display = 'block';
    inputPromptText.textContent = promptText || '';
    const inputBox = document.getElementById('userInput');
    inputBox.value = '';
    inputBox.focus();
  });
}

function submitUserInput() {
  const val = document.getElementById('userInput').value;
  document.getElementById('inputArea').style.display = 'none';
  document.getElementById('userInput').value = '';
  if (pendingInputResolve) {
    pendingInputResolve(val);
    pendingInputResolve = null;
  }
}

document.getElementById('submitInput').addEventListener('click', submitUserInput);
document.getElementById('userInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitUserInput();
});

document.getElementById('runBtn').addEventListener('click', async () => {
  const code = document.getElementById('codeEditor').value;
  const outputEl = document.getElementById('output');
  outputEl.textContent = 'Running...';
  document.getElementById('inputArea').style.display = 'none';

  // Check if code contains input() calls
  if (code.includes('input(')) {
    // Extract all input() calls and their prompts
    const inputRegex = /input\s*\(\s*([^)]*)\s*\)/g;
    const inputs = [];
    let match;
    let modifiedCode = code;

    while ((match = inputRegex.exec(code)) !== null) {
      const promptRaw = match[1].trim();
      const promptText = promptRaw.replace(/^['"]|['"]$/g, '');
      inputs.push(promptText);
    }

    // Collect all inputs from user one by one
    const userValues = [];
    outputEl.textContent = '';
    for (let i = 0; i < inputs.length; i++) {
      const val = await waitForInput(inputs[i] || `Input ${i + 1}:`);
      userValues.push(val);
      outputEl.textContent += (inputs[i] ? inputs[i] : '') + val + '\n';
    }

    // Now run code with collected inputs piped in
    try {
      const res = await fetch('/run_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, inputs: userValues })
      });
      const data = await res.json();
      outputEl.textContent = data.output || data.error;
    } catch (e) {
      outputEl.textContent = 'Error: Could not connect to server.';
    }

  } else {
    // No input() — run normally
    try {
      const res = await fetch('/run_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, inputs: [] })
      });
      const data = await res.json();
      outputEl.textContent = data.output || data.error;
    } catch (e) {
      outputEl.textContent = 'Error: Could not connect to server.';
    }
  }
});

// --- SAVE SESSION ---
document.getElementById('saveBtn').addEventListener('click', async () => {
  const topic = document.getElementById('topic').value.trim();
  const msg = document.getElementById('saveMsg');
  if (!topic) {
    msg.textContent = '⚠ Please enter a topic name.';
    msg.className = 'save-msg error';
    return;
  }

  clearInterval(timerInterval);

  const payload = {
    session_id: RESUME_SESSION_ID,
    challenge_id: CHALLENGE_ID,
    topic,
    difficulty: document.getElementById('difficulty').value,
    status: document.getElementById('status').value,
    time_spent: seconds,
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
      const totalMins = Math.floor(seconds / 60);
      const totalSecs = seconds % 60;
      const action = RESUME_SESSION_ID ? 'updated' : 'saved';
      msg.textContent = `✅ Session ${action}! Time: ${totalMins}m ${totalSecs}s`;
      msg.className = 'save-msg success';
    }
  } catch (e) {
    msg.textContent = '❌ Failed to save.';
    msg.className = 'save-msg error';
  }
});