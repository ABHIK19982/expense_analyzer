/**
 * Render expense report table and charts from sessionStorage.
 */

document.addEventListener("DOMContentLoaded", () => {
  const raw = sessionStorage.getItem("ea_report");
  if (!raw) {
    showToast("No report data. Returning to dashboard.", "warning");
    setTimeout(() => {
      window.location.href = "/";
    }, 800);
    return;
  }

  let report;
  try {
    report = JSON.parse(raw);
  } catch {
    window.location.href = "/";
    return;
  }

  document.getElementById("report-title").textContent =
    `Monthly Expense Report - ${report.date_month_range}`;

  const thead = document.querySelector("#report-table thead tr");
  const tbody = document.querySelector("#report-table tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  (report.columns || []).forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    thead.appendChild(th);
  });

  const rows = report.rows || [];
  rows.forEach((row, rowIndex) => {
    const tr = document.createElement("tr");
    const isLast = rowIndex === rows.length - 1;
    row.forEach((cell, cellIndex) => {
      const td = document.createElement("td");
      td.textContent = cell;
      if (isLast) {
        td.style.borderTop = "2px solid white";
      } else if (cellIndex === 3) {
        td.style.color = "#961006";
        td.style.borderLeft = "1px solid white";
      } else if (cellIndex === 4) {
        td.style.color = "#529906";
        td.style.borderLeft = "1px solid white";
      } else if (cellIndex === 5) {
        td.style.borderLeft = "1px solid white";
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  document.getElementById("expense-graph").src =
    `data:image/png;base64,${report.expense_graph}`;
  document.getElementById("count-graph").src =
    `data:image/png;base64,${report.count_graph}`;
  document.getElementById("trend-graph").src =
    `data:image/png;base64,${report.trend_graph}`;
});
