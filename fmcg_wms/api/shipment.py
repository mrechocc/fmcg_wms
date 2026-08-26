import frappe

from fmcg_wms.services.receipt import get_pending_items
from fmcg_wms.services.shipment import dispatch, return_from_transit


@frappe.whitelist()
def confirm_dispatch(shipment_name: str):
    return dispatch(shipment_name).name


@frappe.whitelist()
def get_pending_receipt_items(shipment_name: str):
    return get_pending_items(shipment_name)


@frappe.whitelist()
def return_items(shipment_name: str, target_warehouse: str, quantities, reason: str):
    if isinstance(quantities, str):
        quantities = frappe.parse_json(quantities)
    return return_from_transit(shipment_name, target_warehouse, quantities, reason).name
