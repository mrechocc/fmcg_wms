from fmcg_wms.services.sales_order import TRANSIT_DELIVERY_MODE, create_transit_transfer


def create_draft_transit_transfer(sales_order) -> None:
    if sales_order.fmcg_delivery_mode == TRANSIT_DELIVERY_MODE:
        create_transit_transfer(sales_order.name, ignore_permissions=True)
