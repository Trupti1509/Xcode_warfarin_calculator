const API_URL = "/api/calculate";

const form = document.getElementById("calculatorForm");
const fileInput = document.getElementById("geneticFile");
const selectedFile = document.getElementById("selectedFile");
const clearFile = document.getElementById("clearFile");
const formError = document.getElementById("formError");
const resultCard = document.getElementById("resultCard");
const calculateButton = document.getElementById("calculateButton");

const uploadTab = document.getElementById("uploadTab");
const manualTab = document.getElementById("manualTab");
const uploadPanel = document.getElementById("uploadPanel");
const manualPanel = document.getElementById("manualPanel");

const population = document.getElementById("population");
const africanContextWrap = document.getElementById("africanContextWrap");
const targetInr = document.getElementById("targetInr");

let pgxMode = "upload";


/* =========================================================
   PGx INPUT MODE
   ========================================================= */

function setPgxMode(mode) {
  pgxMode = mode;
  const manual = mode === "manual";

  uploadTab.classList.toggle("active", !manual);
  manualTab.classList.toggle("active", manual);

  uploadPanel.classList.toggle("hidden", manual);
  manualPanel.classList.toggle("hidden", !manual);

  uploadTab.setAttribute("aria-selected", String(!manual));
  manualTab.setAttribute("aria-selected", String(manual));
}

uploadTab.addEventListener("click", () => {
  setPgxMode("upload");
});

manualTab.addEventListener("click", () => {
  setPgxMode("manual");
});


/* =========================================================
   AFRICAN-ANCESTRY CONTEXT
   ========================================================= */

function updateAfricanContext() {
  const isAfrican = population.value === "black_african_american";

  if (africanContextWrap) {
    africanContextWrap.classList.toggle("hidden", !isAfrican);
  }

  if (!isAfrican) {
    const africanContext = document.getElementById("africanContext");
    if (africanContext) {
      africanContext.value = "unknown";
    }
  }
}

population.addEventListener("change", updateAfricanContext);
updateAfricanContext();


/* =========================================================
   FILE UPLOAD
   ========================================================= */

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (file) {
    selectedFile.textContent = file.name;
    selectedFile.classList.remove("hidden");
    clearFile.classList.remove("hidden");
  } else {
    clearSelectedFile();
  }
});

clearFile.addEventListener("click", () => {
  fileInput.value = "";
  clearSelectedFile();
});

function clearSelectedFile() {
  selectedFile.textContent = "";
  selectedFile.classList.add("hidden");
  clearFile.classList.add("hidden");
}


/* =========================================================
   INFO BUTTONS
   ========================================================= */

document.querySelectorAll(".info-button").forEach(button => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.target);
    if (target) {
      target.classList.toggle("hidden");
    }
  });
});


/* =========================================================
   CALCULATOR SUBMISSION
   ========================================================= */

form.addEventListener("submit", async event => {
  event.preventDefault();

  formError.classList.add("hidden");
  resultCard.classList.add("hidden");

  if (!form.reportValidity()) {
    return;
  }

  // Target INR validation
  if (targetInr && targetInr.value === "other") {
    formError.textContent =
      "This calculator is not validated for the selected INR target. Use an indication-specific clinical dosing protocol.";
    formError.classList.remove("hidden");
    formError.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  calculateButton.disabled = true;
  calculateButton.textContent = "Calculating…";

  const data = new FormData();
  data.append("age", document.getElementById("age").value);
  data.append("height_cm", document.getElementById("height").value);
  data.append("weight_kg", document.getElementById("weight").value);
  data.append("population", population.value);
  data.append("target_inr", targetInr ? targetInr.value : "2.0-3.0");
  data.append("african_context", document.getElementById("africanContext")?.value || "unknown");
  data.append("amiodarone", document.getElementById("amiodarone").checked ? "true" : "false");
  data.append("enzyme_inducer", document.getElementById("inducer").checked ? "true" : "false");

  if (pgxMode === "upload") {
    const file = fileInput.files?.[0];
    if (file) {
      data.append("genetic_file", file);
    }
  } else {
    data.append("manual_pgx", "true");
    data.append("cyp2c9_allele1", document.getElementById("cyp2c9Allele1").value);
    data.append("cyp2c9_allele2", document.getElementById("cyp2c9Allele2").value);
    data.append("expanded_tested", document.getElementById("expandedTested").checked ? "true" : "false");
    data.append("vkorc1", document.getElementById("manualVkorc1").value);
    data.append("cyp4f2", document.getElementById("manualCyp4f2").value);
    data.append("rs12777823", document.getElementById("manualRs127").value);
  }

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: data
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "The calculation could not be completed.");
    }

    renderResult(payload);
  } catch (error) {
    formError.textContent = error.message;
    formError.classList.remove("hidden");
    formError.scrollIntoView({ behavior: "smooth", block: "center" });
  } finally {
    calculateButton.disabled = false;
    calculateButton.textContent = "Calculate maintenance dose";
  }
});


/* =========================================================
   RESULT RENDERING
   ========================================================= */

function renderResult(result) {
  // Point estimates only
  document.getElementById("weeklyDose").textContent = result.weekly_mg.toFixed(1);
  document.getElementById("dailyDose").textContent = result.daily_average_mg.toFixed(1);

  // Calculation method & reason
  document.getElementById("methodBadge").textContent = result.method_label;
  document.getElementById("pathwayReason").textContent = result.pathway_reason;

  // Genetic summary
  const geneticSummary = document.getElementById("geneticSummary");
  const g = result.genetic_summary || {};

  if (Object.keys(g).length && (g.cyp2c9_diplotype !== "Unavailable" || g.vkorc1 !== "Unavailable")) {
    const cyp2c9Cell = document.getElementById("summaryCYP2C9");
    if (g.additional_cyp2c9_finding) {
      cyp2c9Cell.innerHTML = `
        <div class="genotype-subline"><strong>Reported result:</strong> ${g.cyp2c9_reported || g.cyp2c9_diplotype}</div>
        <div class="genotype-subline"><strong>Original IWPC input:</strong> ${g.iwpc_cyp2c9_input_text}</div>
        <div class="genotype-subline cpic-finding"><strong>Additional CPIC finding:</strong> ${g.additional_cyp2c9_finding}</div>
      `;
    } else {
      const iwpcText = g.iwpc_cyp2c9_input_text || g.iwpc_cyp2c9_base;
      cyp2c9Cell.innerHTML = `
        <div class="genotype-subline"><strong>Reported result:</strong> ${g.cyp2c9_reported || g.cyp2c9_diplotype}</div>
        <div class="genotype-subline"><strong>Original IWPC input:</strong> ${iwpcText}</div>
      `;
    }

    document.getElementById("summaryVKORC1").textContent = g.vkorc1 || "Unavailable";
    document.getElementById("summaryCYP4F2").textContent = g.cyp4f2_diplotype || "Unavailable";

    const rs127Row = document.getElementById("summaryRs127Row");
    if (g.rs12777823) {
      document.getElementById("summaryRs127").textContent = g.rs12777823;
      rs127Row?.classList.remove("hidden");
    } else {
      rs127Row?.classList.add("hidden");
    }

    geneticSummary.classList.remove("hidden");
  } else {
    geneticSummary.classList.add("hidden");
  }

  // CPIC Considerations (displayed separately)
  const notesSection = document.getElementById("pgxNotes");
  const notesList = document.getElementById("pgxNotesList");
  notesList.innerHTML = "";

  if (result.pgx_notes?.length) {
    result.pgx_notes.forEach(note => {
      const item = document.createElement("div");
      item.className = "note-item";

      const headerDiv = document.createElement("div");
      headerDiv.className = "note-header-row";

      const title = document.createElement("strong");
      title.textContent = note.title;
      headerDiv.appendChild(title);

      if (note.strength) {
        const strength = document.createElement("span");
        const strengthClass = note.strength.toLowerCase().replace(/[^a-z0-9]/g, "-");
        strength.className = `note-strength ${strengthClass}`;
        if (note.strength.toLowerCase().includes("informational")) {
          strength.textContent = `Status: ${note.strength}`;
        } else {
          strength.textContent = `CPIC recommendation: ${note.strength}`;
        }
        headerDiv.appendChild(strength);
      }

      item.appendChild(headerDiv);

      const text = document.createElement("p");
      text.className = "note-text";
      text.textContent = note.text;
      item.appendChild(text);

      if (note.range?.length === 2) {
        const range = document.createElement("p");
        range.className = "note-range";
        range.textContent = `If this adjustment is applied to the IWPC estimate: ${note.range[0].toFixed(1)}–${note.range[1].toFixed(1)} mg/week`;
        item.appendChild(range);
      }

      notesList.appendChild(item);
    });

    notesSection.classList.remove("hidden");
  } else {
    notesSection.classList.add("hidden");
  }

  // FDA Label Reference Card (if present in DOM)
  const fdaCard = document.getElementById("fdaReferenceCard");
  const fdaCallout = document.getElementById("fdaSpecificCallout");
  if (fdaCard && fdaCallout) {
    if (result.fda_label_reference) {
      fdaCallout.textContent = result.fda_label_reference;
      fdaCallout.classList.remove("hidden");
      fdaCard.classList.remove("hidden");
    } else {
      fdaCallout.textContent = "";
      fdaCallout.classList.add("hidden");
      fdaCard.classList.add("hidden");
    }
  }

  // Clinical warnings
  const warningsCard = document.getElementById("warningsCard");
  const warnings = document.getElementById("warnings");
  if (result.warnings?.length) {
    warnings.textContent = result.warnings.join(" ");
    warningsCard.classList.remove("hidden");
  } else {
    warningsCard.classList.add("hidden");
  }

  // Reveal result
  resultCard.classList.remove("hidden");
  resultCard.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "start"
  });
}