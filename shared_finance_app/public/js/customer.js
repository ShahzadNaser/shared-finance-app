frappe.ui.form.on('Customer', {
    refresh:function(frm){

    },
    customer_group: function(frm){
           if(frm.doc.customer_group == "INDUSTRIAL" ){
            frm.set_value('enable_v_pay_formula_for_5_years_case_basic_salary_',1);
            frm.set_value('after_years',100);
            frm.set_value('enable_eosb_formula_for_5_years_case_basic_salary_',1);
            frm.set_value('after_year',100);

           }
           else{
               frm.set_value('enable_v_pay_formula_for_5_years_case_basic_salary_',0);
            frm.set_value('after_years',null);
            frm.set_value('enable_eosb_formula_for_5_years_case_basic_salary_',0);
            frm.set_value('after_year',null);


           }
            frm.refres_field("enable_v_pay_formula_for_5_years_case_basic_salary_");
            frm.refres_field("after_years");
            frm.refres_field("enable_eosb_formula_for_5_years_case_basic_salary_");
            frm.refres_field("after_year");
    },

})
