frappe.ui.form.on("Sales Order", {
  refresh(frm) {
    if (frm.doc.docstatus !== 1 || flt(frm.doc.per_delivered) >= 100) return;

    if (frm.doc.fmcg_delivery_mode === "\u5f53\u573a\u4ea4\u4ed8") {
      add_immediate_delivery_button(frm);
    }
    if (frm.doc.fmcg_delivery_mode === "\u5728\u9014\u4ea4\u4ed8") {
      add_transit_transfer_button(frm);
    }
  },
});

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

function add_transit_transfer_button(frm) {
  frm.add_custom_button(__("\u751f\u6210\u5728\u9014\u8c03\u62e8\u5355"), () => {
    frappe.confirm(
      __("\u7cfb\u7edf\u5c06\u628a\u672c\u9500\u552e\u8ba2\u5355\u5f53\u524d\u672a\u4ea4\u4ed8\u7684\u6570\u91cf\u8f6c\u5165\u672c\u516c\u53f8\u9ed8\u8ba4\u5ba2\u6237\u5728\u9014\u4ed3\u3002\u662f\u5426\u7ee7\u7eed\uff1f"),
      () => frappe.call({
        method: "fmcg_wms.api.sales_order.create_transit_transfer",
        args: { sales_order_name: frm.doc.name },
        freeze: true,
        freeze_message: "\u6b63\u5728\u521b\u5efa\u5728\u9014\u8c03\u62e8\u5355...",
        callback(response) {
          if (response.message) frappe.set_route("Form", "Customer Shipment", response.message.shipment);
        },
      }),
    );
  }, __("\u53d1\u8d27"));
}
