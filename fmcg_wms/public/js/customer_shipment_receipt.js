frappe.ui.form.on("Customer Shipment Receipt", {
  refresh(frm) {
    frm.set_query("customer_shipment", () => ({ filters: { docstatus: 1 } }));
    if (frm.doc.docstatus === 0 && frm.doc.customer_shipment) {
      frm.add_custom_button(__("Load Pending Transit Items"), () => load_pending_items(frm), __("Actions"));
    }
  },
  customer_shipment(frm) {
    if (frm.doc.customer_shipment) load_pending_items(frm);
  },
});

function load_pending_items(frm) {
  frappe.call({
    method: "fmcg_wms.api.shipment.get_pending_receipt_items",
    args: { shipment_name: frm.doc.customer_shipment },
    freeze: true,
    callback(response) {
      const rows = response.message || [];
      frm.clear_table("items");
      rows.forEach((source) => {
        const row = frm.add_child("items");
        Object.assign(row, source);
      });
      frm.refresh_field("items");
    },
  });
}
