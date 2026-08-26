# 快消品WMS系统

`fmcg_wms` is an ERPNext custom app for commercial businesses that need to
separate vehicle dispatch from customer receipt. It moves goods from an
operational warehouse to a company-owned transit warehouse at dispatch, then
creates the Sales Delivery Note only for customer-confirmed quantities.

The app intentionally does not patch ERPNext core files. All stock and sales
transactions are created through standard ERPNext documents.

See [docs/deployment.md](docs/deployment.md) for installation, configuration,
cutover, and acceptance checks.
