from erpnext.controllers import sales_and_purchase_return

_original_validate_quantity = sales_and_purchase_return.validate_quantity


def custom_validate_quantity(doc, key, d, ref, valid_items, already_returned_items):
    return


sales_and_purchase_return.validate_quantity = custom_validate_quantity
