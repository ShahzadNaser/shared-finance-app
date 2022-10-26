



import frappe

def execute():


    frappe.db.sql(""" INSERT INTO `tabProperty Setter`
                    (`default_value`,`doc_type`,`docstatus`,`doctype_or_field`,`field_name`,`modified`,`creation`,`name`,`property`,`property_type`,`value`)
                    VALUES
                    (0,'Payment Request',0,'DocField','currency','2022-10-16 14:38:31.442080','2022-10-16 14:38:31.442080','Payment Request-currencyccc-read_only','read_only','Check',0);
                    """)

    frappe.db.commit()