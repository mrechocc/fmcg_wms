import frappe

from fmcg_wms.services.external_erp import preview_import, run_import


@frappe.whitelist()
def preview(
    file_url: str,
    import_type: str,
    company: str,
    submit_documents=None,
    customer_group=None,
    territory=None,
    item_group=None,
    sales_uom=None,
):
    return preview_import(file_url, import_type, company, customer_group, territory, item_group, sales_uom)


@frappe.whitelist()
def run(
    file_url: str,
    import_type: str,
    company: str,
    submit_documents: int | bool = False,
    customer_group=None,
    territory=None,
    item_group=None,
    sales_uom=None,
):
    return run_import(
        file_url,
        import_type,
        company,
        bool(int(submit_documents)),
        customer_group,
        territory,
        item_group,
        sales_uom,
    )
