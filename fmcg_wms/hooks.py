app_name = "fmcg_wms"
app_title = "快消品WMS系统"
app_publisher = "快消品WMS系统"
app_description = "FMCG warehouse management and in-transit inventory controls"
app_email = "ops@example.invalid"
app_license = "MIT"
app_version = "0.2.0"

doctype_js = {
    "Customer Shipment": "public/js/customer_shipment.js",
    "Customer Shipment Receipt": "public/js/customer_shipment_receipt.js",
    "Sales Order": "public/js/sales_order.js",
}

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["name", "in", ["Sales Order-fmcg_customer_shipment"]]],
    }
]
