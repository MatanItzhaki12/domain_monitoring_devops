document.addEventListener("DOMContentLoaded", function () {
  // =======================
  // Utility Helpers
  // =======================
  function showStatus(el, message, type = "loading") {
    if (!el) return;
    el.textContent = message;
    el.className = ""; // Reset classes
    el.classList.add("modal-status", `status-${type}`);
  }

  async function finalizeModal(el, message, type = "success", modal, reload = true) {
    showStatus(el, message, type);
    if (type === "success" && modal) {
      setTimeout(() => {
        closeModal(modal);
        if (reload) location.reload();
      }, 1200);
    }
  }

  function openModal(modal) {
    if (modal) modal.style.display = "flex";
  }

  function closeModal(modal) {
    if (modal) modal.style.display = "none";
  }

  // =======================
  // Global Elements
  // =======================
  const addDomainModal = document.getElementById("addDomainModal");
  const openAddDomainBtn = document.getElementById("openAddDomain");
  const addDomainForm = document.getElementById("addDomainForm");
  const addDomainStatus = document.getElementById("addDomainStatus");

  const bulkUploadModal = document.getElementById("bulkUploadModal");
  const openBulkUploadBtn = document.getElementById("openBulkUpload");
  const bulkUploadForm = document.getElementById("bulkUploadForm");
  const bulkUploadStatus = document.getElementById("bulkUploadStatus");

  const deleteDomainModal = document.getElementById("deleteDomainModal");
  const deleteDomainText = document.getElementById("deleteDomainText");
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");

  const logoutBtn = document.getElementById("logoutBtn");
  const scanNowBtn = document.getElementById("scanNowBtn");
  const bulkActions = document.querySelector(".bulk-actions");
  const selectAllCheckbox = document.getElementById("selectAll");

  let domainsToDelete = [];

  // =======================
  // Add Domain
  // =======================
  openAddDomainBtn?.addEventListener("click", () => {
    openModal(addDomainModal);
    addDomainForm.reset();
    addDomainStatus.textContent = "";
  });

  addDomainForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const domain = document.getElementById("domainInput").value.trim();
    const submitBtn = addDomainForm.querySelector('button[type="submit"]');

    submitBtn.style.display = "none";
    showStatus(addDomainStatus, "Adding domain... please wait", "loading");
    await new Promise(requestAnimationFrame);

    try {
      const res = await fetch("/add_domain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      });
      const result = await res.json();

      if (result.ok) {
        sessionStorage.removeItem("scanClicked"); 
        await finalizeModal(addDomainStatus, "Domain added successfully!", "success", addDomainModal);
      } else {
        showStatus(addDomainStatus, result.error || "Failed to add domain.", "error");
        submitBtn.style.display = "block";
      }
    } catch {
      showStatus(addDomainStatus, "Request failed. Try again.", "error");
      submitBtn.style.display = "block";
    }
  });

  // =======================
  // Bulk Upload
  // =======================
  openBulkUploadBtn?.addEventListener("click", () => {
    openModal(bulkUploadModal);
    bulkUploadForm.reset();
    bulkUploadStatus.textContent = "";
  });

  bulkUploadForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(bulkUploadForm);
    const submitBtn = bulkUploadForm.querySelector('button[type="submit"]');

    submitBtn.style.display = "none";
    showStatus(bulkUploadStatus, "Uploading domains... please wait", "loading");
    await new Promise(requestAnimationFrame);

    try {
      const res = await fetch("/bulk_domains", { method: "POST", body: formData });
      const result = await res.json();

      if (result.ok) {
        sessionStorage.removeItem("scanClicked"); 
        await finalizeModal(bulkUploadStatus, "Bulk upload completed!", "success", bulkUploadModal); 
      } else {
        showStatus(bulkUploadStatus, result.error || "Upload failed.", "error");
        submitBtn.style.display = "block";
      }
    } catch {
      showStatus(bulkUploadStatus, "Upload failed. Try again.", "error");
      submitBtn.style.display = "block";
    }
  });

  // =======================
  // Delete Logic
  // =======================
  function openDeleteModal(domains, message) {
    domainsToDelete = domains;
    deleteDomainText.textContent = message;
    confirmDeleteBtn.style.display = "block";
    openModal(deleteDomainModal);
  }

  function attachDeleteHandlers() {
    document.querySelectorAll(".delete-domain-btn").forEach((btn) => {
      btn.onclick = () => {
        const domain = btn.getAttribute("data-domain");
        openDeleteModal([domain], `Delete '${domain}'?`);
      };
    });
  }
  attachDeleteHandlers();

  document.getElementById("bulkDeleteBtn")?.addEventListener("click", () => {
    const checked = Array.from(document.querySelectorAll(".select-domain:checked"));
    if (!checked.length) return alert("No domains selected!");
    const domains = checked.map((cb) => cb.value);
    openDeleteModal(domains, `Delete ${domains.length} domain(s)?`);
  });

  document.getElementById("deleteAllBtn")?.addEventListener("click", () => {
    const all = Array.from(document.querySelectorAll(".select-domain")).map((cb) => cb.value);
    if (!all.length) return alert("No domains available!");
    openDeleteModal(all, `Delete ALL ${all.length} domains?`);
  });

  cancelDeleteBtn?.addEventListener("click", () => {
    closeModal(deleteDomainModal);
    domainsToDelete = [];
  });

  confirmDeleteBtn?.addEventListener("click", async () => {
    if (!domainsToDelete.length) return;

    confirmDeleteBtn.style.display = "none";
    showStatus(deleteDomainText, "Removing domains... please wait", "loading");
    await new Promise(requestAnimationFrame);

    try {
      const response = await fetch("/remove_domains", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domains: domainsToDelete }),
      });
      const result = await response.json();

      if (result.ok) {
        await finalizeModal(deleteDomainText, "Domains removed successfully!", "success", deleteDomainModal);
      } else {
        showStatus(deleteDomainText, result.error || "Failed to delete.", "error");
        confirmDeleteBtn.style.display = "block";
      }
    } catch {
      showStatus(deleteDomainText, "Request failed. Try again.", "error");
      confirmDeleteBtn.style.display = "block";
    }
    domainsToDelete = [];
  });

  // =======================
  // Bulk Actions Visibility
  // =======================
  function toggleBulkActions() {
    const anyChecked = document.querySelectorAll(".select-domain:checked").length > 0;
    bulkActions.style.display = anyChecked ? "flex" : "none";
  }

  function attachCheckboxHandlers() {
    document.querySelectorAll(".select-domain").forEach((cb) => {
      cb.onchange = toggleBulkActions;
    });

    selectAllCheckbox?.addEventListener("change", () => {
      const allChecks = document.querySelectorAll(".select-domain");
      allChecks.forEach((cb) => (cb.checked = selectAllCheckbox.checked));
      toggleBulkActions();
    });
  }

  attachCheckboxHandlers();
  toggleBulkActions(); // initialize hidden

  // =======================
  // Scan Now
  // =======================
  scanNowBtn?.addEventListener("click", async () => {
    scanNowBtn.disabled = true;
    scanNowBtn.textContent = "Scanning...";
    try {
      await fetch("/scan_domains");
      location.reload();
    } catch {
      alert("Scan failed.");
      scanNowBtn.textContent = "Scan Now";
      scanNowBtn.disabled = false;
    }
  });

  // =======================
  // Logout feedback
  // =======================
  logoutBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    sessionStorage.removeItem("scanClicked"); 
    logoutBtn.textContent = "Logging out...";
    logoutBtn.style.pointerEvents = "none";
    logoutBtn.style.opacity = "0.7";
    setTimeout(() => (window.location.href = "/logout"), 700);
  });

  // =======================
  // Modal Closing
  // =======================
  document.querySelectorAll(".modal .close").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.closest(".modal")));
  });

  window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal")) closeModal(e.target);
  });
  // =======================
  // Auto-scan on page load
  // =======================

  if (!sessionStorage.getItem("scanClicked")) {
    const scanBtn = document.getElementById("scanNowBtn");
    if (scanBtn) {
      sessionStorage.setItem("scanClicked", "true");
      scanBtn.click();
    }
  }
});

