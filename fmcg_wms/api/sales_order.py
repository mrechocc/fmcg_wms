import frappe

from fmcg_wms.services.sales_order import (
    create_immediate_delivery as create_delivery,
    create_transit_transfer as create_transfer,
)


@frappe.whitelist()
def create_transit_transfer(sales_order_name: str, transit_warehouse: str, expected_receipt_date=None):
    shipment = create_transfer(sales_order_name, transit_warehouse, expected_receipt_date)
    return {"shipment": shipment.name, "stock_entry": shipment.stock_entry}


@frappe.whitelist()
def create_immediate_delivery(sales_order_name: str, posting_date=None):
    delivery_note = create_delivery(sales_order_name, posting_date)
    return {"delivery_note": delivery_note.name}
