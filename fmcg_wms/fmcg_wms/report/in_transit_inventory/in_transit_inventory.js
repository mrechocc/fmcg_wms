frappe.query_reports["In Transit Inventory"] = {
  filters: [
    { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company" },
    { fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
  ],
};
