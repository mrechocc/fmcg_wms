frappe.ui.form.on("External ERP Import", {
  refresh(frm) {
    if (!frm.doc.source_file || !frm.doc.company) return;

    frm.add_custom_button(__("\u9884\u89c8\u5e76\u6821\u9a8c"), () => run_import(frm, "preview"));
    frm.add_custom_button(__("\u6267\u884c\u5bfc\u5165"), () => {
      frappe.confirm(
        frm.doc.submit_documents
          ? __("\u6821\u9a8c\u901a\u8fc7\u7684\u5355\u636e\u5c06\u4f1a\u63d0\u4ea4\uff0c\u53ef\u80fd\u4ea7\u751f\u5e93\u5b58\u6d41\u6c34\u3002\u662f\u5426\u7ee7\u7eed\uff1f")
          : __("\u6821\u9a8c\u901a\u8fc7\u7684\u5355\u636e\u53ea\u4f1a\u521b\u5efa\u4e3a\u8349\u7a3f\u3002\u662f\u5426\u7ee7\u7eed\uff1f"),
        () => run_import(frm, "run")
      );
    });
  },
});

function run_import(frm, action) {
  frappe.call({
    method: `fmcg_wms.api.external_erp.${action}`,
    args: {
      file_url: frm.doc.source_file,
      import_type: frm.doc.import_type,
      company: frm.doc.company,
      submit_documents: frm.doc.submit_documents || 0,
      item_group: frm.doc.item_group,
      sales_uom: frm.doc.sales_uom,
    },
    freeze: true,
    freeze_message: action === "preview" ? __("\u6b63\u5728\u6821\u9a8c Excel \u6570\u636e...") : __("\u6b63\u5728\u5bfc\u5165\u5916\u90e8 ERP \u6570\u636e..."),
    callback(response) {
      const result = response.message || {};
      const errors = result.errors || [];
      const skipped = result.skipped || [];
      const isMasterData = [__("\u5ba2\u6237\u57fa\u7840\u8d44\u6599"), __("\u7269\u6599\u57fa\u7840\u8d44\u6599")].includes(frm.doc.import_type);
      const recordLabel = isMasterData ? __("\u57fa\u7840\u8d44\u6599\u8bb0\u5f55") : __("\u5355\u636e");
      const summary = [
        `${__("\u6e90\u660e\u7ec6\u884c")}: ${result.source_rows || 0}`,
        `${__("\u53ef\u5bfc\u5165")}${recordLabel}: ${result.ready_documents || 0}`,
        `${__("\u5df2\u8df3\u8fc7")}${recordLabel}: ${result.skipped_documents || 0}`,
        `${__("\u5f02\u5e38")}: ${errors.length}`,
      ].join("\n");
      frm.set_value("result_summary", summary);
      frm.set_value(
        "error_log",
        [...errors, ...skipped.map((row) => `${__("\u5df2\u8df3\u8fc7")}: ${row.external_no} -> ${row.existing}`)].join("\n")
      );
      frm.save();
      if (errors.length) {
        frappe.msgprint({ title: __("\u6821\u9a8c\u5931\u8d25"), indicator: "red", message: errors.join("<br>") });
      } else if (action === "run") {
        frappe.show_alert({ message: __("\u5bfc\u5165\u5b8c\u6210"), indicator: "green" });
      }
    },
  });
}
