import frappe

def after_migrate():


    frappe.db.sql(""" delete from `tabProperty Setter` where name='Payment Request-currencyccc-read_only';
                     INSERT INTO `tabProperty Setter`
                    (`default_value`,`doc_type`,`docstatus`,`doctype_or_field`,`field_name`,`modified`,`creation`,`name`,`property`,`property_type`,`value`)
                    VALUES
                    (0,'Payment Request',0,'DocField','currency','2022-10-16 14:38:31.442080','2022-10-16 14:38:31.442080','Payment Request-currencyccc-read_only','read_only','Check',0);
                    """)

    frappe.db.sql(""" delete from `tabProperty Setter` where name='Journal Entry-read_only';
                        INSERT INTO `tabProperty Setter`
                       (`default_value`,`doc_type`,`docstatus`,`doctype_or_field`,`field_name`,`modified`,`creation`,`name`,`property`,`property_type`,`value`)
                       VALUES
                       (0,'Journal Entry',0,'DocField','finance_book','2022-10-16 14:38:31.442080','2022-10-16 14:38:31.442080','Journal Entry-read_only','read_only','Check',0);
                       """)




    frappe.db.commit()



