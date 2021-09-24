odoo.define('superaia_salesrep_app.datatable_table', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.datatableJs = publicWidget.Widget.extend({
        selector: '#wrap',

        start: function () {
            if ($('#all-accounts-table').length) {
                $('#all-accounts-table').DataTable({
                    "ordering": true,
                    columnDefs: [{
                        orderable: false,
                        targets: "no-sort"
                    },
                    { width: "22%", targets: 0 },
                    { width: "5%", targets: "more-info" }
                ],
                    "dom": "<'tablelength'l><'tablebody't>S<'tableinfobar'i><'tablepaging'p>",
                });
            }
            return this._super.apply(this, arguments);
        },

    });
});