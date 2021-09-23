odoo.define('superaia_salesrep_app.datatable_table', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.datatableJs = publicWidget.Widget.extend({
        selector: '#wrap',

        start: function () {
            if ($('#example').length) {
                $('#example').DataTable();
            }
            return this._super.apply(this, arguments);
        },
    

    });
});