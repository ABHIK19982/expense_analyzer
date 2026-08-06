/**
 * Dashboard: guest landing vs logged-in expense UI.
 */

function validateFile(input) {
  const file = input.files[0];
  if (!file) return false;
  const validExtensions = ["jpg", "jpeg", "pdf"];
  const fileExtension = file.name.split(".").pop().toLowerCase();
  if (!validExtensions.includes(fileExtension)) {
    alert("Please upload only jpg or pdf files");
    input.value = "";
    return false;
  }
  return true;
}

function renderGuest() {
  document.getElementById("guest-view").style.display = "block";
  document.getElementById("user-view").style.display = "none";
}

function renderUser(me) {
  document.getElementById("guest-view").style.display = "none";
  document.getElementById("user-view").style.display = "block";
  document.getElementById("welcome-user").textContent = `Welcome ${me.username}`;

  const monthContainer = document.getElementById("month-buttons");
  monthContainer.innerHTML = "";
  (me.months || []).forEach((month) => {
    const btn = document.createElement("button");
    btn.className = "btn";
    btn.type = "button";
    btn.textContent = month;
    btn.addEventListener("click", async () => {
      try {
        const report = await apiPost("/reports/by-month", { month });
        sessionStorage.setItem("ea_report", JSON.stringify(report));
        window.location.href = "/report.html";
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
    monthContainer.appendChild(btn);
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const me = await apiGet("/auth/me");
    if (me.authenticated) {
      renderUser(me);
    } else {
      renderGuest();
    }
  } catch {
    renderGuest();
  }

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const res = await apiPost("/auth/logout", {});
        showToast(res.message || "Logged out successfully", "success");
      } catch (err) {
        showToast(err.message, "warning");
      }
      setTimeout(() => {
        window.location.href = "/";
      }, 400);
    });
  }

  const expenseForm = document.getElementById("expense-form");
  if (expenseForm) {
    expenseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = new FormData(expenseForm);
      try {
        const res = await apiPost("/expenses", {
          expense_date: form.get("expense_date"),
          commodity: form.get("commodity"),
          type: form.get("type"),
          price: form.get("price"),
        });
        showToast(res.message || "Expense added successfully", "success");
        expenseForm.reset();
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
  }

  const uploadForm = document.getElementById("upload-form");
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById("bill_image");
      if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload");
        return;
      }
      if (!validateFile(fileInput)) return;

      const fd = new FormData();
      fd.append("bill_image", fileInput.files[0]);
      try {
        const res = await apiPostForm("/expenses/upload", fd);
        showToast(res.message || "File Uploaded successfully", "success");
        uploadForm.reset();
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
  }

  const rangeForm = document.getElementById("date-range-form");
  if (rangeForm) {
    rangeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = new FormData(rangeForm);
      try {
        const report = await apiPost("/reports/by-date-range", {
          start_date: form.get("start_date"),
          end_date: form.get("end_date"),
        });
        sessionStorage.setItem("ea_report", JSON.stringify(report));
        window.location.href = "/report.html";
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
  }
});
