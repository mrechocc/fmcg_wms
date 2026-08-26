import frappe
from frappe import _


TRANSIT_DELIVERY_MODE = "\u5728\u9014\u4ea4\u4ed8"


def block_manual_transit_delivery(delivery_note) -> None:
    """Keep transit Sales Orders from bypassing the signed receipt workflow."""
    if getattr(delivery_note.flags, "fmcg_wms_transit_delivery", False):
        return

    sales_orders = {row.against_sales_order for row in delivery_note.items if row.against_sales_order}
    if not sales_orders:
        return

    transit_orders = frappe.get_all(
        "Sales Order",
        filters={"name": ["in", list(sales_orders)], "fmcg_delivery_mode": TRANSIT_DELIVERY_MODE},
        pluck="name",
    )
    if transit_orders:
        frappe.throw(
            _("Sales Order {0} is a transit delivery. Create a Customer Shipment Receipt after customer acceptance; "
              "the generated Delivery Note will issue stock from the transit warehouse.").format(
                ", ".join(transit_orders)
            )
        )
