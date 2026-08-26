import frappe
from frappe import _
from frappe.utils import date_diff, flt, nowdate


def execute(filters=None):
    filters = filters or {}
    columns = [
        {"label": _("Shipment"), "fieldname": "shipment", "fieldtype": "Link", "options": "Customer Shipment", "width": 150},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Dispatch Date"), "fieldname": "dispatch_date", "fieldtype": "Date", "width": 100},
        {"label": _("Transit Days"), "fieldname": "transit_days", "fieldtype": "Int", "width": 100},
        {"label": _("Expected Receipt"), "fieldname": "expected_receipt_date", "fieldtype": "Date", "width": 110},
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Transit Qty"), "fieldname": "remaining_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Transit Warehouse"), "fieldname": "transit_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 170},
        {"label": _("Tracking No"), "fieldname": "tracking_no", "fieldtype": "Data", "width": 130},
    ]
    shipment_filters = {"docstatus": 1}
    if filters.get("company"):
        shipment_filters["company"] = filters.company
    if filters.get("customer"):
        shipment_filters["customer"] = filters.customer

    shipments = frappe.get_all(
        "Customer Shipment",
        filters=shipment_filters,
        fields=[
            "name", "status", "customer", "dispatch_date", "expected_receipt_date",
            "transit_warehouse", "tracking_no",
        ],
        order_by="dispatch_date asc, name asc",
    )
    data = []
    for shipment in shipments:
        for item in frappe.get_all(
            "Customer Shipment Item",
            filters={"parent": shipment.name, "parenttype": "Customer Shipment"},
            fields=["item_code", "uom", "remaining_qty"],
        ):
            if flt(item.remaining_qty) <= 0:
                continue
            data.append(
                {
                    "shipment": shipment.name,
                    "status": shipment.status,
                    "customer": shipment.customer,
                    "dispatch_date": shipment.dispatch_date,
                    "transit_days": date_diff(nowdate(), shipment.dispatch_date),
                    "expected_receipt_date": shipment.expected_receipt_date,
                    "item_code": item.item_code,
                    "uom": item.uom,
                    "remaining_qty": item.remaining_qty,
                    "transit_warehouse": shipment.transit_warehouse,
                    "tracking_no": shipment.tracking_no,
                }
            )
    return columns, data
