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
2. Submit a `Transit Delivery` order. The app automatically creates and submits
   a standard Stock Entry with purpose `Material Transfer`, moving stock from
   the central warehouse to the Transit warehouse. The Sales Order opens that
   Stock Entry directly after submission.
3. Find, filter, print, or export the transfer in `Stock > Stock Entry`. The
   Stock Entry includes read-only Sales Order, Customer, and expected receipt
   date fields for traceability.
4. When the customer accepts the goods, create a Delivery Note from the Sales
   Order. The app issues the stock from the Transit warehouse automatically.
5. For customer pickup, choose `Immediate Delivery` and use `Shipping > Confirm
   Immediate Delivery`; the Delivery Note issues directly from the central
   warehouse.
6. For a customer return before delivery, create a standard Material Transfer
   from the Transit warehouse back to the central warehouse.

## Reporting

Use the standard Stock Entry list for individual movements and its built-in
export action for CSV or XLSX. The `In Transit Inventory` report also uses
standard Stock Entry records and compares transferred, delivered, and remaining
quantities by Sales Order line.

## Acceptance Checks

1. A transit order creates one submitted Material Transfer and reduces the
   central warehouse by the transferred quantity.
2. The same quantity appears in the Transit warehouse.
3. A Delivery Note created from that order uses the Transit warehouse.
4. The In Transit Inventory report links every new row to a Stock Entry rather
   than a Customer Shipment.
