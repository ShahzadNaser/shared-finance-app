import frappe
from frappe import _, msgprint
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder

class CustomPurchaseOrder(PurchaseOrder):
    def before_save(self):
        # 1. Prepare field_a and field_b
        field_a = f"{self.grand_total:,.2f} SAR" if self.grand_total else ""
        field_b = self.supplier_name if self.supplier_name else ""
        
        # 2. Construct the fresh title based on current form values
        raw_title = f"{field_a} - {field_b}".strip(" - ")
        new_title = raw_title[:139] # Safe truncation for Data field (140 max)
        
        # Update if custom_title is empty OR if the current values don't match the existing title
        if not self.custom_titlee or not self.custom_titlee.strip() or self.custom_titlee != new_title:
            self.custom_titlee = new_title