import frappe
from frappe import _
from frappe.utils import flt

from fmcg_wms.services.sales_order import (
    TRANSIT_DELIVERY_MODE,
    get_default_transit_warehouse,
    get_submitted_transit_quantities,
)


def validate_transit_transfer_before_submit(stock_entry) -> None:
    """Prevent a warehouse approval from exceeding its Sales Order allocation."""
    sales_order_name = stock_entry.get("fmcg_sales_order")
    if not sales_order_name:
        return
    if stock_entry.purpose != "Material Transfer":
        frappe.throw(_("FMCG transit transfers must use Material Transfer."))

    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    if sales_order.docstatus != 1 or sales_order.fmcg_delivery_mode != TRANSIT_DELIVERY_MODE:
        frappe.throw(_("The linked Sales Order is not a submitted transit-delivery order."))
    if stock_entry.company != sales_order.company:
        frappe.throw(_("The transit transfer company must match the linked Sales Order company."))

    order_items = {row.name: row for row in sales_order.items}
    order_quantities = {name: flt(row.qty) for name, row in order_items.items()}
    submitted_quantities = get_submitted_transit_quantities(sales_order.name, stock_entry.name)
    requested_quantities = {}
    transit_warehouse = get_default_transit_warehouse(sales_order.company)

    for row in stock_entry.items:
        sales_order_item = row.get("fmcg_sales_order_item")
        if not sales_order_item or sales_order_item not in order_items:
            frappe.throw(_("Every material movement row must link to a Sales Order Item before approval."))
        if row.item_code != order_items[sales_order_item].item_code:
            frappe.throw(_("A transit transfer row's item must match its linked Sales Order Item."))
        if row.t_warehouse != transit_warehouse:
            frappe.throw(_("Transit transfers must move to warehouse {0}.").format(transit_warehouse))
        requested_quantities[sales_order_item] = flt(requested_quantities.get(sales_order_item)) + flt(row.qty)

    for sales_order_item, requested_qty in requested_quantities.items():
        if requested_qty <= 0:
            frappe.throw(_("Approved transfer quantities must be greater than zero."))
        available_qty = order_quantities[sales_order_item] - flt(submitted_quantities.get(sales_order_item))
        if requested_qty > available_qty:
            frappe.throw(
                _("Sales Order Item {0} can transfer at most {1}; this approval requests {2}.").format(
                    sales_order_item, available_qty, requested_qty
                )
            )


def record_transit_transfer_submission(stock_entry) -> None:
    if not stock_entry.get("fmcg_sales_order"):
        return
    sales_order = frappe.get_doc("Sales Order", stock_entry.fmcg_sales_order)
    if sales_order.fmcg_delivery_mode != TRANSIT_DELIVERY_MODE:
        return
    if sales_order.meta.has_field("fmcg_transit_stock_entry"):
        sales_order.db_set("fmcg_transit_stock_entry", stock_entry.name, update_modified=False)
    sales_order.add_comment("Info", _("Approved transit Stock Entry {0}.").format(stock_entry.name))
