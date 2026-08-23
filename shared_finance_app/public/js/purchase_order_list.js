frappe.listview_settings['Purchase Order'] = {
    onload: function (listview) {
        
        let style = document.createElement('style');
        style.innerHTML = `
            @media (max-width: 500px) {
                .frappe-list .list-row-container .indicator-pill,
                .frappe-list .list-row-container .indicator,
                .list-row-col .indicator-pill {
                    display: none !important;
                    opacity: 0 !important;
                    visibility: hidden !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
};