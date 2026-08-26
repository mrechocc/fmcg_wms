import frappe
from frappe import _
from frappe.utils import flt, nowdate

from fmcg_wms.services.status import get_shipment_status
from fmcg_wms.services.stock import make_material_transfer


def validate_shipment(shipment, validate_reservation: bool = False) -> None:
    if shipment.source_warehouse == shipment.transit_warehouse:
        frappe.throw(_("Default Source Warehouse and Transit Warehouse must be different."))

    sales_order = frappe.get_doc("Sales Order", shipment.sales_order)
    if sales_order.company != shipment.company or sales_order.customer != shipment.customer:
        frappe.throw(_("The Sales Order must belong to the selected Company and Customer."))

    sales_order_items = {row.name: row for row in sales_order.items}
    shipment_qty_by_so_item = {}
    for row in shipment.items:
        sales_order_item = sales_order_items.get(row.sales_order_item)
        if not sales_order_item:
            frappe.throw(_("Row {0}: Sales Order Item does not belong to {1}.").format(row.idx, sales_order.name))
        if row.item_code != sales_order_item.item_code:
            frappe.throw(_("Row {0}: Item must match the linked Sales Order Item.").format(row.idx))
        if row.uom != sales_order_item.uom:
            frappe.throw(
                _("Row {0}: UOM {1} must match Sales Order UOM {2}.").format(
                    row.idx, row.uom, sales_order_item.uom
                )
            )
        if flt(row.dispatched_qty) <= 0:
            frappe.throw(_("Row {0}: Dispatched Qty must be greater than zero.").format(row.idx))
        shipment_qty_by_so_item[row.sales_order_item] = (
            shipment_qty_by_so_item.get(row.sales_order_item, 0) + flt(row.dispatched_qty)
        )
        if validate_reservation and flt(sales_order_item.stock_reserved_qty):
            frappe.throw(
                _("Row {0}: unreserve Sales Order stock before dispatching it to transit.").format(row.idx)
            )

    active_transit_qty = _get_active_transit_qty(shipment_qty_by_so_item)
    for sales_order_item_name, shipment_qty in shipment_qty_by_so_item.items():
        sales_order_item = sales_order_items[sales_order_item_name]
        remaining_sales_qty = flt(sales_order_item.qty) - flt(sales_order_item.delivered_qty)
        if shipment_qty + active_transit_qty.get(sales_order_item_name, 0) > remaining_sales_qty:
            frappe.throw(
                _("Dispatched Qty for Sales Order Item {0} exceeds its remaining quantity after active transit shipments.").format(
                    sales_order_item_name
                )
            )


def _get_active_transit_qty(sales_order_item_qty: dict) -> dict:
    if not sales_order_item_qty:
        return {}
    rows = frappe.db.sql(
        """
        SELECT shipment_item.sales_order_item, SUM(shipment_item.dispatched_qty) AS qty
        FROM `tabCustomer Shipment Item` AS shipment_item
        INNER JOIN `tabCustomer Shipment` AS shipment ON shipment.name = shipment_item.parent
        WHERE shipment_item.sales_order_item IN %(sales_order_items)s
          AND shipment.docstatus = 1
          AND shipment.status IN ('Dispatched', 'Partially Received')
        GROUP BY shipment_item.sales_order_item
        """,
        {"sales_order_items": tuple(sales_order_item_qty)},
        as_dict=True,
    )
    return {row.sales_order_item: flt(row.qty) for row in rows}


def dispatch(shipment_name: str):
    shipment = frappe.get_doc("Customer Shipment", shipment_name)
    shipment.check_permission("submit")
    if shipment.docstatus != 0:
        frappe.throw(_("Only a draft Customer Shipment can be dispatched."))

    validate_shipment(shipment, validate_reservation=True)
    entry = make_material_transfer(
        company=shipment.company,
        source_warehouse=shipment.source_warehouse,
        target_warehouse=shipment.transit_warehouse,
        lines=shipment.items,
        posting_date=shipment.dispatch_date or nowdate(),
        remarks=_("Dispatch to transit for Customer Shipment {0}").format(shipment.name),
    )
    shipment.stock_entry = entry.name
    shipment.status = "Dispatched"
    for row in shipment.items:
        row.received_qty = 0
        row.returned_qty = 0
        row.remaining_qty = flt(row.dispatched_qty)
    shipment.submit()
    shipment.add_comment("Info", _("Dispatched to transit through Stock Entry {0}.").format(entry.name))
    return shipment


def return_from_transit(shipment_name: str, target_warehouse: str, quantities: list[dict], reason: str):
    shipment = frappe.get_doc("Customer Shipment", shipment_name)
    shipment.check_permission("write")
    if shipment.docstatus != 1:
        frappe.throw(_("Only a submitted Customer Shipment can be returned from transit."))
    if target_warehouse == shipment.transit_warehouse:
        frappe.throw(_("Return Warehouse must be different from Transit Warehouse."))

    rows_by_name = {row.name: row for row in shipment.items}
    lines = []
    requested_qty_by_row = {}
    for request in quantities:
        row = rows_by_name.get(request.get("customer_shipment_item"))
        qty = flt(request.get("qty"))
        if not row or qty <= 0:
            frappe.throw(_("Each return row must identify a shipment item and positive quantity."))
        requested_qty_by_row[row.name] = requested_qty_by_row.get(row.name, 0) + qty
        if requested_qty_by_row[row.name] > flt(row.remaining_qty):
            frappe.throw(_("Return Qty cannot exceed the remaining transit quantity."))
        lines.append(
            frappe._dict(
                {
                    "item_code": row.item_code,
                    "qty": qty,
                    "uom": row.uom,
                    "conversion_factor": row.conversion_factor,
                    "batch_no": row.batch_no,
                    "serial_no": row.serial_no,
                    "serial_and_batch_bundle": row.serial_and_batch_bundle,
                    "source_warehouse": shipment.transit_warehouse,
                    "shipment_row": row,
                }
            )
        )

    entry = make_material_transfer(
        company=shipment.company,
        source_warehouse=shipment.transit_warehouse,
        target_warehouse=target_warehouse,
        lines=lines,
        posting_date=nowdate(),
        remarks=_("Return from transit for Customer Shipment {0}: {1}").format(shipment.name, reason),
    )
    for line in lines:
        row = line.shipment_row
        row.returned_qty = flt(row.returned_qty) + flt(line.qty)
        row.remaining_qty = flt(row.dispatched_qty) - flt(row.received_qty) - flt(row.returned_qty)
    shipment.status = get_shipment_status(shipment.items)
    shipment.save()
    shipment.add_comment("Info", _("Returned from transit through Stock Entry {0}: {1}").format(entry.name, reason))
    return entry


def cancel_shipment(shipment) -> None:
    if frappe.db.exists("Customer Shipment Receipt", {"customer_shipment": shipment.name, "docstatus": 1}):
        frappe.throw(_("Cancel submitted Customer Shipment Receipts before cancelling this shipment."))
    if shipment.stock_entry:
        entry = frappe.get_doc("Stock Entry", shipment.stock_entry)
        if entry.docstatus == 1:
            entry.cancel()
