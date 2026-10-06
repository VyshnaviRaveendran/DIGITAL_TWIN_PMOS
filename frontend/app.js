// ==========================================
// 1. DIGITAL TWIN HEALTH LOG SYNCHRONIZATION
// ==========================================
const syncBtn = document.getElementById('syncBtn');
if (syncBtn) {
    syncBtn.addEventListener('click', async () => {
        const userId = localStorage.getItem('user_id');
        if (!userId) {
            alert("Session expired or user not logged in. Please log in first.");
            window.location.href = "login.html";
            return;
        }
        const diet = parseFloat(document.getElementById('diet').value);
        const sleep = parseFloat(document.getElementById('sleep').value);
        const exercise = parseFloat(document.getElementById('exercise').value);
        const meds = parseFloat(document.getElementById('meds').value);
        const stress = parseFloat(document.getElementById('stress').value);

        const riskDisplay = document.getElementById('riskValue');
        const textDisplay = document.getElementById('interventionText');
        const indicator = document.getElementById('statusIndicator');
        const statusMsg = document.getElementById('statusMessage');
        const twinCard = document.getElementById('twinResponseCard');

        if (statusMsg) statusMsg.innerText = "Transmitting state vector payload...";
        if (indicator) indicator.className = "h-2 w-2 rounded-full bg-yellow-500 animate-ping";

        const payload = {
            user_id: parseInt(userId),
            diet_quality: diet,
            sleep_hours: sleep,
            exercise_minutes: exercise,
            medication_taken: meds,
            stress_level: stress
        };
        try {
            const response = await fetch('http://127.0.0.1:8000/api/update-twin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                throw new Error(`Server returned HTTP Error Status: ${response.status}`);
            }
            const data = await response.json();
            if (riskDisplay) riskDisplay.innerText = data.symptom_risk_coefficient.toFixed(2);
            if (textDisplay) textDisplay.innerText = data.dynamic_intervention;

            if (data.symptom_risk_coefficient > 0.6) {
                if (riskDisplay) riskDisplay.className = "text-5xl font-black font-mono text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.3)]";
                if (twinCard) twinCard.className = "bg-slate-800 p-6 rounded-2xl border-2 border-red-500/80 shadow-[0_0_30px_rgba(239,68,68,0.15)] min-h-[350px] flex flex-col justify-between transition-all duration-300";
                if (indicator) indicator.className = "h-2 w-2 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444]";
                if (statusMsg) statusMsg.innerText = "Anomaly Alert Flagged.";
            } else if (data.symptom_risk_coefficient > 0.3) {
                if (riskDisplay) riskDisplay.className = "text-5xl font-black font-mono text-amber-500";
                if (twinCard) twinCard.className = "bg-slate-800 p-6 rounded-2xl border-2 border-amber-500/60 shadow-xl min-h-[350px] flex flex-col justify-between transition-all duration-300";
                if (indicator) indicator.className = "h-2 w-2 rounded-full bg-amber-500";
                if (statusMsg) statusMsg.innerText = "Warning: Fluctuating State Vector.";
            } else {
                if (riskDisplay) riskDisplay.className = "text-5xl font-black font-mono text-teal-400 drop-shadow-[0_0_10px_rgba(45,212,191,0.2)]";
                if (twinCard) twinCard.className = "bg-slate-800 p-6 rounded-2xl border-2 border-teal-500/60 shadow-[0_0_25px_rgba(45,212,191,0.1)] min-h-[350px] flex flex-col justify-between transition-all duration-300";
                if (indicator) indicator.className = "h-2 w-2 rounded-full bg-teal-400";
                if (statusMsg) statusMsg.innerText = "Digital Twin synchronization complete.";
            }
        } catch (error) {
            console.error("Transmission Failure Error Log:", error);
            if (riskDisplay) {
                riskDisplay.innerText = "ERR";
                riskDisplay.className = "text-5xl font-black font-mono text-rose-600";
            }
            if (twinCard) twinCard.className = "bg-slate-800 p-6 rounded-2xl border-2 border-rose-600/80 shadow-md min-h-[350px] flex flex-col justify-between";
            if (textDisplay) textDisplay.innerText = "Could not establish data link connection to the Python computational server engine. Verify your uvicorn server terminal is awake and actively running.";
            if (indicator) indicator.className = "h-2 w-2 rounded-full bg-rose-600";
            if (statusMsg) statusMsg.innerText = "Data Link Disconnected.";
        }
    });
}

// ==========================================
// 2. SIGNUP FORM HANDLER
// ==========================================
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        try {
            const response = await fetch("http://127.0.0.1:8000/api/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    password: password
                })
            });
            const data = await response.json();
            if (response.ok) {
                alert("Account registered successfully! Redirecting to login...");
                window.location.href = "login.html";
            } else {
                alert(data.detail || "Signup failed. Please try again.");
            }
        } catch (error) {
            console.error("Signup error:", error);
            alert("Could not connect to the backend server.");
        }
    });
}

// ==========================================
// 3. LOGIN FORM HANDLER
// ==========================================
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        try {
            const response = await fetch("http://127.0.0.1:8000/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email, password: password })
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem("user_token", data.access_token || 'sample_token_xyz');
                localStorage.setItem("user_id", data.user_id);
                localStorage.setItem("full_name", data.full_name);
                localStorage.setItem("user_email", email);
                alert(`Welcome back, ${data.full_name}!`);
                window.location.href = data.has_assessed ? "dashboard.html" : "intake.html";
            } else {
                alert(data.detail || "Invalid login credentials.");
            }
        } catch (error) {
            console.error("Login error:", error);
            alert("Could not connect to the backend server.");
        }
    });
}