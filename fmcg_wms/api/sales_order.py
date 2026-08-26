import frappe

from fmcg_wms.services.sales_order import (
    create_immediate_delivery as create_delivery,
    create_transit_transfer as create_transfer,
    get_default_source_warehouse,
)


@frappe.whitelist()
def get_default_source_warehouse_for_company(company: str):
    return {"warehouse": get_default_source_warehouse(company)}


@frappe.whitelist()
def create_transit_transfer(sales_order_name: str):
    stock_entry = create_transfer(sales_order_name)
    return {"stock_entry": stock_entry.name}


@frappe.whitelist()
def create_immediate_delivery(sales_order_name: str, posting_date=None):
    delivery_note = create_delivery(sales_order_name, posting_date)
    return {"delivery_note": delivery_note.name}
