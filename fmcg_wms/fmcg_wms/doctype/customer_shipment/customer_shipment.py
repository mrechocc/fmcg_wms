import frappe
from frappe import _
from frappe.model.document import Document

from fmcg_wms.services.shipment import cancel_shipment, validate_shipment


class CustomerShipment(Document):
    def validate(self):
        if self.docstatus == 0:
            validate_shipment(self)

    def before_submit(self):
        if not self.stock_entry or self.status != "Dispatched":
            frappe.throw(_("Use Confirm Dispatch to submit a Customer Shipment."))
        entry = frappe.get_doc("Stock Entry", self.stock_entry)
        if (
            entry.docstatus != 1
            or entry.company != self.company
            or entry.purpose != "Material Transfer"
            or entry.from_warehouse != self.source_warehouse
            or entry.to_warehouse != self.transit_warehouse
        ):
            frappe.throw(_("Dispatch Stock Entry does not match this Customer Shipment."))

    def on_cancel(self):
        cancel_shipment(self)
        self.db_set("status", "Cancelled", update_modified=False)
