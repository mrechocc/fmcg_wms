frappe.ui.form.on("Sales Order", {
  onload(frm) {
    set_default_source_warehouse(frm);
  },
  company(frm) {
    set_default_source_warehouse(frm);
  },
  refresh(frm) {
    if (frm.doc.docstatus === 0) set_default_source_warehouse(frm);
    if (frm.doc.docstatus !== 1 || flt(frm.doc.per_delivered) >= 100) return;

    if (frm.doc.fmcg_delivery_mode === "\u5f53\u573a\u4ea4\u4ed8") {
      add_immediate_delivery_button(frm);
    }
    if (frm.doc.fmcg_delivery_mode === "\u5728\u9014\u4ea4\u4ed8") {
      add_transit_shipment_button(frm);
    }
  },
  on_submit(frm) {
    if (frm.doc.fmcg_delivery_mode !== "\u5728\u9014\u4ea4\u4ed8") return;
    frm.reload_doc().then(() => {
      if (frm.doc.fmcg_transit_stock_entry) {
        frappe.set_route("Form", "Stock Entry", frm.doc.fmcg_transit_stock_entry);
      }
    });
  },
});

function set_default_source_warehouse(frm) {
  if (!frm.doc.company || frm.doc.set_warehouse || frm.__fmcg_loading_default_warehouse) return;
  frm.__fmcg_loading_default_warehouse = true;
  frappe.call({
    method: "fmcg_wms.api.sales_order.get_default_source_warehouse_for_company",
    args: { company: frm.doc.company },
    callback(response) {
      const warehouse = response.message && response.message.warehouse;
      if (!warehouse) return;
      frm.set_value("set_warehouse", warehouse);
      (frm.doc.items || []).forEach((row) => {
        if (!row.warehouse) frappe.model.set_value(row.doctype, row.name, "warehouse", warehouse);
      });
    },
    always() {
      frm.__fmcg_loading_default_warehouse = false;
    },
  });
}

function add_immediate_delivery_button(frm) {
  frm.add_custom_button(__("\u786e\u8ba4\u5f53\u573a\u4ea4\u4ed8"), () => {
    frappe.confirm(
      __("\u7cfb\u7edf\u5c06\u4ece\u8ba2\u5355\u5546\u54c1\u884c\u7684\u6765\u6e90\u4ed3\u5e93\u76f4\u63a5\u521b\u5efa\u5e76\u63d0\u4ea4\u9500\u552e\u51fa\u5e93\u5355\u3002\u662f\u5426\u786e\u8ba4\u5ba2\u6237\u5df2\u5f53\u573a\u63d0\u8d27\uff1f"),
      () => frappe.call({
        method: "fmcg_wms.api.sales_order.create_immediate_delivery",
        args: { sales_order_name: frm.doc.name },
        freeze: true,
        freeze_message: "\u6b63\u5728\u521b\u5efa\u9500\u552e\u51fa\u5e93\u5355...",
        callback(response) {
          if (response.message) frappe.set_route("Form", "Delivery Note", response.message.delivery_note);
        },
      }),
    );
  }, __("\u53d1\u8d27"));
}

function add_transit_shipment_button(frm) {
  if (!frm.doc.fmcg_transit_stock_entry) {
    frm.add_custom_button(__("\u8865\u5efa\u7269\u6599\u79fb\u52a8"), () => {
      frappe.confirm(
        __("\u7cfb\u7edf\u5c06\u4e3a\u8fd9\u5f20\u5df2\u63d0\u4ea4\u7684\u9500\u552e\u8ba2\u5355\u8865\u5efa\u4e00\u5f20\u4e2d\u5fc3\u4ed3\u81f3\u5ba2\u6237\u5728\u9014\u4ed3\u7684\u7269\u6599\u79fb\u52a8\u3002\u662f\u5426\u7ee7\u7eed\uff1f"),
        () => frappe.call({
          method: "fmcg_wms.api.sales_order.create_transit_transfer",
          args: { sales_order_name: frm.doc.name },
          freeze: true,
          freeze_message: "\u6b63\u5728\u521b\u5efa\u7269\u6599\u79fb\u52a8...",
          callback(response) {
            if (response.message) frappe.set_route("Form", "Stock Entry", response.message.stock_entry);
          },
        }),
      );
    }, __("\u53d1\u8d27"));
    return;
  }
  frm.add_custom_button(__("\u67e5\u770b\u7269\u6599\u79fb\u52a8"), () => {
    frappe.set_route("Form", "Stock Entry", frm.doc.fmcg_transit_stock_entry);
  }, __("\u53d1\u8d27"));
}
