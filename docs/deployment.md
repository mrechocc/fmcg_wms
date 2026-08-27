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
5. When the customer accepts the goods, create a Delivery Note from the Sales
   Order. It issues from the Transit warehouse automatically and cannot exceed
   the approved-but-not-yet-delivered quantity for that Sales Order line.
6. For customer pickup, choose `Immediate Delivery` and use `Shipping > Confirm
   Immediate Delivery`; the Delivery Note issues directly from the central
   warehouse.
7. For a customer return before delivery, create a standard Material Transfer
   from the Transit warehouse back to the central warehouse.

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
4. A Delivery Note uses the Transit warehouse and cannot exceed the total
   approved quantity for each Sales Order line.
5. The In Transit Inventory report allocates delivered quantity across multiple
   transfers in chronological order.
