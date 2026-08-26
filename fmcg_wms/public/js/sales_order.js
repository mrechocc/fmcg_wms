frappe.ui.form.on("Sales Order", {
  refresh(frm) {
    if (frm.doc.docstatus !== 1 || flt(frm.doc.per_delivered) >= 100) return;

    frm.add_custom_button(__("当场交付"), () => {
      frappe.confirm(
        __("系统将从订单商品行的来源仓库直接创建并提交销售出库单。是否确认客户已当场提货？"),
        () => frappe.call({
          method: "fmcg_wms.api.sales_order.create_immediate_delivery",
          args: { sales_order_name: frm.doc.name },
          freeze: true,
          freeze_message: __("正在创建销售出库单..."),
          callback(response) {
            if (!response.message) return;
            frappe.set_route("Form", "Delivery Note", response.message.delivery_note);
          },
        }),
      );
    }, __("操作"));

    frm.add_custom_button(__("创建在途调拨单"), () => {
      frappe.prompt([
        {
          fieldname: "transit_warehouse",
          label: __("客户在途仓"),
          fieldtype: "Link",
          options: "Warehouse",
          reqd: 1,
          get_query: () => ({
            filters: { company: frm.doc.company, warehouse_type: "Transit", is_group: 0 },
          }),
        },
        {
          fieldname: "expected_receipt_date",
          label: __("预计签收日期"),
          fieldtype: "Date",
          default: frm.doc.delivery_date,
        },
      ], (values) => {
        frappe.confirm(
          __("系统将把本销售订单当前未交付的数量转入客户在途仓。是否继续？"),
          () => frappe.call({
            method: "fmcg_wms.api.sales_order.create_transit_transfer",
            args: {
              sales_order_name: frm.doc.name,
              transit_warehouse: values.transit_warehouse,
              expected_receipt_date: values.expected_receipt_date,
            },
            freeze: true,
            freeze_message: __("正在创建在途调拨单..."),
            callback(response) {
              if (!response.message) return;
              frappe.set_route("Form", "Customer Shipment", response.message.shipment);
            },
          }),
        );
      }, __("创建在途调拨单"), __("创建"));
    }, __("操作"));
  },
});
