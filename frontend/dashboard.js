// ==========================================
// DIGITAL TWIN DASHBOARD ENGINE
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

function switchTab(tab) {
  const overviewSec = document.getElementById("overviewSection");
  const profileSec = document.getElementById("profileSection");
  const navOverview = document.getElementById("navOverview");
  if (tab === 'profile') {
    if (overviewSec) overviewSec.classList.add("hidden");
    if (profileSec) profileSec.classList.remove("hidden");
    if (navOverview) navOverview.className = "w-full flex items-center gap-3.5 px-4 py-2.5 text-slate-400 hover:bg-slate-800/50 rounded-xl text-sm font-medium transition text-left";
  } else {
    if (profileSec) profileSec.classList.add("hidden");
    if (overviewSec) overviewSec.classList.remove("hidden");
    if (navOverview) navOverview.className = "w-full flex items-center gap-3.5 px-4 py-2.5 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded-xl text-sm font-medium transition text-left";
  }
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

function refreshUserDisplay() {
  const fullName = localStorage.getItem("full_name") || "Rose";
  const email = localStorage.getItem("user_email") || "rose@gmail.com";
  const userId = localStorage.getItem("user_id") || "1";
  const dob = localStorage.getItem("user_dob") || "Not set";

  const sideName = document.getElementById("sideUserName");
  const sideEmail = document.getElementById("sideUserEmail");
  const profName = document.getElementById("profFullName");
  const profEmail = document.getElementById("profEmail");
  const profId = document.getElementById("profUserId");
  const profDob = document.getElementById("profDobDisplay");
  const editName = document.getElementById("editFullName");
  const editDob = document.getElementById("editDob");

  if (sideName) sideName.innerText = fullName;
  if (sideEmail) sideEmail.innerText = email;
  if (profName) profName.innerText = fullName;
  if (profEmail) profEmail.innerText = email;
  if (profId) profId.innerText = userId;
  if (profDob) profDob.innerText = dob;
  if (editName) editName.value = fullName;
  if (editDob) editDob.value = dob !== "Not set" ? dob : "";
}

window.openBmiModal = () => { 
  const m = document.getElementById('bmiModal'); 
  if (m) { m.classList.remove('hidden'); m.style.display = 'flex'; }
};

window.closeBmiModal = () => { 
  const m = document.getElementById('bmiModal'); 
  if (m) { m.classList.add('hidden'); m.style.display = 'none'; }
};

window.openReportModal = async () => { 
  const m = document.getElementById('reportModal'); 
  if (m) { 
    m.classList.remove('hidden'); 
    m.style.display = 'flex'; 
    await fetchAndRenderReport();
  }
};

window.closeReportModal = () => { 
  const m = document.getElementById('reportModal'); 
  if (m) { m.classList.add('hidden'); m.style.display = 'none'; }
};

document.addEventListener("DOMContentLoaded", async function() {
  refreshUserDisplay();
  try {
    await fetchUserProfileAndPhenotype();
    await syncDigitalTwinOverview();
  } catch (err) {
    console.warn("API Connection Error during initial load:", err);
  }
});

async function fetchUserProfileAndPhenotype() {
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return;
  try {
    const res = await fetch(`${API_BASE}/api/user-profile/${currentUserId}`);
    if (res.ok) {
      const data = await res.json();
      if (data.bmi && data.bmi > 0) {
        const navBmi = document.getElementById("navBmiDisplay");
        const sideBmi = document.getElementById("sideBmiScore");
        const modalBmi = document.getElementById("modalBmiScore");
        if (navBmi) navBmi.innerText = `BMI: ${data.bmi}`;
        if (sideBmi) sideBmi.innerText = `${data.bmi}`;
        if (modalBmi) modalBmi.innerText = `${data.bmi}`;
      }
      if (data.bmi_category) {
        const sideCat = document.getElementById("sideBmiCategory");
        const modalCat = document.getElementById("modalBmiCategory");
        if (sideCat) sideCat.innerText = data.bmi_category.split(' ')[0];
        if (modalCat) modalCat.innerText = data.bmi_category;
      }
      if (data.assigned_phenotype && data.assigned_phenotype !== "None") {
        applyPhenotypeUI(data.assigned_phenotype, true);
      }
    }
  } catch (err) {
    console.warn("Fallback to baseline profile", err);
  }
}

async function syncDigitalTwinOverview() {
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return;

  try {
    // 1. Telemetry Data
    const telemRes = await fetch(`${API_BASE}/api/latest-telemetry/${currentUserId}`);
    if (telemRes.ok) {
      const telem = await telemRes.json();
      const scoreEl = document.getElementById("scoreDisplay");
      if (scoreEl && telem.stability_score !== undefined) {
        scoreEl.innerText = telem.stability_score;
      }

      const badgeEl = document.getElementById("syncStatusBadge");
      const pillarSyncLabel = document.getElementById("pillarSyncStatusLabel");

      if (telem.has_logged) {
        if (badgeEl) {
          badgeEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Calibrated`;
        }
        if (pillarSyncLabel) {
          pillarSyncLabel.innerText = "Synced to Twin";
          pillarSyncLabel.className = "px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        }
      } else {
        if (badgeEl) {
          badgeEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span> Uncalibrated`;
        }
        if (pillarSyncLabel) {
          pillarSyncLabel.innerText = "Pending Logs";
          pillarSyncLabel.className = "px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
        }
      }

      updateTwinNodes(telem);
    }

    // 2. Multi-Pillar Risk Diagnostic Call
    const twinRes = await fetch(`${API_BASE}/api/update-twin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: parseInt(currentUserId, 10) })
    });

    if (twinRes.ok) {
      const twinData = await twinRes.json();
      const recTextEl = document.getElementById("recommendationText");
      if (recTextEl && twinData.dynamic_intervention) {
        recTextEl.innerText = twinData.dynamic_intervention;
      }

      // If recommendations array returned, render structured diagnostic blocks
      const container = document.getElementById("recommendationTextContainer");
      if (container && twinData.recommendations && twinData.recommendations.length > 0) {
        container.innerHTML = twinData.recommendations.map(rec => {
          if (rec.type === "risk") {
            return `
              <div class="p-3 bg-rose-950/40 border border-rose-500/40 rounded-xl text-xs text-rose-200 space-y-1 mb-2">
                <p class="font-bold text-rose-400">${rec.title}</p>
                <p class="leading-relaxed text-slate-300">${rec.body}</p>
              </div>`;
          } else {
            return `
              <div class="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-xl text-xs text-emerald-200 space-y-1 mb-2">
                <p class="font-bold text-emerald-400">${rec.title}</p>
                <p class="leading-relaxed text-slate-300">${rec.body}</p>
              </div>`;
          }
        }).join("");
      }
    }

  } catch (err) {
    console.error("Digital Twin sync error:", err);
  }
}

function updateTwinNodes(telem) {
  const brainNode = document.getElementById("brainTwinNode");
  const metabolicNode = document.getElementById("metabolicTwinNode");
  const recoveryNode = document.getElementById("recoveryTwinNode");

  const optimalStyle = "w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center text-xs font-bold text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all duration-300";
  const mildStressStyle = "w-16 h-16 rounded-full bg-amber-500/20 border-2 border-amber-500 flex items-center justify-center text-xs font-bold text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)] transition-all duration-300";
  const highRiskStyle = "w-16 h-16 rounded-full bg-rose-500/20 border-2 border-rose-500 flex items-center justify-center text-xs font-bold text-rose-300 shadow-[0_0_20px_rgba(244,63,94,0.5)] animate-pulse transition-all duration-300";

  if (!telem.has_logged) {
    if (brainNode) brainNode.className = optimalStyle;
    if (metabolicNode) metabolicNode.className = optimalStyle;
    if (recoveryNode) recoveryNode.className = optimalStyle;
    return;
  }

  if (telem.is_high_risk) {
    if (metabolicNode) metabolicNode.className = highRiskStyle;
    if (brainNode) brainNode.className = mildStressStyle;
    if (recoveryNode) recoveryNode.className = telem.stability_score < 40 ? highRiskStyle : mildStressStyle;
  } else {
    if (brainNode) brainNode.className = optimalStyle;
    if (metabolicNode) metabolicNode.className = optimalStyle;
    if (recoveryNode) recoveryNode.className = optimalStyle;
  }
}

function applyPhenotypeUI(phenotypeName, isCalibrated) {
  const dashPheno = document.getElementById("dashPhenotypeDisplay");
  const profPheno = document.getElementById("profPhenotype");
  const badge = document.getElementById("dashPhenotypeBadge");

  if (dashPheno) dashPheno.innerText = phenotypeName;
  if (profPheno) profPheno.innerText = phenotypeName;
  if (badge) {
    badge.innerText = isCalibrated ? "Live Calibrated" : "Uncalibrated";
    badge.className = isCalibrated ? 
      "bg-emerald-900/40 text-emerald-300 border border-emerald-500/40 text-xs px-3.5 py-1.5 rounded-full font-medium whitespace-nowrap shrink-0" : 
      "bg-purple-900/40 text-purple-300 border border-purple-500/40 text-xs px-3.5 py-1.5 rounded-full font-medium whitespace-nowrap shrink-0";
  }
}

async function submitBmiUpdate(e) {
  e.preventDefault();
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return;
  const payload = {
    user_id: parseInt(currentUserId, 10),
    height_cm: parseFloat(document.getElementById("inputHeight")?.value || 162),
    weight_kg: parseFloat(document.getElementById("inputWeight")?.value || 58)
  };
  try {
    const res = await fetch(`${API_BASE}/api/update-bmi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeBmiModal();
      await fetchUserProfileAndPhenotype();
      await syncDigitalTwinOverview();
    }
  } catch (err) {
    console.error("BMI update failed:", err);
  }
}

async function updateUserProfile(e) {
  e.preventDefault();
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return;
  const name = document.getElementById("editFullName")?.value || "";
  const dob = document.getElementById("editDob")?.value || "";
  const newPass = document.getElementById("editNewPassword")?.value || "";
  const confirmPass = document.getElementById("editConfirmPassword")?.value || "";

  if (newPass && newPass !== confirmPass) {
    alert("New passwords do not match.");
    return;
  }

  const payload = { user_id: parseInt(currentUserId, 10), full_name: name, dob: dob };
  if (newPass) payload.password = newPass;

  try {
    const res = await fetch(`${API_BASE}/api/update-profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      localStorage.setItem("full_name", name);
      if (dob) localStorage.setItem("user_dob", dob);
      refreshUserDisplay();
      alert("Profile updated successfully!");
    }
  } catch (err) {
    console.error("Profile update failed:", err);
  }
}

async function fetchAndRenderReport() {
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return;
  try {
    const res = await fetch(`${API_BASE}/api/generate-health-report/${currentUserId}?days=30`);
    if (res.ok) {
      const data = await res.json();
      const meta = data.report_metadata;
      const analytics = data.pillar_analytics;
      const cycles = data.cycle_summary;

      const rptName = document.getElementById("rptPatientName");
      const rptPheno = document.getElementById("rptPhenotype");
      const rptBmi = document.getElementById("rptBmi");
      const rptAvgCal = document.getElementById("rptAvgCal");
      const rptWorkouts = document.getElementById("rptWorkouts");
      const cycleContainer = document.getElementById("rptCycleDetails");
      const rptHighGi = document.getElementById("rptHighGi");
      const rptBurned = document.getElementById("rptBurned");
      const rptActiveMeds = document.getElementById("rptActiveMeds");
      const rptResets = document.getElementById("rptResets");

      if (rptName) rptName.innerText = `Patient: ${meta.patient_name}`;
      if (rptPheno) rptPheno.innerText = meta.assigned_phenotype;
      if (rptBmi) rptBmi.innerText = `${meta.bmi} (${meta.bmi_category})`;
      if (rptAvgCal) rptAvgCal.innerText = `${analytics.diet.total_calories_logged} kcal`;
      if (rptWorkouts) rptWorkouts.innerText = `${analytics.exercise.total_completed_workouts} sessions`;

      if (cycleContainer) {
        if (cycles.recent_periods && cycles.recent_periods.length > 0) {
          cycleContainer.innerHTML = cycles.recent_periods.map(c => `
            <div class="flex justify-between py-1 border-b border-slate-800/40">
              <span class="font-semibold text-purple-300">Start Date: ${c.start}</span>
              <span class="text-slate-400">Flow: ${c.flow} · Cycle Length: ${c.length} Days</span>
            </div>
          `).join("");
        } else {
          cycleContainer.innerText = "No cycle data logged in the last 30 days.";
        }
      }

      if (rptHighGi) rptHighGi.innerText = `High GI Meals: ${analytics.diet.high_gi_meals_count}`;
      if (rptBurned) rptBurned.innerText = `Calories Burned: ${analytics.exercise.total_calories_burned} kcal`;
      if (rptActiveMeds) {
        const medsList = analytics.medications.active_protocol;
        rptActiveMeds.innerText = `Active Meds: ${medsList.length > 0 ? medsList.join(', ') : 'None'}`;
      }
      if (rptResets) rptResets.innerText = `Parasympathetic Resets: ${analytics.stress_and_symptoms.total_resets_completed}`;
    }
  } catch (err) {
    console.error("Report generation error:", err);
  }
}
