import frappe
from frappe import _
from frappe.utils import flt


def get_material_transfer_type() -> str:
    stock_entry_type = frappe.db.get_value(
        "Stock Entry Type", {"purpose": "Material Transfer"}, "name"
    )
    if not stock_entry_type:
        frappe.throw(_("A Stock Entry Type with purpose Material Transfer is required."))
    return stock_entry_type


def add_traceability_fields(target, source) -> None:
    """Copy only fields available in the installed ERPNext stock entry schema."""
    stock_entry_meta = frappe.get_meta("Stock Entry Detail")
    for fieldname in ("batch_no", "serial_no", "serial_and_batch_bundle"):
        if stock_entry_meta.has_field(fieldname) and source.get(fieldname):
            target[fieldname] = source.get(fieldname)


def make_material_transfer(
    *, company, source_warehouse, target_warehouse, lines, posting_date, remarks, ignore_permissions: bool = False
):
    if source_warehouse == target_warehouse:
        frappe.throw(_("Source Warehouse and Transit Warehouse must be different."))

    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = get_material_transfer_type()
    entry.purpose = "Material Transfer"
    entry.company = company
    entry.from_warehouse = source_warehouse
    entry.to_warehouse = target_warehouse
    entry.posting_date = posting_date
    entry.remarks = remarks

    for line in lines:
        qty = flt(line.get("qty") or line.get("dispatched_qty"))
        if qty <= 0:
            frappe.throw(_("Transferred quantity must be greater than zero."))

        item = {
            "item_code": line.item_code,
            "qty": qty,
            "uom": line.uom,
            "conversion_factor": line.get("conversion_factor") or 1,
            "s_warehouse": line.get("source_warehouse") or source_warehouse,
            "t_warehouse": target_warehouse,
        }
        add_traceability_fields(item, line)
        entry.append("items", item)

    entry.flags.ignore_permissions = ignore_permissions
    entry.insert(ignore_permissions=ignore_permissions)
    entry.submit()
    return entry
