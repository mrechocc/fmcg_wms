import frappe

from fmcg_wms.services.external_erp import preview_import, run_import


@frappe.whitelist()
def preview(file_url: str, import_type: str, company: str, submit_documents=None):
    return preview_import(file_url, import_type, company)


@frappe.whitelist()
def run(file_url: str, import_type: str, company: str, submit_documents: int | bool = False):
    return run_import(file_url, import_type, company, bool(int(submit_documents)))
