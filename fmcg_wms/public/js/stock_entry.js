frappe.ui.form.on("Stock Entry", {
  refresh(frm) {
    if (
      frm.doc.docstatus !== 0 ||
      !frm.doc.fmcg_sales_order ||
      frm.doc.purpose !== "Material Transfer"
    ) {
      return;
    }

    frm.add_custom_button(__("核准并提交"), () => {
      frappe.confirm(
        __("请确认明细数量就是本次实际从中心仓发出的数量。提交后将正式扣减中心仓并增加在途仓库存。"),
        () => frm.savesubmit(),
      );
    }, __("发货"));
  },
});
