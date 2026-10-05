// ==========================================
// CYCLE TRACKER ENGINE
// Digital Twin PMOS Menstrual Telemetry
// ==========================================

const API_BASE = "http://127.0.0.1:8000";
let isSidebarCollapsed = false;

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  if (!sidebar) return;
  isSidebarCollapsed = !isSidebarCollapsed;
  if (isSidebarCollapsed) {
    sidebar.classList.remove("w-64");
    sidebar.classList.add("w-20", "items-center", "sidebar-collapsed");
    if (toggleBtn) toggleBtn.innerText = "▶";
  } else {
    sidebar.classList.remove("w-20", "items-center", "sidebar-collapsed");
    sidebar.classList.add("w-64");
    if (toggleBtn) toggleBtn.innerText = "◀";
  }
}

window.toggleSidebar = toggleSidebar;

function getCleanUserId() {
  const raw = localStorage.getItem("user_id");
  if (!raw) {
    window.location.href = "login.html";
    return null;
  }
  const clean = parseInt(raw, 10);
  return isNaN(clean) ? null : clean;
}

document.addEventListener("DOMContentLoaded", async function() {
  const fullName = localStorage.getItem("full_name") || "User Account";
  const email = localStorage.getItem("user_email") || "user@example.com";
  const initials = fullName
    .split(" ")
    .filter(Boolean)
    .map(n => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";

  const sideAvatar = document.getElementById("sideAvatarBadge");
  const sideName = document.getElementById("sideUserName");
  const sideEmail = document.getElementById("sideUserEmail");

  if (sideAvatar) sideAvatar.innerText = initials;
  if (sideName) sideName.innerText = fullName;
  if (sideEmail) sideEmail.innerText = email;

  // Set default start date input to today if empty
  const startInput = document.getElementById("inputStartDate");
  if (startInput && !startInput.value) {
    startInput.value = new Date().toISOString().split("T")[0];
  }

  await loadTrackerSummary();
  await loadCycleHistory();
});

async function loadTrackerSummary() {
  const userId = getCleanUserId();
  if (!userId) return;

  try {
    const res = await fetch(`${API_BASE}/api/cycle-tracker/${userId}`);
    if (res.ok) {
      const data = await res.json();
      const valPhase = document.getElementById("valPhase");
      const valDay = document.getElementById("valCycleDay");
      const valOvulation = document.getElementById("valOvulation");
      const valNextPeriod = document.getElementById("valNextPeriod");
      const valGuidance = document.getElementById("valGuidance");
      const sidePhase = document.getElementById("sidebarPhaseDisplay");

      if (valPhase) valPhase.innerText = data.current_phase || "Pending Entry";
      if (valDay) valDay.innerText = data.has_logged ? `Day ${data.cycle_day}` : "Day --";
      if (valOvulation) valOvulation.innerText = data.estimated_ovulation || "--";
      if (valNextPeriod) valNextPeriod.innerText = data.next_period_date || "--";
      if (valGuidance) valGuidance.innerText = data.guidance || "";
      if (sidePhase) sidePhase.innerText = data.current_phase || "Monitored";
    }
  } catch (err) {
    console.error("Tracker summary fetch error:", err);
  }
}

async function loadCycleHistory() {
  const userId = getCleanUserId();
  if (!userId) return;

  try {
    const res = await fetch(`${API_BASE}/api/cycle-history/${userId}`);
    const tableBody = document.getElementById("historyTableBody");
    const badge = document.getElementById("historyCountBadge");

    if (res.ok) {
      const rawHistory = await res.json();

      // Deduplicate records by period start date
      const uniqueHistory = [];
      const seenDates = new Set();

      for (const item of rawHistory) {
        if (!seenDates.has(item.period_start_date)) {
          seenDates.add(item.period_start_date);
          uniqueHistory.push(item);
        }
      }

      if (badge) badge.innerText = `${uniqueHistory.length} Logged`;

      if (!tableBody) return;

      if (!uniqueHistory || uniqueHistory.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="4" class="py-6 text-center text-slate-500 text-xs">No previous periods logged yet.</td></tr>`;
        return;
      }

      tableBody.innerHTML = uniqueHistory.map(item => `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-2.5 px-3 font-semibold text-purple-300">${item.period_start_date}</td>
          <td class="py-2.5 px-3 text-slate-300">${item.cycle_length_days} Days</td>
          <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-950 text-purple-300 border border-purple-500/30">${item.flow_intensity}</span></td>
          <td class="py-2.5 px-3 text-slate-400 truncate max-w-[150px]">${item.notes || '-'}</td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Cycle history fetch error:", err);
  }
}

async function submitCycleLog(event) {
  event.preventDefault();
  const userId = getCleanUserId();
  if (!userId) return;

  const startDate = document.getElementById("inputStartDate")?.value;
  const cycleLen = parseInt(document.getElementById("inputCycleLength")?.value || 28, 10);
  const flow = document.getElementById("selectFlow")?.value || "Medium";
  const notes = document.getElementById("inputNotes")?.value || "";

  if (!startDate) {
    alert("Please select a valid period start date.");
    return;
  }

  const btn = document.getElementById("btnSaveCycle");
  if (btn) {
    btn.innerText = "Syncing Log...";
    btn.disabled = true;
  }

  try {
    const res = await fetch(`${API_BASE}/api/log-cycle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        period_start_date: startDate,
        cycle_length_days: cycleLen,
        flow_intensity: flow,
        notes: notes
      })
    });

    if (res.ok) {
      const notesInput = document.getElementById("inputNotes");
      if (notesInput) notesInput.value = "";
      
      await loadTrackerSummary();
      await loadCycleHistory();

      alert("Period entry logged successfully!");
    } else {
      alert("Failed to save entry. Check backend connection.");
    }
  } catch (err) {
    console.error("Cycle submit error:", err);
    alert("Network error saving cycle log.");
  } finally {
    if (btn) {
      btn.innerText = "Save Cycle Log";
      btn.disabled = false;
    }
  }
}

async function resetCycleData() {
  const userId = getCleanUserId();
  if (!userId) return;

  if (confirm("Are you sure you want to clear all logged period data?")) {
    try {
      const res = await fetch(`${API_BASE}/api/reset-cycle/${userId}`, { method: "POST" });
      if (res.ok) {
        await loadTrackerSummary();
        await loadCycleHistory();
        alert("All cycle records have been reset.");
      }
    } catch (err) {
      console.error("Cycle reset error:", err);
    }
  }
}
