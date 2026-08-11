import frappe
from frappe import _, msgprint
from frappe.utils import flt

from erpnext.stock.doctype.material_request.material_request import MaterialRequest

class CustomMaterialRequest(MaterialRequest):
    def before_save(self):
        if hasattr(super(), "before_save"):
            super().before_save()

        total = sum([flt(item.amount) for item in self.get("items")])
        total_qty = sum([flt(item.qty) for item in self.get("items")])

        self.custom_total_quantity = total_qty
        self.custom_total_amount = total
        
        # 1. Prepare field_a and field_b
        field_a = f"{total:,.2f} SAR"
        item_names = ", ".join([str(d.item_name) for d in self.get("items") if d.item_name][:3])
        field_b = _("{0} Request for {1}").format(_(self.material_request_type), item_names)[:100]
        
        # 2. Construct the fresh title based on current form values
        raw_title = f"{field_a} - {field_b}"
        new_title = raw_title[:139] # Safe truncation for Data field (140 max)
        
        # Update if custom_title is empty OR if the current values don't match the existing title
        if not self.custom_titlee or not self.custom_titlee.strip() or self.custom_titlee != new_title:
            self.custom_titlee = new_title

		#Reject/Revise action block from list view
        is_list_view_action = frappe.form_dict.get('cmd') == 'frappe.model.workflow.bulk_workflow_approval'

        current_state = self.workflow_state or ''

        if is_list_view_action and (current_state == 'Draft' or 'Rejected' in current_state) and self.has_value_changed('workflow_state'):
            frappe.throw("<b>Action Blocked:</b> You cannot Reject or Revise directly from the List View. Please click on the document to open it, then take your action so you can provide mandatory remarks.<br>")
    