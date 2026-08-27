from types import SimpleNamespace

from fmcg_wms.fmcg_wms.report.in_transit_inventory.in_transit_inventory import (
    allocate_delivered_quantities,
)


def test_delivery_is_allocated_to_oldest_transit_transfer_first():
    entries = {
        "MAT-STE-0001": SimpleNamespace(posting_date="2026-08-01"),
        "MAT-STE-0002": SimpleNamespace(posting_date="2026-08-03"),
    }
    rows = [
        SimpleNamespace(parent="MAT-STE-0001", idx=1, qty=40, fmcg_sales_order_item="SOI-001"),
        SimpleNamespace(parent="MAT-STE-0002", idx=1, qty=60, fmcg_sales_order_item="SOI-001"),
    ]

    allocations = allocate_delivered_quantities(rows, entries, {"SOI-001": 55})

    assert allocations == {("MAT-STE-0001", 1): 40, ("MAT-STE-0002", 1): 15}
