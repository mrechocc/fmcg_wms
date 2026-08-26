frappe.ui.form.on("Customer Shipment", {
  refresh(frm) {
    frm.set_query("sales_order", () => ({
      filters: { company: frm.doc.company, customer: frm.doc.customer, docstatus: 1 },
    }));

    if (frm.doc.docstatus === 0 && !frm.is_new()) {
      frm.add_custom_button(__("Confirm Dispatch"), () => {
        frappe.confirm(
          __("This will move stock from the source warehouse to the transit warehouse and submit the shipment."),
          () => frappe.call({
            method: "fmcg_wms.api.shipment.confirm_dispatch",
            args: { shipment_name: frm.doc.name },
            freeze: true,
            freeze_message: __("Creating transit transfer..."),
            callback: () => frm.reload_doc(),
          })
        );
      }, __("Actions"));
    }

    if (frm.doc.docstatus === 1 && ["Dispatched", "Partially Received"].includes(frm.doc.status)) {
      frm.add_custom_button(__("Return All Remaining"), () => {
        const remaining = (frm.doc.items || []).filter((row) => flt(row.remaining_qty) > 0);
        if (!remaining.length) return;
        frappe.prompt([
          { fieldname: "target_warehouse", label: __("Return Warehouse"), fieldtype: "Link", options: "Warehouse", reqd: 1 },
          { fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
        ], (values) => frappe.call({
          method: "fmcg_wms.api.shipment.return_items",
          args: {
            shipment_name: frm.doc.name,
            target_warehouse: values.target_warehouse,
            reason: values.reason,
            quantities: remaining.map((row) => ({ customer_shipment_item: row.name, qty: row.remaining_qty })),
          },
          freeze: true,
          freeze_message: __("Returning transit inventory..."),
          callback: () => frm.reload_doc(),
        }), __("Return Remaining Transit Inventory"), __("Submit"));
      }, __("Actions"));
    }
  },
  sales_order(frm) {
    if (!frm.doc.sales_order) return;
    frappe.db.get_doc("Sales Order", frm.doc.sales_order).then((sales_order) => {
      if (!frm.doc.customer) frm.set_value("customer", sales_order.customer);
      if (!frm.doc.company) frm.set_value("company", sales_order.company);
      frm.clear_table("items");
      (sales_order.items || []).forEach((source) => {
        const pending_qty = flt(source.qty) - flt(source.delivered_qty);
        if (pending_qty <= 0) return;
        const row = frm.add_child("items");
        row.sales_order_item = source.name;
        row.item_code = source.item_code;
        row.uom = source.uom;
        row.conversion_factor = source.conversion_factor || 1;
        row.source_warehouse = source.warehouse || frm.doc.source_warehouse;
        row.dispatched_qty = pending_qty;
      });
      frm.refresh_field("items");
    });
  },
});
