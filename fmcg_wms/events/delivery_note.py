import frappe
from frappe import _
from frappe.utils import flt

from fmcg_wms.services.sales_order import (
    TRANSIT_DELIVERY_MODE,
    get_default_transit_warehouse,
    get_submitted_transit_quantities,
)


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


def validate_transit_delivery_before_submit(delivery_note) -> None:
    """A transit Delivery Note cannot sign for more than its approved transfers."""
    transit_orders = _get_transit_sales_orders(delivery_note)
    if not transit_orders:
        return

    requested_quantities = {}
    for row in delivery_note.items:
        if row.against_sales_order not in transit_orders:
            continue
        if not row.so_detail:
            frappe.throw(_("Transit Delivery Note rows must link to a Sales Order Item."))
        requested_quantities.setdefault(row.against_sales_order, {})
        requested_quantities[row.against_sales_order][row.so_detail] = (
            flt(requested_quantities[row.against_sales_order].get(row.so_detail)) + flt(row.qty)
        )

    for sales_order_name, order_requested_quantities in requested_quantities.items():
        sales_order = frappe.get_doc("Sales Order", sales_order_name)
        if sales_order.company != delivery_note.company:
            frappe.throw(_("The Delivery Note company must match its linked Sales Order company."))
        transferred_quantities = get_submitted_transit_quantities(sales_order_name)
        delivered_quantities = _get_submitted_delivery_quantities(sales_order_name, delivery_note.name)
        for sales_order_item, requested_qty in order_requested_quantities.items():
            available_qty = flt(transferred_quantities.get(sales_order_item)) - flt(
                delivered_quantities.get(sales_order_item)
            )
            if requested_qty > available_qty:
                frappe.throw(
                    _("Sales Order Item {0} has only {1} approved transit quantity available for delivery; this Delivery Note requests {2}.").format(
                        sales_order_item, available_qty, requested_qty
                    )
                )


def _get_submitted_delivery_quantities(sales_order_name: str, current_delivery_note: str | None) -> dict[str, float]:
    rows = frappe.db.sql(
        """
        SELECT item.so_detail, COALESCE(SUM(item.qty), 0) AS delivered_qty
        FROM `tabDelivery Note Item` AS item
        INNER JOIN `tabDelivery Note` AS delivery_note ON delivery_note.name = item.parent
        WHERE delivery_note.docstatus = 1
          AND item.against_sales_order = %(sales_order_name)s
          AND (%(current_delivery_note)s IS NULL OR item.parent != %(current_delivery_note)s)
        GROUP BY item.so_detail
        """,
        {
            "sales_order_name": sales_order_name,
            "current_delivery_note": current_delivery_note,
        },
        as_dict=True,
    )
    return {row.so_detail: flt(row.delivered_qty) for row in rows if row.so_detail}
