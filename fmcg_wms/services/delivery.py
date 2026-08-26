import frappe
from frappe import _
from frappe.utils import flt


def create_delivery_note_from_sales_order(
    sales_order_name: str,
    quantities_by_so_item: dict[str, float],
    warehouses_by_so_item: dict[str, str],
    posting_date,
    remarks: str,
    allow_transit_delivery: bool = False,
):
    """Create one submitted Delivery Note from selected Sales Order quantities."""
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

    delivery_note = make_delivery_note(sales_order_name)
    mapped_rows = []
    for row in delivery_note.items:
        requested_qty = quantities_by_so_item.get(row.so_detail)
        if requested_qty is None:
            continue
        warehouse = warehouses_by_so_item.get(row.so_detail)
        if not warehouse:
            frappe.throw(_("Could not find a source warehouse for Sales Order Item {0}.").format(row.so_detail))
        row.qty = requested_qty
        row.stock_qty = requested_qty * flt(row.conversion_factor or 1)
        row.warehouse = warehouse
        mapped_rows.append(row)

    if len(mapped_rows) != len(quantities_by_so_item):
        frappe.throw(_("Could not map every requested item to a pending Sales Order item."))

    delivery_note.items = mapped_rows
    delivery_note.set_warehouse = mapped_rows[0].warehouse
    delivery_note.posting_date = posting_date
    delivery_note.remarks = "\n".join(filter(None, [delivery_note.remarks, remarks]))
    delivery_note.flags.fmcg_wms_transit_delivery = allow_transit_delivery
    delivery_note.run_method("set_missing_values")
    delivery_note.run_method("set_po_nos")
    delivery_note.run_method("calculate_taxes_and_totals")
    delivery_note.insert()
    delivery_note.submit()
    return delivery_note
