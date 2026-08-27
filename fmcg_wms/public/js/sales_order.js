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

    if (
      frm.doc.fmcg_delivery_mode === "\u5f53\u573a\u4ea4\u4ed8" ||
      frm.doc.fmcg_delivery_mode === "\u5728\u9014\u4ea4\u4ed8"
    ) {
      frm.remove_custom_button(__("Delivery Note"), __("Create"));
    }

    if (frm.doc.fmcg_delivery_mode === "\u5f53\u573a\u4ea4\u4ed8") {
      add_immediate_delivery_button(frm);
    }
    if (frm.doc.fmcg_delivery_mode === "\u5728\u9014\u4ea4\u4ed8") {
      add_transit_stock_entry_buttons(frm);
    }
  },
  on_submit(frm) {
    if (frm.doc.fmcg_delivery_mode !== "\u5728\u9014\u4ea4\u4ed8") return;
    frappe.db.get_value("Sales Order", frm.doc.name, "fmcg_transit_stock_entry", (response) => {
      const stockEntry = response && response.fmcg_transit_stock_entry;
      if (stockEntry) {
        frappe.set_route("Form", "Stock Entry", stockEntry);
      } else {
        frm.reload_doc();
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

function add_transit_stock_entry_buttons(frm) {
  frm.add_custom_button(__("\u67e5\u770b\u7269\u6599\u79fb\u52a8"), () => {
    frappe.set_route("List", "Stock Entry", { fmcg_sales_order: frm.doc.name });
  }, __("\u53d1\u8d27"));

  frappe.call({
    method: "fmcg_wms.api.sales_order.get_transit_transfer_status",
    args: { sales_order_name: frm.doc.name },
    callback(response) {
      const status = response.message || {};
      if (status.has_remaining_quantity || status.draft_stock_entry) {
        add_create_or_open_transfer_button(frm, status.draft_stock_entry);
      }
      frm.add_custom_button(__("\u67e5\u770b\u5f85\u9001\u8d27\u660e\u7ec6"), () => {
        show_transit_delivery_availability(frm);
      }, __("\u53d1\u8d27"));
      if (status.has_submitted_transfer) {
        frm.add_custom_button(__("\u521b\u5efa\u672c\u6b21\u9001\u8d27\u5355"), () => {
          frappe.call({
            method: "fmcg_wms.api.sales_order.create_transit_delivery_note",
            args: { sales_order_name: frm.doc.name },
            freeze: true,
            freeze_message: "\u6b63\u5728\u521b\u5efa\u672c\u6b21\u9001\u8d27\u5355...",
            callback(response) {
              const deliveryNote = response.message && response.message.delivery_note;
              if (deliveryNote) frappe.set_route("Form", "Delivery Note", deliveryNote);
            },
          });
        }, __("\u53d1\u8d27"));
      }
    },
  });
}

function show_transit_delivery_availability(frm) {
  frappe.call({
    method: "fmcg_wms.api.sales_order.get_transit_delivery_availability",
    args: { sales_order_name: frm.doc.name },
    freeze: true,
    callback(response) {
      const lines = (response.message && response.message.lines) || [];
      const body = lines.map((line) => `
        <tr>
          <td>${frappe.utils.escape_html(line.item_code || "")}</td>
          <td>${frappe.utils.escape_html(line.item_name || "")}</td>
          <td class="text-right">${line.ordered_qty}</td>
          <td class="text-right">${line.approved_qty}</td>
          <td class="text-right">${line.delivered_qty}</td>
          <td class="text-right"><strong>${line.available_to_deliver_qty}</strong></td>
          <td class="text-right">${line.not_transferred_qty}</td>
          <td>${frappe.utils.escape_html(line.uom || "")}</td>
        </tr>
      `).join("");
      frappe.msgprint({
        title: __("\u5f85\u9001\u8d27\u660e\u7ec6"),
        wide: true,
        message: `
          <div class="table-responsive">
            <table class="table table-bordered">
              <thead>
                <tr>
                  <th>${__("\u7269\u6599")}</th>
                  <th>${__("\u540d\u79f0")}</th>
                  <th class="text-right">${__("\u8ba2\u5355\u6570\u91cf")}</th>
                  <th class="text-right">${__("\u5df2\u6838\u51c6\u8c03\u62e8")}</th>
                  <th class="text-right">${__("\u5df2\u9001\u8d27")}</th>
                  <th class="text-right">${__("\u672c\u6b21\u53ef\u9001")}</th>
                  <th class="text-right">${__("\u5c1a\u672a\u8c03\u62e8")}</th>
                  <th>${__("\u5355\u4f4d")}</th>
                </tr>
              </thead>
              <tbody>${body}</tbody>
            </table>
          </div>
        `,
      });
    },
  });
}

function add_create_or_open_transfer_button(frm, draftStockEntry) {
  const label = draftStockEntry ? __("\u6253\u5f00\u5f85\u6838\u51c6\u8c03\u62e8") : __("\u521b\u5efa\u672c\u6b21\u8c03\u62e8");
  frm.add_custom_button(label, () => {
    if (draftStockEntry) {
      frappe.set_route("Form", "Stock Entry", draftStockEntry);
      return;
    }
    frappe.call({
      method: "fmcg_wms.api.sales_order.create_transit_transfer",
      args: { sales_order_name: frm.doc.name },
      freeze: true,
      freeze_message: "\u6b63\u5728\u521b\u5efa\u5f85\u6838\u51c6\u8c03\u62e8...",
      callback(response) {
        const stockEntry = response.message && response.message.stock_entry;
        if (stockEntry) frappe.set_route("Form", "Stock Entry", stockEntry);
      },
    });
  }, __("\u53d1\u8d27"));
}
