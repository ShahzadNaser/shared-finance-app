frappe.ui.form.on("Purchase Order", {
    refresh:function(frm){

		if (window.innerWidth <= 501) {   
			setTimeout(() => {
				let $btn = $('.page-head .sidebar-toggle-btn');
				
				if ($btn.length > 0) {
						// 1. Remove Frappe's native workspace toggle class
						$btn.removeClass('sidebar-toggle-btn').addClass('custom-mobile-btn');
						
						// 2. FIX: Hide the double-arrow and force the three-line menu to show
						$btn.find('.sidebar-toggle-icon').hide(); // Hides the >>
						$btn.find('.sidebar-toggle-placeholder').show(); // Shows the 3 lines
						
						// 3. Attach our smart toggle logic
						$('.custom-mobile-btn').off('click').on('click', function(e) {
						e.preventDefault();
						
						let $sideSection = $('.layout-side-section');
						let $formSidebar = $('.form-sidebar');
						let $htmlTag = $('html');
						
						// Toggle logic for the button itself
						if ($sideSection.hasClass('show')) {
							$sideSection.removeClass('show');
							$formSidebar.removeClass('opened').addClass('hidden-xs hidden-sm');
							$htmlTag.css('overflow-y', '');
							$(document).off('click.customSidebar'); 
						} else {
							// OPEN Sidebar
							$sideSection.addClass('show');
							$formSidebar.addClass('opened').removeClass('hidden-xs hidden-sm');
							$htmlTag.css('overflow-y', 'hidden'); 
							
							// Smart Closing Listener
							setTimeout(() => {
								$(document).on('click.customSidebar', function(event) {
									let $target = $(event.target);
									
									// Ignore clicks on our custom button
									if ($target.closest('.custom-mobile-btn').length > 0) return;
									
									// Check where the user clicked
									let clickedOutside = $target.closest('.layout-side-section').length === 0;
									let clickedAction = $target.closest('button, a, [data-action], .icon').length > 0;
									let isModal = $target.closest('.modal, .modal-dialog').length > 0;
									
									// If interacting with a popup (like the attachment upload), do NOT close
									if (isModal) return;
									
									// If clicked outside, or clicked an action button inside the sidebar -> Close
									if (clickedOutside || clickedAction) {
											$sideSection.removeClass('show');
											$formSidebar.removeClass('opened').addClass('hidden-xs hidden-sm');
											$htmlTag.css('overflow-y', '');
											
											$(document).off('click.customSidebar'); 
									}
								});
							}, 50);
						}
						});
				}
			}, 500);
		}

        let help_box = frm.get_field('custom_department_manager').$wrapper.find('.help-box');
        
		if (help_box.length) {
			// Appling color
			help_box[0].style.setProperty('color', '#2490EF', 'important');
			help_box[0].style.setProperty('font-weight', 'bold', 'important');
		}
        
        if(frm.doc.custom_department){
            frm.trigger("set_department_manager");
        }

        frm.set_query('custom_department', function() {
            return {
				filters: [
						['Department', 'name', '!=', 1],
						['Department', 'company', '=', frm.doc.company]
				]
			};
		});

		let current_state = frm.doc.workflow_state || '';

		if (frm.doc.custom_action_remarks && (current_state === 'Draft' || current_state.includes('Rejected'))) {
			frm.set_intro(frm.doc.custom_action_remarks, 'red');
		} else {
			frm.set_intro('');
		}
    },
	before_workflow_action: function(frm) {
		if (['Reject', 'Revise'].includes(frm.selected_workflow_action)) {
			return new Promise((resolve, reject) => {

				frappe.dom.unfreeze();

				frappe.prompt([
						{
						label: 'Remarks / Reason',
						fieldname: 'user_remarks',
						fieldtype: 'Text',
						reqd: 1,
						description: 'Please provide a reason for this action.'
						}
				],
				function(values) {
						frappe.dom.freeze('Saving Remarks...');

						let current_user = frappe.session.user_fullname;
						let action = frm.selected_workflow_action;
						
						let professional_sentence = `This document was <b>${action}</b> by <b>${current_user}</b>. <b>Remarks:</b> ${values.user_remarks}`;
						
						frappe.db.set_value(
							frm.doctype, 
							frm.docname, 
							'custom_action_remarks',
							professional_sentence
						).then(() => {
							resolve(); 
						}).catch(() => {
							frappe.dom.unfreeze();
							frappe.msgprint('Error saving remarks.');
							reject();
						});
				},
				'Mandatory Remarks For <b>' + frm.selected_workflow_action + ' Action</b>',
				'Submit'
				);
			});
		}
	},
    custom_department: function(frm) {
        frm.trigger("set_department_manager");
    },
    set_department_manager: function(frm) {
		if (frm.doc.custom_department) {
			return frappe.call({
				method: 'shared_finance_app.overrides_class.payment_request.get_department_manager',
				args: {
					"department": frm.doc.custom_department,
				},
				callback: function(r) {
					if (r && r.message) {
                        if (frm.doc.custom_department_manager !== r.message) {
						    frm.set_value('custom_department_manager', r.message);
                        }
					}
				}
			});
		}
	}
})