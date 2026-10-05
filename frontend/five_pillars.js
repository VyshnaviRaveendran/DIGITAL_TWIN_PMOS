// ==========================================
// 5 PILLARS MANAGEMENT ENGINE
// Digital Twin Health PMOS System
// ==========================================

const API_BASE = "http://127.0.0.1:8000";

// Global Component State
let currentScannedCalories = 0;
let currentScannedProtein = 0;
let currentScannedCarbs = 0;
let currentScannedFats = 0;
let currentScannedClassification = "Pending Scan";
let currentTargetDuration = 25;
let currentTargetBurn = 150;
let currentWorkoutTitle = "Daily Workout";
let userMedicationsList = [];
let isSidebarCollapsed = false;
let selectedSymptoms = [];
let currentBreathingTechnique = "4-7-8";
let breathingInterval = null;

// ==========================================
// AUTHENTICATION & PROFILE HELPERS
// ==========================================
function getCleanUserId() {
  const rawUserId = localStorage.getItem("user_id");
  if (!rawUserId) {
    window.location.href = "login.html";
    return null;
  }
  const cleanId = parseInt(rawUserId, 10);
  if (isNaN(cleanId)) {
    window.location.href = "login.html";
    return null;
  }
  return cleanId;
}

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

window.openBmiModal = () => {
  const m = document.getElementById('bmiModal');
  if (m) {
    m.classList.remove('hidden');
    m.style.display = 'flex';
  }
};

window.closeBmiModal = () => {
  const m = document.getElementById('bmiModal');
  if (m) {
    m.classList.add('hidden');
    m.style.display = 'none';
  }
};

function refreshUserDisplay() {
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
}

async function refreshStabilityScore() {
  const userId = getCleanUserId();
  if (!userId) return;
  try {
    const telemRes = await fetch(`${API_BASE}/api/latest-telemetry/${userId}`);
    if (telemRes.ok) {
      const telemData = await telemRes.json();
      const scoreDisplay = document.getElementById("scoreDisplay");
      if (scoreDisplay && telemData.stability_score !== undefined) {
        scoreDisplay.innerText = telemData.stability_score;
      }
      localStorage.setItem("latest_stability", telemData.stability_score);
    }
  } catch (err) {
    console.error("Telemetry sync error:", err);
  }
}

async function fetchUserProfile() {
  const userId = getCleanUserId();
  if (!userId) return;
  try {
    const res = await fetch(`${API_BASE}/api/user-profile/${userId}`);
    if (res.ok) {
      const data = await res.json();
      const inputH = document.getElementById("inputHeight");
      const inputW = document.getElementById("inputWeight");
      const sideScore = document.getElementById("sideBmiScore");
      const modalScore = document.getElementById("modalBmiScore");
      const sideCat = document.getElementById("sideBmiCategory");
      const modalCat = document.getElementById("modalBmiCategory");

      if (data.height_cm && inputH) inputH.value = data.height_cm;
      if (data.weight_kg && inputW) inputW.value = data.weight_kg;
      if (data.bmi) {
        if (sideScore) sideScore.innerText = `${data.bmi}`;
        if (modalScore) modalScore.innerText = `${data.bmi}`;
      }
      if (data.bmi_category) {
        if (sideCat) sideCat.innerText = data.bmi_category.split(' ')[0];
        if (modalCat) modalCat.innerText = data.bmi_category;
      }
    }
  } catch (err) {
    console.error("Profile fetch error:", err);
  }
}

// ==========================================
// TAB SWITCHER
// ==========================================
function switchPillarTab(pillarName) {
  const diet = document.getElementById("pillarDietContainer");
  const ex = document.getElementById("pillarExerciseContainer");
  const sleep = document.getElementById("pillarSleepContainer");
  const meds = document.getElementById("pillarMedsContainer");
  const stress = document.getElementById("pillarStressContainer");

  const tabDiet = document.getElementById("tabPillarDiet");
  const tabEx = document.getElementById("tabPillarExercise");
  const tabSleep = document.getElementById("tabPillarSleep");
  const tabMeds = document.getElementById("tabPillarMeds");
  const tabStress = document.getElementById("tabPillarStress");

  const activeStyle = "bg-indigo-900/40 border border-indigo-500 text-indigo-300 font-semibold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 shadow-sm";
  const inactiveStyle = "bg-[#111625] border border-slate-800 text-slate-400 hover:text-indigo-300 hover:border-slate-700 px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 transition";

  [diet, ex, sleep, meds, stress].forEach(c => {
    if (c) {
      c.classList.add("hidden");
      c.classList.remove("grid");
    }
  });

  [tabDiet, tabEx, tabSleep, tabMeds, tabStress].forEach(t => {
    if (t) t.className = inactiveStyle;
  });

  if (pillarName === "exercise" && ex) {
    ex.classList.remove("hidden");
    ex.classList.add("grid");
    if (tabEx) tabEx.className = activeStyle;
    loadExerciseRecommendation();
  } else if (pillarName === "sleep" && sleep) {
    sleep.classList.remove("hidden");
    sleep.classList.add("grid");
    if (tabSleep) tabSleep.className = activeStyle;
    loadSleepRecommendation();
  } else if (pillarName === "meds" && meds) {
    meds.classList.remove("hidden");
    meds.classList.add("grid");
    if (tabMeds) tabMeds.className = activeStyle;
    loadUserMedications();
  } else if (pillarName === "stress" && stress) {
    stress.classList.remove("hidden");
    stress.classList.add("grid");
    if (tabStress) tabStress.className = activeStyle;
  } else if (diet) {
    diet.classList.remove("hidden");
    diet.classList.add("grid");
    if (tabDiet) tabDiet.className = activeStyle;
    fetchDietSummary();
    loadPhenotypeDietSuggestions();
  }
}

// ==========================================
// PILLAR 1: DIET & NUTRITION
// ==========================================
function handleFileSelect(files) {
  if (files && files[0]) {
    const file = files[0];
    const nameInput = document.getElementById('mealNameInput');
    const nameDisplay = document.getElementById('fileNameDisplay');
    const preview = document.getElementById('imagePreview');
    const placeholder = document.getElementById('uploadPlaceholder');
    const previewBox = document.getElementById('previewContainer');

    if (nameInput) nameInput.value = file.name;
    if (nameDisplay) nameDisplay.innerText = file.name;

    const reader = new FileReader();
    reader.onload = function(e) {
      if (preview) preview.src = e.target.result;
      if (placeholder) placeholder.classList.add('hidden');
      if (previewBox) {
        previewBox.classList.remove('hidden');
        previewBox.classList.add('flex');
      }
    };
    reader.readAsDataURL(file);
    scanMealWithML();
  }
}

async function scanMealWithML() {
  const mealNameEl = document.getElementById("mealNameInput");
  const mealFileName = mealNameEl ? mealNameEl.value : "Custom Meal";
  const userId = getCleanUserId();
  if (!userId) return;

  const statusBadge = document.getElementById("scanStatusBadge");
  if (statusBadge) statusBadge.innerText = "Evaluating...";

  try {
    const response = await fetch(`${API_BASE}/api/scan-meal-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, image_filename: mealFileName, meal_name: mealFileName })
    });
    const data = await response.json();
    if (response.ok) {
      const resName = document.getElementById("resMealName");
      const resCal = document.getElementById("resCalories");
      const resProt = document.getElementById("resProtein");
      const resCarb = document.getElementById("resCarbs");
      const resFat = document.getElementById("resFats");
      const tag = document.getElementById("resPhenotypeTag");

      if (resName) resName.innerText = data.meal_name;
      if (resCal) resCal.innerText = `${data.extracted_macros.calories}`;
      if (resProt) resProt.innerText = `${data.extracted_macros.protein}g`;
      if (resCarb) resCarb.innerText = `${data.extracted_macros.carbs}g`;
      if (resFat) resFat.innerText = `${data.extracted_macros.fats}g`;

      currentScannedCalories = data.extracted_macros.calories;
      currentScannedProtein = data.extracted_macros.protein;
      currentScannedCarbs = data.extracted_macros.carbs;
      currentScannedFats = data.extracted_macros.fats;
      currentScannedClassification = data.classification;

      if (tag) {
        tag.innerText = data.classification;
        if (data.classification === "High Glycemic Spike Risk") {
          tag.className = "bg-rose-900/50 text-rose-400 border border-rose-600/50 text-[10px] px-2.5 py-0.5 rounded-full font-semibold animate-pulse";
        } else if (data.classification === "Insulin Resistant Safe") {
          tag.className = "bg-amber-900/50 text-amber-300 border border-amber-600/50 text-[10px] px-2.5 py-0.5 rounded-full font-medium";
        } else {
          tag.className = "bg-emerald-900/50 text-emerald-400 border border-emerald-600/50 text-[10px] px-2.5 py-0.5 rounded-full font-medium";
        }
      }
      if (statusBadge) statusBadge.innerText = "Scanned ✓";
    }
  } catch (err) {
    console.error(err);
    if (statusBadge) statusBadge.innerText = "Error";
  }
}

async function addMealToLog() {
  const userId = getCleanUserId();
  if (!userId) return;

  const mealName = document.getElementById("resMealName")?.innerText || "Logged Meal";
  const mealSlot = document.getElementById("mealSlotSelect")?.value || "Dinner";
  const payload = {
    user_id: userId,
    meal_name: mealName,
    meal_type: mealSlot,
    calories: currentScannedCalories,
    protein: currentScannedProtein,
    carbs: currentScannedCarbs,
    fats: currentScannedFats,
    glycemic_risk: currentScannedClassification
  };

  try {
    const res = await fetch(`${API_BASE}/api/log-meal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      await fetchDietSummary();
      await loadPhenotypeDietSuggestions();
      await loadExerciseRecommendation();
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Error logging meal:", err);
  }
}

async function fetchDietSummary() {
  const userId = getCleanUserId();
  if (!userId) return;

  try {
    const res = await fetch(`${API_BASE}/api/diet-summary/${userId}`);
    if (res.ok) {
      const data = await res.json();
      const valTDEE = document.getElementById("valTDEE");
      const valLogged = document.getElementById("valLogged");
      const valRem = document.getElementById("valRemaining");

      if (valTDEE) valTDEE.innerText = Math.round(data.daily_target) || "--";
      if (valLogged) valLogged.innerText = data.logged_today || 0;
      if (valRem) valRem.innerText = Math.round(data.remaining_balance) || "--";

      const slots = ["Breakfast", "Lunch", "Dinner", "Snack"];
      slots.forEach(slot => {
        const row = document.getElementById(`slotRow_${slot}`);
        const splitValEl = document.getElementById(`val${slot}Split`);
        if (data.logged_slots && data.logged_slots.includes(slot)) {
          if (row) row.classList.add("opacity-40", "bg-slate-900/60");
          if (splitValEl) splitValEl.innerText = "✓ Logged";
        } else {
          if (row) row.classList.remove("opacity-40", "bg-slate-900/60");
          if (splitValEl) splitValEl.innerText = `${data.allowance_split ? data.allowance_split[slot] || 0 : 0} kcal`;
        }
      });

      const badge = document.getElementById("dayStatusBadge");
      const banner = document.getElementById("dayCompletedBanner");
      const addBtn = document.getElementById("addLogBtn");

      if (data.day_completed) {
        if (badge) {
          badge.innerText = "Day Complete";
          badge.className = "bg-emerald-950 text-emerald-300 border border-emerald-500/40 text-xs px-3 py-1 rounded-full font-semibold";
        }
        if (banner) banner.classList.remove("hidden");
        if (addBtn) {
          addBtn.disabled = true;
          addBtn.classList.add("opacity-50", "cursor-not-allowed");
        }
      } else {
        if (badge) {
          badge.innerText = `${data.unlogged_slots ? data.unlogged_slots.length : 4} Left`;
          badge.className = "bg-indigo-950 text-indigo-400 border border-indigo-500/30 text-xs px-3 py-1 rounded-full font-semibold";
        }
        if (banner) banner.classList.add("hidden");
        if (addBtn) {
          addBtn.disabled = false;
          addBtn.classList.remove("opacity-50", "cursor-not-allowed");
        }
      }
    }
  } catch (err) {
    console.error("Diet summary fetch error:", err);
  }
}

async function loadPhenotypeDietSuggestions() {
  const userId = getCleanUserId();
  if (!userId) return;

  const container = document.getElementById("recipeContainer");
  const recomTitle = document.getElementById("recommendationTitle");
  const recomBody = document.getElementById("recommendationBody");
  const recomBadge = document.getElementById("recomPhenoBadge");

  try {
    const res = await fetch(`${API_BASE}/api/diet-recommendations/${userId}`);
    if (res.ok) {
      const data = await res.json();
      if (!data.assigned_phenotype || data.assigned_phenotype === "Pending Assessment" || !data.recipes || data.recipes.length === 0) {
        if (recomBadge) recomBadge.innerText = "Uncalibrated";
        if (recomTitle) recomTitle.innerHTML = `<span>💡</span> Initializing Plan:`;
        if (recomBody) recomBody.innerText = "Complete your health assessment in the main dashboard to calculate personalized meal recommendations.";
        if (container) {
          container.innerHTML = `
            <div class="col-span-2 p-6 text-center bg-[#0B0F19] border border-slate-800 rounded-xl">
              <p class="text-xs text-slate-400">No calibrated recipes available yet.</p>
            </div>`;
        }
        return;
      }

      if (recomTitle) recomTitle.innerHTML = `<span>💡</span> ${data.guidance_title}`;
      if (recomBody) recomBody.innerText = data.guidance_body;
      if (recomBadge) recomBadge.innerText = data.assigned_phenotype;

      const slotIcons = { "Breakfast": "🍳", "Lunch": "🥗", "Dinner": "🍲", "Snack": "🥜" };
      if (container) {
        container.innerHTML = data.recipes.map(r => `
          <div class="bg-[#0B0F19] p-3.5 rounded-xl border ${r.is_logged ? 'border-slate-800/40 opacity-40' : 'border-slate-800 hover:border-indigo-500/40'} flex flex-col justify-between transition min-h-[125px]">
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-[10px] font-bold px-2 py-0.5 bg-indigo-950 text-indigo-300 rounded-md border border-indigo-500/30">
                  ${slotIcons[r.meal_slot] || '🍽️'} ${r.meal_slot}
                </span>
                <span class="text-xs font-bold text-indigo-400">${r.kcal} kcal</span>
              </div>
              <p class="text-xs font-bold text-white leading-snug line-clamp-1">${r.name}</p>
              <p class="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">${r.desc}</p>
            </div>
            <div class="mt-3 flex items-center justify-between pt-2 border-t border-slate-800/60">
              <span class="text-[10px] text-slate-400 font-medium">${r.protein}g P · ${r.fats}g F · GI ${r.gi}</span>
              ${r.is_logged ? 
                `<span class="text-emerald-400 font-bold text-xs">✓ Logged</span>` :
                `<button onclick="selectSuggestedRecipe('${r.meal_slot}', '${r.name.replace(/'/g, "\\'")}', ${r.kcal}, ${r.protein}, ${r.carbs}, ${r.fats})" class="bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-xs px-2.5 py-1 rounded-lg transition font-medium">+ Select</button>`
              }
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Diet suggestions fetch error:", err);
  }
}

function selectSuggestedRecipe(slot, name, kcal, protein, carbs, fats) {
  const nameInput = document.getElementById("mealNameInput");
  const slotSelect = document.getElementById("mealSlotSelect");
  const resName = document.getElementById("resMealName");
  const resCal = document.getElementById("resCalories");
  const resProt = document.getElementById("resProtein");
  const resCarb = document.getElementById("resCarbs");
  const resFat = document.getElementById("resFats");

  if (nameInput) nameInput.value = name;
  if (slotSelect) slotSelect.value = slot;
  if (resName) resName.innerText = name;
  if (resCal) resCal.innerText = `${kcal}`;
  if (resProt) resProt.innerText = `${protein}g`;
  if (resCarb) resCarb.innerText = `${carbs}g`;
  if (resFat) resFat.innerText = `${fats}g`;

  currentScannedCalories = kcal;
  currentScannedProtein = protein;
  currentScannedCarbs = carbs;
  currentScannedFats = fats;
  addMealToLog();
}

async function resetDayRollover() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (confirm("Reset day & refresh all 4 meal allowances?")) {
    try {
      const res = await fetch(`${API_BASE}/api/reset-day/${userId}`, { method: "POST" });
      if (res.ok) {
        await fetchDietSummary();
        await loadPhenotypeDietSuggestions();
        await loadExerciseRecommendation();
        await refreshStabilityScore();
      }
    } catch (err) {
      console.error(err);
    }
  }
}

// ==========================================
// PILLAR 2: EXERCISE & MOVEMENT
// ==========================================
async function loadExerciseRecommendation(advanceDay = false) {
  const userId = getCleanUserId();
  if (!userId) return;

  try {
    const url = `${API_BASE}/api/exercise-recommendation/${userId}${advanceDay ? '?advance_day=true' : ''}`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      const preservedMatchedMeal = data.last_meal_name || "Daily Target";
      const preservedTargetBurn = data.target_burn_kcal || currentTargetBurn || 150;
      currentTargetDuration = data.duration_mins || 25;
      currentTargetBurn = preservedTargetBurn;
      currentWorkoutTitle = data.workout_type || "Daily Workout";

      const dayBadge = document.getElementById("exDayBadge");
      const mainIcon = document.getElementById("exMainIcon");
      const planTitle = document.getElementById("exPlanTitle");
      const routineList = document.getElementById("exRoutineList");
      const targetDuration = document.getElementById("exTargetDuration");
      const targetBurn = document.getElementById("exTargetBurn");
      const matchedMeal = document.getElementById("exMatchedMeal");
      const subTitleEl = document.getElementById("exSubTitle");
      const btnComplete = document.getElementById("btnCompleteExercise");
      const statusLabel = document.getElementById("exStatusLabel");

      if (dayBadge) dayBadge.innerText = `📅 ${data.day || "Today"}'s Plan`;
      if (mainIcon) mainIcon.innerText = data.icon || "🏃";
      if (planTitle) planTitle.innerText = data.workout_type || "Standard Routine";
      if (routineList) routineList.innerText = data.exercises || "Light walking (30 mins)";
      if (targetDuration) targetDuration.innerText = `${data.duration_mins || 20} mins`;
      if (targetBurn) targetBurn.innerText = `${preservedTargetBurn} kcal`;
      if (matchedMeal) matchedMeal.innerText = preservedMatchedMeal;
      if (subTitleEl) subTitleEl.innerText = `${data.duration_mins || 20} Mins • ${preservedTargetBurn} Kcal Target`;

      if (data.is_completed_today) {
        if (statusLabel) {
          statusLabel.innerText = "Completed ✓";
          statusLabel.className = "text-xs font-bold text-emerald-400";
        }
        if (btnComplete) {
          btnComplete.innerHTML = "<span>✓</span> Workout Completed Today!";
          btnComplete.className = "w-full py-3.5 bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-bold text-xs rounded-xl cursor-not-allowed";
          btnComplete.disabled = true;
        }
      } else {
        if (statusLabel) {
          statusLabel.innerText = advanceDay ? "Next Day Loaded ⏭️" : "Ready to start";
          statusLabel.className = advanceDay ? "text-xs font-bold text-indigo-400" : "text-xs font-medium text-amber-400";
        }
        if (btnComplete) {
          btnComplete.innerHTML = "<span>✓</span> Mark Workout as Done for Today";
          btnComplete.className = "w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20";
          btnComplete.disabled = false;
        }
      }
    }
  } catch (err) {
    console.error("Error loading exercise recommendation:", err);
  }
}

async function markTodayExerciseDone() {
  await submitExerciseWorkout(currentWorkoutTitle, currentTargetDuration, currentTargetBurn);
  await loadExerciseRecommendation();
}

async function resetTodayExercise() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (!confirm("Are you sure you want to reset today's workout status?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/reset-exercise/${userId}`, { method: "POST" });
    if (res.ok) {
      await loadExerciseRecommendation();
      await refreshStabilityScore();
      alert("Today's exercise status has been reset.");
    }
  } catch (err) {
    console.error("Error resetting exercise status:", err);
  }
}

async function skipTodayExercise() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (!confirm("Skip today's workout and view next day's plan? (Your meal calorie target will be preserved)")) return;
  
  const preservedBurn = currentTargetBurn;
  try {
    const res = await fetch(`${API_BASE}/api/skip-exercise/${userId}`, { 
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, preserve_target_burn: preservedBurn })
    });
    if (res.ok) {
      await loadExerciseRecommendation(true);
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Error executing skip exercise:", err);
    await loadExerciseRecommendation(true);
  }
}

async function submitExerciseWorkout(exerciseName, durationMins, caloriesBurned) {
  const userId = getCleanUserId();
  if (!userId) return;
  const payload = {
    user_id: userId,
    exercise_name: exerciseName,
    duration_mins: parseInt(durationMins, 10),
    calories_burned: parseInt(caloriesBurned, 10)
  };
  const res = await fetch(`${API_BASE}/api/complete-exercise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    await refreshStabilityScore();
    alert(`Workout logged! Burned ${caloriesBurned} kcal.`);
  }
}

// ==========================================
// PILLAR 3: SLEEP ARCHITECTURE
// ==========================================
function calculateSleepHours(bedTimeStr, wakeTimeStr) {
  if (!bedTimeStr || !wakeTimeStr) return 8.0;
  try {
    const [bH, bM] = bedTimeStr.split(":").map(Number);
    const [wH, wM] = wakeTimeStr.split(":").map(Number);
    let diffMins = (wH * 60 + wM) - (bH * 60 + bM);
    if (diffMins <= 0) diffMins += 24 * 60; // crossed midnight
    return Math.round((diffMins / 60) * 10) / 10;
  } catch (e) {
    return 8.0;
  }
}

async function loadSleepRecommendation() {
  const userId = getCleanUserId();
  if (!userId) return;
  try {
    const res = await fetch(`${API_BASE}/api/sleep-recommendation/${userId}`);
    if (res.ok) {
      const data = await res.json();
      const targetVal = document.getElementById("sleepTargetVal");
      const lastVal = document.getElementById("sleepLastVal");
      const debtVal = document.getElementById("sleepDebtVal");
      const bedtime = document.getElementById("sleepBedtime");
      const waketime = document.getElementById("sleepWaketime");
      const advice = document.getElementById("sleepCircadianAdvice");

      if (targetVal) targetVal.innerText = `${data.target_hours || 8.0} hrs`;
      if (lastVal) lastVal.innerText = data.last_logged_sleep ? `${data.last_logged_sleep} hrs` : "-- hrs";
      if (debtVal) debtVal.innerText = data.sleep_debt > 0 ? `+${data.sleep_debt} hrs` : "0 hrs";
      if (bedtime) bedtime.innerText = data.ideal_bedtime || "10:30 PM";
      if (waketime) waketime.innerText = data.ideal_waketime || "06:30 AM";
      if (advice && data.circadian_advice) advice.innerText = data.circadian_advice;
    }
  } catch (err) {
    console.error("Sleep fetch error:", err);
  }
}

async function submitSleepWindow(event) {
  event.preventDefault();
  const userId = getCleanUserId();
  if (!userId) return;

  const bed = document.getElementById("sleepInputBed")?.value || "22:30";
  const wake = document.getElementById("sleepInputWake")?.value || "06:30";
  const quality = document.getElementById("sleepInputQuality")?.value || "Restful";
  const calculatedHours = calculateSleepHours(bed, wake);

  try {
    const res = await fetch(`${API_BASE}/api/log-sleep-schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        sleep_hours: calculatedHours,
        bed_time: bed,
        wake_time: wake,
        sleep_quality: quality
      })
    });
    if (res.ok) {
      alert(`Sleep schedule synced (${calculatedHours} hrs)!`);
      await loadSleepRecommendation();
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Sleep submit error:", err);
  }
}

async function resetSleepLog() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (confirm("Reset today's sleep telemetry log?")) {
    try {
      const res = await fetch(`${API_BASE}/api/reset-sleep/${userId}`, { method: "POST" });
      if (res.ok) {
        await loadSleepRecommendation();
        await refreshStabilityScore();
        alert("Sleep log reset for today.");
      }
    } catch (err) {
      console.error("Sleep reset error:", err);
    }
  }
}

// ==========================================
// PILLAR 4: MEDICATION & SUPPLEMENTS
// ==========================================
async function loadUserMedications() {
  const userId = getCleanUserId();
  if (!userId) return;
  try {
    const res = await fetch(`${API_BASE}/api/user-medications/${userId}`);
    if (res.ok) {
      userMedicationsList = await res.json();
    } else {
      userMedicationsList = [];
    }
    renderMedicationsList();
  } catch (err) {
    console.error("Error loading medications:", err);
    userMedicationsList = [];
    renderMedicationsList();
  }
}

function renderMedicationsList() {
  const container = document.getElementById("medicationListContainer");
  const adherenceEl = document.getElementById("medAdherenceRate");
  if (!container) return;

  if (!userMedicationsList || userMedicationsList.length === 0) {
    container.innerHTML = `
      <div class="p-6 text-center border border-dashed border-slate-800 rounded-xl bg-[#0B0F19]">
        <p class="text-xs text-slate-400 font-medium">No active medications or supplements logged.</p>
        <p class="text-[11px] text-slate-500 mt-1">Scan a prescription photo or add your first item using the form.</p>
      </div>`;
    if (adherenceEl) adherenceEl.innerText = "0% Protocol Compliance";
    return;
  }

  let takenCount = 0;
  container.innerHTML = userMedicationsList.map(m => {
    if (m.is_taken_today) takenCount++;
    return `
      <div class="flex items-center justify-between p-3.5 bg-[#0B0F19] rounded-xl border border-slate-800 hover:border-slate-700 transition">
        <div class="flex items-start gap-3 min-w-0 flex-1 pr-3">
          <span class="text-xl p-2 bg-[#111625] rounded-xl border border-slate-800 shrink-0">${m.icon || '💊'}</span>
          <div class="min-w-0">
            <h4 class="text-xs font-bold text-white leading-tight truncate">${m.name}</h4>
            <p class="text-[11px] text-slate-400 mt-0.5 leading-snug">
              ${m.dosage_frequency} <span class="text-slate-600">|</span> <span class="text-slate-500">${m.clinical_purpose || 'General'}</span>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          ${m.is_taken_today ? 
            `<button onclick="toggleDose(${m.id})" class="px-3 py-1.5 bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-xs font-semibold rounded-lg flex items-center gap-1 hover:bg-emerald-900/60 transition shadow-sm">
              ✓ Taken
            </button>` : 
            `<button onclick="toggleDose(${m.id})" class="px-3 py-1.5 bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white border border-slate-700 hover:border-indigo-500 text-xs font-semibold rounded-lg transition shadow-sm">
              Take Dose
            </button>`
          }
          <button onclick="removeMedication(${m.id}, '${m.name.replace(/'/g, "\\'")}')" class="px-2.5 py-1.5 bg-rose-950/40 hover:bg-rose-900 text-rose-400 border border-rose-600/30 hover:border-rose-500 text-xs font-medium rounded-lg transition shadow-sm">
            Remove
          </button>
        </div>
      </div>`;
  }).join("");

  const adherence = Math.round((takenCount / userMedicationsList.length) * 100);
  if (adherenceEl) adherenceEl.innerText = `${adherence}% Protocol Compliance`;
}

async function removeMedication(medId, medName) {
  const cleanMedId = parseInt(medId, 10);
  if (confirm(`Remove "${medName}" from your active daily protocol?`)) {
    try {
      const res = await fetch(`${API_BASE}/api/delete-medication/${cleanMedId}`, { method: "DELETE" });
      if (res.ok) {
        userMedicationsList = userMedicationsList.filter(m => m.id !== cleanMedId);
        renderMedicationsList();
        await refreshStabilityScore();
      }
    } catch (err) {
      console.error("Error removing medication:", err);
    }
  }
}

async function toggleDose(medId) {
  try {
    const res = await fetch(`${API_BASE}/api/toggle-medication-dose/${medId}`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      const med = userMedicationsList.find(m => m.id === medId);
      if (med) med.is_taken_today = data.is_taken_today;
      renderMedicationsList();
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Error toggling dose:", err);
  }
}

async function resetMedicationsDay() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (confirm("Start a new day and reset all daily doses to pending?")) {
    try {
      const res = await fetch(`${API_BASE}/api/reset-medications-day/${userId}`, { method: "POST" });
      if (res.ok) {
        userMedicationsList.forEach(m => m.is_taken_today = false);
        renderMedicationsList();
        await refreshStabilityScore();
      }
    } catch (err) {
      console.error(err);
    }
  }
}

async function handleRxUpload(files) {
  if (!files || !files[0]) return;
  const file = files[0];
  const nameInput = document.getElementById("inputMedName");
  const dosageInput = document.getElementById("inputMedDosage");

  if (nameInput) nameInput.value = "AI Neural OCR scanning prescription...";
  if (dosageInput) dosageInput.value = "Recognizing handwritten/printed text...";

  try {
    const ocrResult = await Tesseract.recognize(file, 'eng', {
      logger: m => {
        if (m.status === 'recognizing text' && dosageInput) {
          dosageInput.value = `AI Reading text: ${Math.round(m.progress * 100)}%`;
        }
      }
    });
    const recognizedText = ocrResult.data.text || "";
    const res = await fetch(`${API_BASE}/api/scan-prescription`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, extracted_text: recognizedText })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.not_found || !data.name) {
        if (nameInput) nameInput.value = "";
        if (dosageInput) dosageInput.value = "";
        alert(`⚠ No PMOS medication matched from this image.`);
      } else {
        if (nameInput) nameInput.value = data.name;
        if (dosageInput) dosageInput.value = data.dosage;
        alert(`🧠 AI Vision Scanner Extracted:\n\nPrescribed: ${data.name}\nSchedule: ${data.dosage}`);
      }
    }
  } catch (err) {
    console.error("AI OCR Error:", err);
    if (nameInput) nameInput.value = "";
    if (dosageInput) dosageInput.value = "";
    alert("Error executing neural OCR.");
  } finally {
    const fileInput = document.getElementById("rxFileInput");
    if (fileInput) fileInput.value = "";
  }
}

async function handleMedSearch(query) {
  const box = document.getElementById("medSuggestionsBox");
  if (!box) return;
  if (!query || query.trim().length === 0) {
    box.classList.add("hidden");
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/medication-suggestions?query=${encodeURIComponent(query)}`);
    if (res.ok) {
      const suggestions = await res.json();
      if (suggestions.length === 0) {
        box.classList.add("hidden");
        return;
      }
      box.innerHTML = suggestions.map(s => `
        <div onclick="selectSuggestion('${s.name.replace(/'/g, "\\'")}', '${s.default_dosage.replace(/'/g, "\\'")}')" class="p-2.5 hover:bg-indigo-600/30 cursor-pointer border-b border-slate-800 last:border-none text-left transition">
          <div class="flex items-center gap-2">
            <span>${s.icon}</span>
            <p class="text-xs font-bold text-white">${s.name}</p>
          </div>
          <p class="text-[10px] text-slate-400 pl-6">${s.default_dosage} — ${s.purpose}</p>
        </div>
      `).join("");
      box.classList.remove("hidden");
    }
  } catch (err) {
    console.error(err);
  }
}

function selectSuggestion(name, dosage) {
  const nameInput = document.getElementById("inputMedName");
  const dosageInput = document.getElementById("inputMedDosage");
  const box = document.getElementById("medSuggestionsBox");
  if (nameInput) nameInput.value = name;
  if (dosageInput) dosageInput.value = dosage;
  if (box) box.classList.add("hidden");
}

async function submitNewMedication(event) {
  event.preventDefault();
  const userId = getCleanUserId();
  if (!userId) return;

  const nameInput = document.getElementById("inputMedName");
  const dosageInput = document.getElementById("inputMedDosage");
  const timingSelect = document.getElementById("selectMedTiming");

  const name = nameInput ? nameInput.value.trim() : "";
  const dosage = dosageInput ? dosageInput.value.trim() : "";
  const timing = timingSelect ? timingSelect.value : "Morning";

  if (!name) return;

  const duplicate = userMedicationsList.some(m => m.name.toLowerCase() === name.toLowerCase());
  if (duplicate) {
    alert(`⚠️ "${name}" is already active in your protocol!`);
    return;
  }

  const fullDosageStr = dosage.includes("|") ? dosage : `${dosage} | ${timing}`;
  try {
    const res = await fetch(`${API_BASE}/api/add-medication`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, med_name: name, dosage_frequency: fullDosageStr })
    });
    if (res.ok) {
      if (nameInput) nameInput.value = "";
      if (dosageInput) dosageInput.value = "";
      await loadUserMedications();
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Error adding medication:", err);
  }
}

// ==========================================
// PILLAR 5: STRESS & VAGUS ENGINE
// ==========================================
function toggleSymptomTag(btn, tag) {
  const idx = selectedSymptoms.indexOf(tag);
  if (idx > -1) {
    selectedSymptoms.splice(idx, 1);
    btn.classList.remove("border-indigo-500", "bg-indigo-950/60", "text-indigo-300");
    btn.classList.add("border-slate-800", "bg-[#0B0F19]", "text-slate-400");
  } else {
    selectedSymptoms.push(tag);
    btn.classList.remove("border-slate-800", "bg-[#0B0F19]", "text-slate-400");
    btn.classList.add("border-indigo-500", "bg-indigo-950/60", "text-indigo-300");
  }
}

async function logSelectedSymptoms() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (selectedSymptoms.length === 0) {
    alert("Please select at least one symptom tag before logging.");
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/log-stress-reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        technique: "Symptom Logging",
        duration_mins: 2,
        symptoms: selectedSymptoms
      })
    });
    if (res.ok) {
      alert("Symptoms logged successfully!");
      document.querySelectorAll(".symptom-tag").forEach(btn => {
        btn.classList.remove("border-indigo-500", "bg-indigo-950/60", "text-indigo-300");
        btn.classList.add("border-slate-800", "bg-[#0B0F19]", "text-slate-400");
      });
      selectedSymptoms = [];
      await refreshStabilityScore();
    }
  } catch (err) {
    console.error("Error logging symptoms:", err);
  }
}

async function resetStressDay() {
  const userId = getCleanUserId();
  if (!userId) return;
  if (confirm("Reset all stress and symptom logs for today?")) {
    try {
      const res = await fetch(`${API_BASE}/api/reset-stress-day/${userId}`, { method: "POST" });
      if (res.ok) {
        alert("Stress and symptom logs reset successfully.");
        await refreshStabilityScore();
      }
    } catch (err) {
      console.error("Error resetting stress day:", err);
    }
  }
}

function switchBreathingTechnique(tech) {
  stopBreathingExercise();
  currentBreathingTechnique = tech;
  const note = document.getElementById("techniqueClinicalNote");
  if (!note) return;
  if (tech === "box") {
    note.innerText = "Box Breathing (4s Inhale, 4s Hold, 4s Exhale, 4s Hold) stabilizes autonomic reactivity and improves heart rate variability (HRV).";
  } else if (tech === "sigh") {
    note.innerText = "The Physiological Sigh (two quick inhales through the nose followed by a long mouth exhale) reinflates alveoli and triggers rapid parasympathetic calm.";
  } else {
    note.innerText = "4-7-8 breathing maximizes blood oxygen saturation while long exhalations trigger acetylcholine release via the vagus nerve to reduce adrenal strain.";
  }
}

function startBreathingExercise() {
  stopBreathingExercise();
  const circle = document.getElementById("breathingCircle");
  const action = document.getElementById("breathingAction");
  const timer = document.getElementById("breathingTimer");
  const startBtn = document.getElementById("breathingStartBtn");
  if (startBtn) startBtn.disabled = true;

  if (currentBreathingTechnique === "box") {
    runBoxBreathing(circle, action, timer);
  } else if (currentBreathingTechnique === "sigh") {
    runPhysiologicalSigh(circle, action, timer);
  } else {
    run478Breathing(circle, action, timer);
  }
}

function run478Breathing(circle, action, timer) {
  let stage = 0;
  let count = 4;
  if (action) action.innerText = "Inhale (Nose)";
  if (timer) timer.innerText = `${count}s`;
  if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-emerald-500 bg-emerald-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_35px_rgba(16,185,129,0.5)]";

  breathingInterval = setInterval(() => {
    count--;
    if (count <= 0) {
      stage = (stage + 1) % 3;
      if (stage === 0) {
        count = 4;
        if (action) action.innerText = "Inhale (Nose)";
        if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-emerald-500 bg-emerald-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_35px_rgba(16,185,129,0.5)]";
      } else if (stage === 1) {
        count = 7;
        if (action) action.innerText = "Hold";
        if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-amber-500 bg-amber-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_35px_rgba(245,158,11,0.5)]";
      } else if (stage === 2) {
        count = 8;
        if (action) action.innerText = "Exhale (Mouth)";
        if (circle) circle.className = "w-36 h-36 rounded-full border-4 border-indigo-500 bg-indigo-500/10 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_20px_rgba(99,102,241,0.3)]";
      }
    }
    if (timer) timer.innerText = `${count}s`;
  }, 1000);
}

function runBoxBreathing(circle, action, timer) {
  let stage = 0;
  let count = 4;
  if (action) action.innerText = "Inhale";
  if (timer) timer.innerText = `${count}s`;
  if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-cyan-500 bg-cyan-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_30px_rgba(6,182,212,0.4)]";

  breathingInterval = setInterval(() => {
    count--;
    if (count <= 0) {
      stage = (stage + 1) % 4;
      count = 4;
      if (stage === 0) {
        if (action) action.innerText = "Inhale";
        if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-cyan-500 bg-cyan-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_30px_rgba(6,182,212,0.4)]";
      } else if (stage === 1) {
        if (action) action.innerText = "Hold";
        if (circle) circle.className = "w-48 h-48 rounded-full border-4 border-amber-500 bg-amber-500/20 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_30px_rgba(245,158,11,0.4)]";
      } else if (stage === 2) {
        if (action) action.innerText = "Exhale";
        if (circle) circle.className = "w-36 h-36 rounded-full border-4 border-indigo-500 bg-indigo-500/10 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_20px_rgba(99,102,241,0.3)]";
      } else {
        if (action) action.innerText = "Hold Empty";
        if (circle) circle.className = "w-36 h-36 rounded-full border-4 border-slate-600 bg-slate-800/20 flex flex-col items-center justify-center transition-all duration-1000";
      }
    }
    if (timer) timer.innerText = `${count}s`;
  }, 1000);
}

function runPhysiologicalSigh(circle, action, timer) {
  let stage = 0;
  let count = 3;
  if (action) action.innerText = "Deep Inhale";
  if (timer) timer.innerText = `${count}s`;
  if (circle) circle.className = "w-44 h-44 rounded-full border-4 border-emerald-500 bg-emerald-500/20 flex flex-col items-center justify-center transition-all duration-700";

  breathingInterval = setInterval(() => {
    count--;
    if (count <= 0) {
      stage = (stage + 1) % 3;
      if (stage === 0) {
        count = 3;
        if (action) action.innerText = "Deep Inhale";
        if (circle) circle.className = "w-44 h-44 rounded-full border-4 border-emerald-500 bg-emerald-500/20 flex flex-col items-center justify-center transition-all duration-700";
      } else if (stage === 1) {
        count = 1;
        if (action) action.innerText = "+ Sniff Inhale";
        if (circle) circle.className = "w-52 h-52 rounded-full border-4 border-teal-400 bg-teal-400/30 flex flex-col items-center justify-center transition-all duration-300";
      } else {
        count = 6;
        if (action) action.innerText = "Long Exhale";
        if (circle) circle.className = "w-36 h-36 rounded-full border-4 border-indigo-500 bg-indigo-500/10 flex flex-col items-center justify-center transition-all duration-1000";
      }
    }
    if (timer) timer.innerText = `${count}s`;
  }, 1000);
}

function stopBreathingExercise() {
  if (breathingInterval) clearInterval(breathingInterval);
  const circle = document.getElementById("breathingCircle");
  const action = document.getElementById("breathingAction");
  const timer = document.getElementById("breathingTimer");
  const startBtn = document.getElementById("breathingStartBtn");

  if (startBtn) startBtn.disabled = false;
  if (action) action.innerText = "Ready";
  if (timer) timer.innerText = "4s";
  if (circle) circle.className = "w-40 h-40 rounded-full border-4 border-indigo-500 bg-indigo-500/10 flex flex-col items-center justify-center transition-all duration-1000 shadow-[0_0_25px_rgba(99,102,241,0.25)]";
}

async function completeStressSession() {
  stopBreathingExercise();
  const userId = getCleanUserId();
  if (!userId) return;

  const btn = document.getElementById("btnSyncStressSession");
  if (btn) {
    btn.innerText = "Syncing with Digital Twin...";
    btn.disabled = true;
  }
  try {
    const res = await fetch(`${API_BASE}/api/log-stress-reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        technique: currentBreathingTechnique,
        duration_mins: 2,
        symptoms: selectedSymptoms
      })
    });
    if (res.ok) {
      const data = await res.json();
      await refreshStabilityScore();
      alert(`🌿 Session Logged!\n\n${data.message}`);
      if (btn) {
        btn.innerHTML = "<span>✓</span> Session Completed Today (+5 pts)";
        btn.className = "w-full py-2.5 bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-bold text-xs rounded-xl cursor-not-allowed";
      }
    }
  } catch (err) {
    console.error("Stress session log error:", err);
    if (btn) {
      btn.innerHTML = "<span>✓</span> Complete & Boost Stability Index (+5 pts)";
      btn.disabled = false;
    }
  }
}

// ==========================================
// ANTHROPOMETRY / BMI SYNC
// ==========================================
async function submitBmiUpdate(event) {
  event.preventDefault();
  const userId = getCleanUserId();
  if (!userId) return;

  const height = parseFloat(document.getElementById("inputHeight")?.value || 162);
  const weight = parseFloat(document.getElementById("inputWeight")?.value || 58);
  const saveBtn = document.getElementById("saveBmiBtn");
  if (saveBtn) saveBtn.innerText = "Syncing...";

  try {
    const res = await fetch(`${API_BASE}/api/update-bmi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, height_cm: height, weight_kg: weight })
    });
    if (res.ok) {
      const data = await res.json();
      const sideScore = document.getElementById("sideBmiScore");
      const sideCat = document.getElementById("sideBmiCategory");
      const modalScore = document.getElementById("modalBmiScore");
      const modalCat = document.getElementById("modalBmiCategory");

      if (sideScore) sideScore.innerText = `${data.bmi}`;
      if (sideCat) sideCat.innerText = data.bmi_category.split(' ')[0];
      if (modalScore) modalScore.innerText = `${data.bmi}`;
      if (modalCat) modalCat.innerText = `${data.bmi_category}`;

      await loadExerciseRecommendation();
      await refreshStabilityScore();
      closeBmiModal();
    }
  } catch (err) {
    console.error("BMI update error:", err);
  } finally {
    if (saveBtn) saveBtn.innerText = "Sync BMI";
  }
}

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", async function() {
  refreshUserDisplay();
  await fetchUserProfile();
  await refreshStabilityScore();

  switchPillarTab('diet');

  const dropZone = document.getElementById('dropZone');
  if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });
    dropZone.addEventListener('drop', e => {
      handleFileSelect(e.dataTransfer.files);
    }, false);
  }
});
