import frappe
from frappe import _, msgprint
from erpnext.stock.doctype.material_request.material_request import MaterialRequest

class CustomMaterialRequest(MaterialRequest):
    def before_save(self):
        super().before_save()

        total = 0.0
        total_qty = 0.0
        for item in self.items:
            total_qty += item.qty
            total += item.amount

        self.custom_total_quantity = total_qty
        self.custom_total = total

        # 1. Prepare field_a and field_b
        field_a = f"{self.custom_total:,.2f} SAR" if self.custom_total else ""
        items = ", ".join([d.item_name for d in self.items][:3])
        field_b = _("{0} Request for {1}").format(_(self.material_request_type), items)[:100]
        
        # 2. Construct the fresh title based on current form values
        raw_title = f"{field_a} - {field_b}".strip(" - ")
        new_title = raw_title[:139] # Safe truncation for Data field (140 max)
        
        # Update if custom_title is empty OR if the current values don't match the existing title
        if not self.custom_titlee or not self.custom_titlee.strip() or self.custom_titlee != new_title:
            self.custom_titlee = new_title