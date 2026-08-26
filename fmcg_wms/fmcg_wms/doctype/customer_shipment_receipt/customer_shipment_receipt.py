from frappe.model.document import Document

from fmcg_wms.services.receipt import cancel_receipt, populate_receipt_header, submit_receipt, validate_receipt


class CustomerShipmentReceipt(Document):
    def validate(self):
        if self.customer_shipment:
            populate_receipt_header(self)
        if self.docstatus == 0 and self.items:
            validate_receipt(self)

    def on_submit(self):
        submit_receipt(self)

    def on_cancel(self):
        cancel_receipt(self)
        self.db_set("status", "Cancelled", update_modified=False)
