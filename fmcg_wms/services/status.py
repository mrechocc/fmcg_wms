from frappe.utils import flt


def get_shipment_status(items) -> str:
    """Calculate the operational status from submitted stock movements."""
    dispatched = sum(flt(row.dispatched_qty) for row in items)
    received = sum(flt(row.received_qty) for row in items)
    returned = sum(flt(row.returned_qty) for row in items)

    if not dispatched:
        return "Draft"
    if received + returned < dispatched:
        return "Partially Received" if received or returned else "Dispatched"
    if returned and not received:
        return "Returned"
    if received and not returned:
        return "Received"
    return "Closed"
