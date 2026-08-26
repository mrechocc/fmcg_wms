import frappe
from frappe import _
from frappe.utils import flt

from fmcg_wms.services.status import get_shipment_status


def get_pending_items(shipment_name: str) -> list[dict]:
    shipment = frappe.get_doc("Customer Shipment", shipment_name)
    if shipment.docstatus != 1:
        frappe.throw(_("Customer Shipment must be submitted before recording receipt."))

    return [
        {
            "customer_shipment_item": row.name,
            "sales_order_item": row.sales_order_item,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "uom": row.uom,
            "accepted_qty": flt(row.remaining_qty),
            "available_transit_qty": flt(row.remaining_qty),
        }
        for row in shipment.items
        if flt(row.remaining_qty) > 0
    ]


def populate_receipt_header(receipt) -> None:
    shipment = frappe.get_doc("Customer Shipment", receipt.customer_shipment)
    receipt.company = shipment.company
    receipt.customer = shipment.customer
    receipt.sales_order = shipment.sales_order


def validate_receipt(receipt) -> None:
    shipment = frappe.get_doc("Customer Shipment", receipt.customer_shipment)
    if shipment.docstatus != 1:
        frappe.throw(_("Customer Shipment must be submitted before recording receipt."))
    if shipment.status in {"Received", "Returned", "Closed", "Cancelled"}:
        frappe.throw(_("Customer Shipment {0} has no transit quantity available for receipt.").format(shipment.name))

    receipt.company = shipment.company
    receipt.customer = shipment.customer
    receipt.sales_order = shipment.sales_order
    shipment_rows = {row.name: row for row in shipment.items}
    seen = set()
    for row in receipt.items:
        shipment_row = shipment_rows.get(row.customer_shipment_item)
        if not shipment_row or row.customer_shipment_item in seen:
            frappe.throw(_("Each receipt item must reference one unique shipment item."))
        seen.add(row.customer_shipment_item)
        if row.item_code != shipment_row.item_code or row.uom != shipment_row.uom:
            frappe.throw(_("Receipt item must match its Customer Shipment Item."))
        if flt(row.accepted_qty) <= 0 or flt(row.accepted_qty) > flt(shipment_row.remaining_qty):
            frappe.throw(_("Accepted Qty must be greater than zero and no more than the transit quantity."))
        row.sales_order_item = shipment_row.sales_order_item
        row.available_transit_qty = shipment_row.remaining_qty


def _make_delivery_note(receipt, shipment):
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

    requested_by_so_item = {}
    for row in receipt.items:
        requested_by_so_item[row.sales_order_item] = flt(row.accepted_qty)

    delivery_note = make_delivery_note(shipment.sales_order)
    mapped_rows = []
    for row in delivery_note.items:
        requested_qty = requested_by_so_item.get(row.so_detail)
        if requested_qty is None:
            continue
        row.qty = requested_qty
        row.stock_qty = requested_qty * flt(row.conversion_factor or 1)
        row.warehouse = shipment.transit_warehouse
        mapped_rows.append(row)

    if len(mapped_rows) != len(requested_by_so_item):
        frappe.throw(_("Could not map every accepted item to a pending Sales Order item."))

    delivery_note.items = mapped_rows
    delivery_note.set_warehouse = shipment.transit_warehouse
    delivery_note.posting_date = receipt.receipt_date
    delivery_note.remarks = "\n".join(
        filter(
            None,
            [
                delivery_note.remarks,
                _("Created from Customer Shipment {0}, Receipt {1}.").format(shipment.name, receipt.name),
            ],
        )
    )
    delivery_note.run_method("set_missing_values")
    delivery_note.run_method("set_po_nos")
    delivery_note.run_method("calculate_taxes_and_totals")
    delivery_note.insert()
    delivery_note.submit()
    return delivery_note


def submit_receipt(receipt) -> None:
    validate_receipt(receipt)
    shipment = frappe.get_doc("Customer Shipment", receipt.customer_shipment)
    delivery_note = _make_delivery_note(receipt, shipment)
    receipt.db_set("delivery_note", delivery_note.name, update_modified=False)
    receipt.db_set("status", "Received", update_modified=False)
    _apply_receipt_to_shipment(shipment, receipt, multiplier=1)
    receipt.add_comment("Info", _("Created Delivery Note {0} from accepted transit quantity.").format(delivery_note.name))


def cancel_receipt(receipt) -> None:
    if receipt.delivery_note:
        delivery_note = frappe.get_doc("Delivery Note", receipt.delivery_note)
        if delivery_note.docstatus == 1:
            delivery_note.cancel()

    shipment = frappe.get_doc("Customer Shipment", receipt.customer_shipment)
    _apply_receipt_to_shipment(shipment, receipt, multiplier=-1)


def _apply_receipt_to_shipment(shipment, receipt, multiplier: int) -> None:
    shipment_rows = {row.name: row for row in shipment.items}
    for receipt_row in receipt.items:
        shipment_row = shipment_rows[receipt_row.customer_shipment_item]
        shipment_row.received_qty = flt(shipment_row.received_qty) + multiplier * flt(receipt_row.accepted_qty)
        shipment_row.remaining_qty = (
            flt(shipment_row.dispatched_qty)
            - flt(shipment_row.received_qty)
            - flt(shipment_row.returned_qty)
        )
    shipment.status = get_shipment_status(shipment.items)
    shipment.save()
