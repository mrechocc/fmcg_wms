# Deployment and Operating Guide

## 1. Scope and accounting assumption

This app assumes the company retains control of goods until the customer
accepts them. Dispatch moves value between two company warehouses; only a
submitted Customer Shipment Receipt creates an ERPNext Delivery Note and its
normal stock/accounting impact. Confirm the contractual revenue-recognition
policy with finance before production use.

## 2. Prerequisites

1. ERPNext and Frappe must use the same major branch. This app is written for
   ERPNext v16 interfaces.
2. Create a Warehouse with warehouse type `Transit`, for example `In Transit -
   Company`. It must belong to the same company as the source warehouse.
3. Ensure Stock Users who dispatch can create and submit `Stock Entry`; users
   who confirm receipt also need permission to create and submit `Delivery Note`.
4. The first release rejects Sales Order rows with standard stock reservations.
   Unreserve them before dispatch. Reservation migration can be added as a
   separate enhancement after the operating flow is accepted.

## 3. Installation

Run on the ERPNext server as the Bench user. Do not copy files into the
`apps/erpnext` directory.

```bash
cd ~/frappe/erpnext-bench
bench get-app /path/to/fmcg_wms
bench --site your-site-name install-app fmcg_wms
bench --site your-site-name migrate
bench build --app fmcg_wms
bench restart
```

## 4. Daily workflow

1. Create a Customer Shipment from one submitted Sales Order.
2. Select the physical source warehouse and the company transit warehouse.
3. Enter only the quantity loaded onto the vehicle, then save and select
   `Actions > Confirm Dispatch`. The app creates a submitted Material Transfer.
4. When the customer signs, create a Customer Shipment Receipt, load pending
   transit items, enter the signed quantity, attach the proof of delivery, and
   submit. The app creates a Delivery Note from the transit warehouse.
5. For refused or returned goods, use `Return All Remaining` on the shipment.
   The generated Stock Entry is the audit record for the return.

## 5. Cutover

Do not delete or mass-cancel historical Delivery Notes. Choose a cutover date,
list physically unreceived shipments, count the corresponding goods, and have
finance approve the opening transit value. Use a controlled Stock
Reconciliation in a test site first, then reconcile the transit warehouse,
Stock Ledger, and General Ledger after production cutover.

## 6. Acceptance checks

1. Dispatch reduces only the source warehouse and increases the transit
   warehouse by the same quantity and value.
2. A partial receipt reduces transit only by the signed quantity and creates a
   Delivery Note with the same quantity.
3. Cancelling a receipt cancels its Delivery Note and restores transit quantity.
4. Returning remaining goods removes them from transit and increases the
   selected return warehouse.
5. The `In Transit Inventory` report agrees with the transit warehouse balance.
