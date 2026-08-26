app_name = "fmcg_wms"
app_title = "\u5feb\u6d88\u54c1WMS\u7cfb\u7edf"
app_publisher = "\u5feb\u6d88\u54c1WMS\u7cfb\u7edf"
app_description = "FMCG warehouse management and in-transit inventory controls"
app_email = "ops@example.invalid"
app_license = "MIT"
app_version = "0.4.0"

doctype_js = {"Sales Order": "public/js/sales_order.js"}

doc_events = {
    "Sales Order": {
        "on_submit": "fmcg_wms.events.sales_order.auto_dispatch_transit_order",
    },
    "Delivery Note": {
        "validate": "fmcg_wms.events.delivery_note.apply_transit_warehouse",
    },
}

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Sales Order-fmcg_delivery_section",
                    "Sales Order-fmcg_delivery_mode",
                    "Sales Order-fmcg_transit_warehouse",
                    "Sales Order-fmcg_expected_receipt_date",
                    "Sales Order-fmcg_transit_stock_entry",
                    "Sales Order-fmcg_customer_shipment",
                    "Stock Entry-fmcg_transit_section",
                    "Stock Entry-fmcg_sales_order",
                    "Stock Entry-fmcg_customer",
                    "Stock Entry-fmcg_expected_receipt_date",
                    "Stock Entry Detail-fmcg_sales_order_item",
                ],
            ]
        ],
    }
]
