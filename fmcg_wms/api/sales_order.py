import frappe
from frappe import _

from fmcg_wms.services.sales_order import (
    TRANSIT_DELIVERY_MODE,
    create_immediate_delivery as create_delivery,
    create_transit_transfer as create_transfer,
    get_default_transit_warehouse,
    get_default_source_warehouse,
    get_transit_transfer_status as get_transfer_status,
)


@frappe.whitelist()
def get_default_source_warehouse_for_company(company: str):
    return {"warehouse": get_default_source_warehouse(company)}


@frappe.whitelist()
def create_transit_transfer(sales_order_name: str):
    stock_entry = create_transfer(sales_order_name)
    return {"stock_entry": stock_entry.name, "docstatus": stock_entry.docstatus}


@frappe.whitelist()
def get_transit_transfer_status(sales_order_name: str):
    return get_transfer_status(sales_order_name)


@frappe.whitelist()
def create_immediate_delivery(sales_order_name: str, posting_date=None):
    delivery_note = create_delivery(sales_order_name, posting_date)
    return {"delivery_note": delivery_note.name}


@frappe.whitelist()
def get_transit_delivery_details(sales_orders, company: str):
    """Return the transit warehouse for the transit-mode Sales Orders in a Delivery Note."""
    if isinstance(sales_orders, str):
        sales_orders = frappe.parse_json(sales_orders)
    sales_orders = list(set(sales_orders or []))
    if not sales_orders:
        return {"transit_orders": []}

    for sales_order_name in sales_orders:
        sales_order = frappe.get_doc("Sales Order", sales_order_name)
        sales_order.check_permission("read")
        if sales_order.company != company:
            frappe.throw(_("Sales Order company must match the Delivery Note company."))

    transit_orders = frappe.get_all(
        "Sales Order",
        filters={"name": ["in", sales_orders], "fmcg_delivery_mode": TRANSIT_DELIVERY_MODE},
        pluck="name",
    )
    if not transit_orders:
        return {"transit_orders": []}

    return {
        "transit_orders": transit_orders,
        "warehouse": get_default_transit_warehouse(company),
    }
