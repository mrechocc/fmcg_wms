from types import SimpleNamespace

from fmcg_wms.services.sales_order import get_dispatch_lines


def test_dispatch_lines_use_item_warehouse_before_order_default():
    sales_order = SimpleNamespace(
        set_warehouse="Center Warehouse",
        items=[
            SimpleNamespace(
                name="SOI-001",
                idx=1,
                item_code="ITEM-001",
                qty=4,
                delivered_qty=1,
                warehouse="Row Warehouse",
                uom="Nos",
                conversion_factor=1,
            ),
            SimpleNamespace(
                name="SOI-002",
                idx=2,
                item_code="ITEM-002",
                qty=2,
                delivered_qty=0,
                warehouse=None,
                uom="Nos",
                conversion_factor=1,
            ),
        ],
    )

    lines = get_dispatch_lines(sales_order)

    assert [line["source_warehouse"] for line in lines] == ["Row Warehouse", "Center Warehouse"]
    assert [line["dispatched_qty"] for line in lines] == [3, 2]
