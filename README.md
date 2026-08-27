# FMCG WMS

`fmcg_wms` is an ERPNext custom app for commercial businesses that need to
separate dispatch from customer receipt while keeping central warehouse stock
accurate.

Version 0.5.6 uses ERPNext's existing documents for the operating workflow:

- Sales Order selects `Immediate Delivery` or `Transit Delivery`.
- A submitted Transit Delivery Sales Order automatically creates a draft
  Stock Entry Material Transfer. The warehouse enters the actual quantity and
  submits it only after approving the dispatch; a Sales Order can have several
  approved transfers.
- The transit Delivery Note is created as a draft with only the approved,
  undelivered quantity. It issues from the Transit warehouse and cannot exceed
  that quantity when submitted.
- Customer pickup creates a Delivery Note directly from the central warehouse.
- Customer master data selects the default delivery mode. Immediate customers issue from the
  source warehouse, while transit customers continue through approved transfers.
- `External ERP Import` first imports Customer and Item master data without stock balances, then validates Excel exports before importing Sales Orders or Delivery Notes.
  It maps external customer, item, warehouse, order, and delivery identifiers, and defaults to
  draft documents so stock is never posted without an explicit choice.

The app does not modify ERPNext core files. Legacy Customer Shipment records
remain available only for historical review; new daily operations use Stock
Entry and Delivery Note.

See [docs/deployment.md](docs/deployment.md) for installation and daily use.
See [docs/ai_handover.md](docs/ai_handover.md) for the Chinese maintenance handover.
