import frappe

from fmcg_wms.services.sales_order import TRANSIT_DELIVERY_MODE, get_default_transit_warehouse


def apply_transit_warehouse(delivery_note) -> None:
    """Make Sales Order Delivery Notes issue transit-mode items from the transit warehouse."""
    transit_orders = _get_transit_sales_orders(delivery_note)
    if not transit_orders:
        return

    transit_warehouse = get_default_transit_warehouse(delivery_note.company)
    for row in delivery_note.items:
        if row.against_sales_order in transit_orders:
            row.warehouse = transit_warehouse
    if all(row.against_sales_order in transit_orders for row in delivery_note.items if row.against_sales_order):
        delivery_note.set_warehouse = transit_warehouse


def _get_transit_sales_orders(delivery_note) -> set[str]:
    sales_orders = {row.against_sales_order for row in delivery_note.items if row.against_sales_order}
    if not sales_orders:
        return set()
    return set(
        frappe.get_all(
            "Sales Order",
            filters={"name": ["in", list(sales_orders)], "fmcg_delivery_mode": TRANSIT_DELIVERY_MODE},
            pluck="name",
        )
    )
