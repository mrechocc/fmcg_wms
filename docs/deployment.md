# Deployment and Operating Guide

## Scope

This app uses ERPNext's standard Sales Order, Stock Entry (Material Transfer),
and Delivery Note documents. It does not add an operational shipment module.
Legacy Customer Shipment records are retained only for historical access.

## Prerequisites

1. ERPNext and Frappe must use the same major branch. This app targets v16.
2. Create exactly one active, non-group Warehouse with type `Transit` for each
   company using this workflow.
3. Set the Company's Default Warehouse to the central warehouse. If it is not
   set, the app can use the only active non-Transit warehouse in the company.
4. Users need permission to create and submit Stock Entry and Delivery Note.
5. Before using External ERP Import, map external customer, item, and warehouse
   codes in their `fmcg_external_*_code` fields. Mark shortage or large-account
   customers as `Transit Delivery`; ordinary customers should remain `Immediate Delivery`.

## Installation or Upgrade

Run as the Bench user, not `root`.

```bash
cd ~/erpnext-bench/apps/fmcg_wms
git pull upstream main

cd ~/erpnext-bench
bench --site your-site-name migrate
bench build --app fmcg_wms
bench restart
```

## Daily Workflow

1. Create the Sales Order and choose `Transit Delivery` or `Immediate Delivery`.
2. Submit a `Transit Delivery` order. The app creates a draft standard Stock
   Entry with purpose `Material Transfer` and opens it. This draft does not
   change stock.
3. The warehouse changes each line to this dispatch's actual quantity, removes
   unavailable lines, then uses `Shipping > Approve and Submit`. Only submission
   moves stock from the central warehouse to the Transit warehouse. Create a
   further draft transfer from the Sales Order whenever more stock is ready.
4. Find, filter, print, or export all transfers in `Stock > Stock Entry`. Each
   entry includes read-only Sales Order, Customer, and expected receipt date
   fields for traceability.
5. When goods are ready for the customer, use `Shipping > Create This Delivery
   Note` on the Sales Order. The draft Delivery Note contains only the
   approved-but-not-yet-delivered quantity for each order line, and issues from
   the Transit warehouse automatically. The user may reduce the quantity before
   submitting it.
   The standard Sales Order `Create` menu hides non-WMS actions; Sales Invoice
   remains available to finance users.
6. For customer pickup, choose `Immediate Delivery` and use `Shipping > Confirm
   Immediate Delivery`; the Delivery Note issues directly from the central
   warehouse.
7. For a customer return before delivery, create a standard Material Transfer
   from the Transit warehouse back to the central warehouse.

## External ERP Excel Import

1. Log in as a user with the `System Manager` role and open `External ERP Import`.
2. For first-time setup, choose `Customer Master Data` and attach the external customer
   export. Customer Group and Territory are assigned automatically, preferring the
   existing `个人` and `中国` records. Active rows whose type contains Customer,
   including Customer/Supplier, are created. No receivable, prepayment, or other
   financial balance is imported.
3. Choose `Item Master Data`, attach the external item export, and select the target
   Item Group and Sales UOM (normally `件`). ERPNext applies its configured Item
   naming rule; the external item code is stored only as the unique matching key. A
   packaging value such as `1箱=6瓶`, `1箱=24罐`, `1箱=12个`, or `1箱=2组` sets
   the stock UOM to `瓶`, `罐`, `个`, or `组` and creates the `件` conversion
   factor. No opening stock,
   warehouse quantity, or cost is imported. The special `FREIGHT` item is created as
   a non-stock item.
4. Use `Preview and Validate` first for each master-data file, then run the import.
   Correct all errors before importing Sales Orders and Delivery Notes.
5. Select the company, choose `Sales Order` or `Delivery Note`, and attach the
   matching external ERP Excel export.
6. Use `Preview and Validate` first. The import stops before creating documents
   when a customer, item, warehouse, external order, Sales Order Item, or transit
   quantity cannot be matched.
7. Import all outstanding external Sales Orders before importing Delivery Notes.
   A delivery sheet can refer to orders created before its export date.
8. Leave `Submit Documents After Validation` unchecked for the first run. Review
   the generated drafts and mapping results. Enabling it submits documents only
   after the whole file passes validation.
9. Uploading the same file again skips documents with an existing external order
   number or external delivery number. Negative delivery quantities are reported
   as exceptions and must use a return process.

## Reporting

Use the standard Stock Entry list for individual movements and its built-in
export action for CSV or XLSX. The `In Transit Inventory` report also uses
standard Stock Entry records and compares transferred, delivered, and remaining
quantities by Sales Order line.

## Acceptance Checks

1. A transit order creates one draft Material Transfer and does not change
   stock before approval.
2. A warehouse-approved transfer reduces the central warehouse and increases
   the Transit warehouse by its actual quantity.
3. A further draft can be created for the remaining quantity of the same Sales
   Order.
4. A transit Delivery Note contains only the approved-but-not-yet-delivered
   quantity, uses the Transit warehouse, and cannot exceed that quantity when
   submitted.
5. The In Transit Inventory report allocates delivered quantity across multiple
   transfers in chronological order.
