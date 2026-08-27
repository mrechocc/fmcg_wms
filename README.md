# FMCG WMS

`fmcg_wms` is an ERPNext custom app for commercial businesses that need to
separate dispatch from customer receipt while keeping central warehouse stock
accurate.

Version 0.5 uses ERPNext's existing documents for the operating workflow:

- Sales Order selects `Immediate Delivery` or `Transit Delivery`.
- A submitted Transit Delivery Sales Order automatically creates a draft
  Stock Entry Material Transfer. The warehouse enters the actual quantity and
  submits it only after approving the dispatch; a Sales Order can have several
  approved transfers.
- A Delivery Note created from that Sales Order issues from the Transit
  warehouse and cannot exceed the approved transit quantity.
- Customer pickup creates a Delivery Note directly from the central warehouse.

The app does not modify ERPNext core files. Legacy Customer Shipment records
remain available only for historical review; new daily operations use Stock
Entry and Delivery Note.

See [docs/deployment.md](docs/deployment.md) for installation and daily use.
See [docs/ai_handover.md](docs/ai_handover.md) for the Chinese maintenance handover.
