const fmcgExistingSalesOrderListSettings = frappe.listview_settings["Sales Order"] || {};

frappe.listview_settings["Sales Order"] = {
  ...fmcgExistingSalesOrderListSettings,
  formatters: {
    ...(fmcgExistingSalesOrderListSettings.formatters || {}),
    per_delivered(value) {
      return fmcg_format_percent(value);
    },
    per_billed(value) {
      return fmcg_format_percent(value);
    },
  },
};

function fmcg_format_percent(value) {
  const numericValue = Number.parseFloat(value);
  const percent = Number.isFinite(numericValue) ? Math.max(0, Math.min(100, numericValue)) : 0;
  const label = `${Math.round(percent)}%`;
  return `
    <div class="fmcg-percent-cell" title="${label}">
      <div class="fmcg-percent-track">
        <div class="fmcg-percent-fill" style="width: ${percent}%"></div>
      </div>
      <span class="fmcg-percent-label">${label}</span>
    </div>
  `;
}
