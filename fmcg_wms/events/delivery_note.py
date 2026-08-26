import frappe
from frappe import _
from frappe.utils import flt

from fmcg_wms.services.sales_order import TRANSIT_DELIVERY_MODE, get_default_transit_warehouse
from fmcg_wms.services.status import get_shipment_status


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


def sync_transit_shipment_on_submit(delivery_note) -> None:
    if _is_receipt_generated_delivery(delivery_note):
        return
    _sync_shipment_quantities(delivery_note, multiplier=1)


def sync_transit_shipment_on_cancel(delivery_note) -> None:
    if _is_receipt_generated_delivery(delivery_note):
        return
    _sync_shipment_quantities(delivery_note, multiplier=-1)


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


def _sync_shipment_quantities(delivery_note, multiplier: int) -> None:
    transit_orders = _get_transit_sales_orders(delivery_note)
    if not transit_orders:
        return

    quantity_by_shipment_item = {}
    for row in delivery_note.items:
        if row.against_sales_order not in transit_orders or not row.so_detail:
            continue
        shipment_name = _get_shipment_name(row.against_sales_order)
        key = (shipment_name, row.so_detail)
        quantity_by_shipment_item[key] = quantity_by_shipment_item.get(key, 0) + flt(row.qty)

    shipments = {}
    for (shipment_name, shipment_item_name), quantity in quantity_by_shipment_item.items():
        shipment = shipments.setdefault(shipment_name, frappe.get_doc("Customer Shipment", shipment_name))
        shipment_item = next((item for item in shipment.items if item.sales_order_item == shipment_item_name), None)
        if not shipment_item:
            frappe.throw(
                _("Customer Shipment {0} does not contain Sales Order Item {1}.").format(
                    shipment_name, shipment_item_name
                )
            )
        updated_received_qty = flt(shipment_item.received_qty) + multiplier * quantity
        if updated_received_qty < 0 or updated_received_qty + flt(shipment_item.returned_qty) > flt(shipment_item.dispatched_qty):
            frappe.throw(_("Delivery Note quantity does not match the available transit quantity."))
        shipment_item.received_qty = updated_received_qty
        shipment_item.remaining_qty = (
            flt(shipment_item.dispatched_qty) - flt(shipment_item.received_qty) - flt(shipment_item.returned_qty)
        )

    for shipment in shipments.values():
        shipment.status = get_shipment_status(shipment.items)
        shipment.save(ignore_permissions=True)


def _get_shipment_name(sales_order_name: str) -> str:
    shipment_name = frappe.db.get_value(
        "Customer Shipment",
        {
            "sales_order": sales_order_name,
            "docstatus": 1,
            "status": ["in", ["Dispatched", "Partially Received", "Received"]],
        },
        order_by="modified desc",
    )
    if not shipment_name:
        frappe.throw(_("Sales Order {0} has no submitted transit transfer.").format(sales_order_name))
    return shipment_name


def _is_receipt_generated_delivery(delivery_note) -> bool:
    return "Created from Customer Shipment" in (delivery_note.remarks or "")
