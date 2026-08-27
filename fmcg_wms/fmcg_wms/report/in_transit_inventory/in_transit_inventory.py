import frappe
from frappe import _
from frappe.utils import date_diff, flt, nowdate


def execute(filters=None):
    filters = filters or {}
    columns = [
        {"label": _("Material Movement"), "fieldname": "stock_entry", "fieldtype": "Link", "options": "Stock Entry", "width": 160},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 170},
        {"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"label": _("Transfer Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
        {"label": _("Transit Days"), "fieldname": "transit_days", "fieldtype": "Int", "width": 100},
        {"label": _("Expected Receipt"), "fieldname": "expected_receipt_date", "fieldtype": "Date", "width": 115},
        {"label": _("Source Warehouse"), "fieldname": "source_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 170},
        {"label": _("Transit Warehouse"), "fieldname": "transit_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 170},
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Transferred Qty"), "fieldname": "transferred_qty", "fieldtype": "Float", "width": 115},
        {"label": _("Delivered Qty"), "fieldname": "delivered_qty", "fieldtype": "Float", "width": 105},
        {"label": _("In Transit Qty"), "fieldname": "remaining_qty", "fieldtype": "Float", "width": 110},
    ]

    entry_filters = {"docstatus": 1, "purpose": "Material Transfer", "fmcg_sales_order": ["is", "set"]}
    if filters.get("company"):
        entry_filters["company"] = filters.company
    if filters.get("customer"):
        entry_filters["fmcg_customer"] = filters.customer

    entries = frappe.get_all(
        "Stock Entry",
        filters=entry_filters,
        fields=["name", "fmcg_sales_order", "fmcg_customer", "posting_date", "fmcg_expected_receipt_date"],
        order_by="posting_date asc, name asc",
    )
    entry_by_name = {entry.name: entry for entry in entries}
    entry_names = list(entry_by_name)
    if not entry_names:
        return columns, []

    transfer_rows = frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": ["in", entry_names], "parenttype": "Stock Entry"},
        fields=["parent", "idx", "item_code", "uom", "qty", "s_warehouse", "t_warehouse", "fmcg_sales_order_item"],
        order_by="parent asc, idx asc",
        limit_page_length=0,
    )
    delivered_quantities = _get_delivered_quantities([row.fmcg_sales_order_item for row in transfer_rows])
    delivered_by_transfer_row = allocate_delivered_quantities(transfer_rows, entry_by_name, delivered_quantities)

    data = []
    for item in transfer_rows:
        entry = entry_by_name[item.parent]
        delivered_qty = delivered_by_transfer_row.get((item.parent, item.idx), 0)
        remaining_qty = max(flt(item.qty) - delivered_qty, 0)
        data.append(
            {
                "stock_entry": entry.name,
                "status": _("Delivered") if remaining_qty == 0 else _("In Transit"),
                "customer": entry.fmcg_customer,
                "sales_order": entry.fmcg_sales_order,
                "posting_date": entry.posting_date,
                "transit_days": date_diff(nowdate(), entry.posting_date),
                "expected_receipt_date": entry.fmcg_expected_receipt_date,
                "source_warehouse": item.s_warehouse,
                "transit_warehouse": item.t_warehouse,
                "item_code": item.item_code,
                "uom": item.uom,
                "transferred_qty": flt(item.qty),
                "delivered_qty": delivered_qty,
                "remaining_qty": remaining_qty,
            }
        )
    return columns, data


def _get_delivered_quantities(sales_order_items: list[str]) -> dict[str, float]:
    sales_order_items = list({name for name in sales_order_items if name})
    if not sales_order_items:
        return {}
    rows = frappe.db.sql(
        """
        SELECT item.so_detail, COALESCE(SUM(item.qty), 0) AS delivered_qty
        FROM `tabDelivery Note Item` AS item
        INNER JOIN `tabDelivery Note` AS delivery_note ON delivery_note.name = item.parent
        WHERE delivery_note.docstatus = 1
          AND item.so_detail IN %(sales_order_items)s
        GROUP BY item.so_detail
        """,
        {"sales_order_items": tuple(sales_order_items)},
        as_dict=True,
    )
    return {row.so_detail: flt(row.delivered_qty) for row in rows}


def allocate_delivered_quantities(transfer_rows, entry_by_name, delivered_quantities: dict[str, float]) -> dict[tuple, float]:
    """Allocate each order line's signed quantity to its oldest approved transfer first."""
    rows_by_order_item = {}
    for row in transfer_rows:
        if row.fmcg_sales_order_item:
            rows_by_order_item.setdefault(row.fmcg_sales_order_item, []).append(row)

    allocations = {}
    for sales_order_item, rows in rows_by_order_item.items():
        remaining_delivery_qty = flt(delivered_quantities.get(sales_order_item))
        rows.sort(key=lambda row: (entry_by_name[row.parent].posting_date, row.parent, row.idx))
        for row in rows:
            allocated_qty = min(flt(row.qty), remaining_delivery_qty)
            allocations[(row.parent, row.idx)] = allocated_qty
            remaining_delivery_qty -= allocated_qty
    return allocations
