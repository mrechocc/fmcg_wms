frappe.ui.form.on("Delivery Note", {
  onload_post_render(frm) {
    apply_fmcg_transit_warehouse(frm);
  },
  refresh(frm) {
    apply_fmcg_transit_warehouse(frm);
  },
});

function apply_fmcg_transit_warehouse(frm) {
  if (frm.doc.docstatus !== 0 || frm.__fmcg_transit_warehouse_loading || frm.__fmcg_transit_warehouse_applied) return;

  const salesOrders = [...new Set(
    (frm.doc.items || []).map((row) => row.against_sales_order).filter(Boolean)
  )];
  if (!salesOrders.length || !frm.doc.company) return;

  frm.__fmcg_transit_warehouse_loading = true;
  frappe.call({
    method: "fmcg_wms.api.sales_order.get_transit_delivery_details",
    args: { sales_orders: salesOrders, company: frm.doc.company },
    callback(response) {
      const details = response.message || {};
      const warehouse = details.warehouse;
      const transitOrders = new Set(details.transit_orders || []);
      if (!warehouse || !transitOrders.size) return;

      const mappedRows = (frm.doc.items || []).filter((row) => transitOrders.has(row.against_sales_order));
      mappedRows.forEach((row) => {
        if (row.warehouse !== warehouse) {
          frappe.model.set_value(row.doctype, row.name, "warehouse", warehouse);
        }
      });
      if (mappedRows.length === (frm.doc.items || []).length) {
        frm.doc.set_warehouse = warehouse;
        frm.refresh_field("set_warehouse");
      }
      frm.refresh_field("items");
      frm.__fmcg_transit_warehouse_applied = true;
    },
    always() {
      frm.__fmcg_transit_warehouse_loading = false;
    },
  });
}
