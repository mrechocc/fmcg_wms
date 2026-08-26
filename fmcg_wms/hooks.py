app_name = "fmcg_wms"
app_title = "快消品WMS系统"
app_publisher = "快消品WMS系统"
app_description = "FMCG warehouse management and in-transit inventory controls"
app_email = "ops@example.invalid"
app_license = "MIT"
app_version = "0.3.1"

doctype_js = {
    "Customer Shipment": "public/js/customer_shipment.js",
    "Customer Shipment Receipt": "public/js/customer_shipment_receipt.js",
    "Sales Order": "public/js/sales_order.js",
}

doc_events = {
    "Sales Order": {
        "on_submit": "fmcg_wms.events.sales_order.auto_dispatch_transit_order",
    },
    "Delivery Note": {
        "validate": "fmcg_wms.events.delivery_note.apply_transit_warehouse",
        "on_submit": "fmcg_wms.events.delivery_note.sync_transit_shipment_on_submit",
        "on_cancel": "fmcg_wms.events.delivery_note.sync_transit_shipment_on_cancel",
    }
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
                    "Sales Order-fmcg_customer_shipment",
                ],
            ]
        ],
    }
]
