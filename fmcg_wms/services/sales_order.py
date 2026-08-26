import frappe
from frappe import _
from frappe.utils import flt, nowdate

from fmcg_wms.services.delivery import create_delivery_note_from_sales_order
from fmcg_wms.services.stock import make_material_transfer

IMMEDIATE_DELIVERY_MODE = "\u5f53\u573a\u4ea4\u4ed8"
TRANSIT_DELIVERY_MODE = "\u5728\u9014\u4ea4\u4ed8"


def get_default_source_warehouse(company: str) -> str | None:
    """Resolve the company's operational warehouse without ever selecting transit stock."""
    company_meta = frappe.get_meta("Company")
    if company_meta.has_field("default_warehouse"):
        default_warehouse = frappe.db.get_value("Company", company, "default_warehouse")
        if default_warehouse:
            warehouse_type, is_group = frappe.db.get_value(
                "Warehouse", default_warehouse, ["warehouse_type", "is_group"]
            ) or (None, None)
            if warehouse_type != "Transit" and not is_group:
                return default_warehouse

    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "is_group": 0},
        fields=["name", "warehouse_type"],
        order_by="name asc",
    )
    operational_warehouses = [warehouse.name for warehouse in warehouses if warehouse.warehouse_type != "Transit"]
    return operational_warehouses[0] if len(operational_warehouses) == 1 else None


def create_transit_transfer(sales_order_name: str, ignore_permissions: bool = False):
    """Create one standard Stock Entry that moves the order to the transit warehouse."""
    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    sales_order.check_permission("read")
    if sales_order.docstatus != 1:
        frappe.throw(_("Only a submitted Sales Order can create a transit transfer."))

    _require_delivery_mode(sales_order, TRANSIT_DELIVERY_MODE)
    transit_warehouse = get_default_transit_warehouse(sales_order.company)
    _ensure_no_active_transit_transfer(sales_order)
    lines = get_dispatch_lines(sales_order)
    if not lines:
        frappe.throw(_("Sales Order {0} has no quantity available for transit dispatch.").format(sales_order.name))

    entry = make_material_transfer(
        company=sales_order.company,
        source_warehouse=lines[0]["source_warehouse"],
        target_warehouse=transit_warehouse,
        lines=lines,
        posting_date=nowdate(),
        sales_order=sales_order.name,
        customer=sales_order.customer,
        expected_receipt_date=sales_order.delivery_date,
        remarks=_("Transit transfer created automatically from Sales Order {0}.").format(sales_order.name),
        ignore_permissions=ignore_permissions,
    )

    if sales_order.meta.has_field("fmcg_transit_warehouse"):
        sales_order.db_set("fmcg_transit_warehouse", transit_warehouse, update_modified=False)
    if sales_order.meta.has_field("fmcg_transit_stock_entry"):
        sales_order.db_set("fmcg_transit_stock_entry", entry.name, update_modified=False)
    sales_order.add_comment(
        "Info",
        _("Created transit Stock Entry {0}.").format(entry.name),
    )
    return entry


def create_immediate_delivery(sales_order_name: str, posting_date=None):
    """Deliver all currently undelivered order quantities from their source warehouses."""
    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    sales_order.check_permission("read")
    if sales_order.docstatus != 1:
        frappe.throw(_("Only a submitted Sales Order can be delivered."))
    _require_delivery_mode(sales_order, IMMEDIATE_DELIVERY_MODE)
    _require_immediate_delivery_permissions()
    lines = get_dispatch_lines(sales_order)
    if not lines:
        frappe.throw(_("Sales Order {0} has no quantity available for delivery.").format(sales_order.name))

    quantities_by_so_item = {line["sales_order_item"]: line["dispatched_qty"] for line in lines}
    warehouses_by_so_item = {line["sales_order_item"]: line["source_warehouse"] for line in lines}
    delivery_note = create_delivery_note_from_sales_order(
        sales_order.name,
        quantities_by_so_item,
        warehouses_by_so_item,
        posting_date or nowdate(),
        _("Immediate customer pickup delivery created from Sales Order {0}.").format(sales_order.name),
    )
    sales_order.add_comment("Info", _("Created immediate pickup Delivery Note {0}.").format(delivery_note.name))
    return delivery_note


def get_dispatch_lines(sales_order) -> list[dict]:
    lines = []
    for row in sales_order.items:
        pending_qty = flt(row.qty) - flt(row.delivered_qty)
        if pending_qty <= 0:
            continue
        source_warehouse = row.warehouse or sales_order.set_warehouse or get_default_source_warehouse(sales_order.company)
        if not source_warehouse:
            frappe.throw(
                _("Sales Order Item {0} needs a source warehouse before creating a transit transfer.").format(
                    row.idx
                )
            )
        lines.append(
            {
                "sales_order_item": row.name,
                "item_code": row.item_code,
                "uom": row.uom,
                "conversion_factor": row.conversion_factor or 1,
                "source_warehouse": source_warehouse,
                "dispatched_qty": pending_qty,
            }
        )
    return lines


def get_default_transit_warehouse(company: str) -> str:
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "warehouse_type": "Transit", "is_group": 0},
        pluck="name",
        order_by="name asc",
        limit_page_length=2,
    )
    if len(warehouses) == 1:
        return warehouses[0]
    if not warehouses:
        frappe.throw(_("Company {0} needs one non-group Warehouse with type Transit.").format(company))
    frappe.throw(
        _("Company {0} has multiple Transit Warehouses. Keep one active transit warehouse or add a company setting.").format(
            company
        )
    )


def _require_delivery_mode(sales_order, expected_mode: str) -> None:
    if not sales_order.meta.has_field("fmcg_delivery_mode"):
        frappe.throw(_("Run bench migrate to add the FMCG delivery fields to Sales Order."))
    if sales_order.fmcg_delivery_mode != expected_mode:
        frappe.throw(_("Select delivery mode {0} on the Sales Order before continuing.").format(expected_mode))


def _ensure_no_active_transit_transfer(sales_order) -> None:
    stock_entry_name = sales_order.get("fmcg_transit_stock_entry")
    if stock_entry_name and frappe.db.get_value("Stock Entry", stock_entry_name, "docstatus") == 1:
        frappe.throw(
            _("Sales Order {0} already has submitted transit Stock Entry {1}.").format(
                sales_order.name, stock_entry_name
            )
        )

    # Orders created before this upgrade may still point at a legacy shipment.
    shipment_name = sales_order.get("fmcg_customer_shipment")
    if shipment_name and frappe.db.get_value("Customer Shipment", shipment_name, "docstatus") == 1:
        frappe.throw(
            _("Sales Order {0} already has a legacy transit shipment {1}.").format(
                sales_order.name, shipment_name
            )
        )


def _require_immediate_delivery_permissions() -> None:
    if not frappe.has_permission("Delivery Note", "create") or not frappe.has_permission("Delivery Note", "submit"):
        frappe.throw(_("Immediate delivery requires Delivery Note create and submit permission."))
