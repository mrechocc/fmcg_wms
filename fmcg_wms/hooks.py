app_name = "fmcg_wms"
app_title = "\u5feb\u6d88\u54c1WMS\u7cfb\u7edf"
app_publisher = "\u5feb\u6d88\u54c1WMS\u7cfb\u7edf"
app_description = "FMCG warehouse management and in-transit inventory controls"
app_email = "ops@example.invalid"
app_license = "MIT"
app_version = "0.5.3"

app_include_css = "/assets/fmcg_wms/css/sales_order_list.css"

doctype_js = {
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Stock Entry": "public/js/stock_entry.js",
    "External ERP Import": "public/js/external_erp_import.js",
}

doctype_list_js = {"Sales Order": "public/js/sales_order_list.js"}

doc_events = {
    "Sales Order": {
        "on_submit": "fmcg_wms.events.sales_order.create_draft_transit_transfer",
    },
    "Delivery Note": {
        "validate": "fmcg_wms.events.delivery_note.apply_transit_warehouse",
        "before_submit": "fmcg_wms.events.delivery_note.validate_transit_delivery_before_submit",
    },
    "Stock Entry": {
        "before_submit": "fmcg_wms.events.stock_entry.validate_transit_transfer_before_submit",
        "on_submit": "fmcg_wms.events.stock_entry.record_transit_transfer_submission",
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
                    "Customer-fmcg_default_delivery_mode",
                    "Customer-fmcg_external_customer_code",
                    "Item-fmcg_external_item_code",
                    "Warehouse-fmcg_external_warehouse_code",
                    "Sales Order-fmcg_external_order_no",
                    "Sales Order Item-fmcg_external_line_key",
                    "Delivery Note-fmcg_external_delivery_no",
                    "Delivery Note Item-fmcg_external_line_key",
                ],
            ]
        ],
    }
]
