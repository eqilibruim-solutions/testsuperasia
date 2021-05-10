odoo.define('bista_superasia_theme.binary_file_limit', function (require) {
"use strict";
var basic_fields = require('web.basic_fields');

basic_fields.AbstractFieldBinary.include({

    init: function (parent, name, record) {
        this._super.apply(this, arguments);
        this.fields = record.fields;
        this.useFileAPI = !!window.FileReader;
        this.max_upload_size = 50 * 1024 * 1024; // 50Mb
        if (!this.useFileAPI) {
            var self = this;
            this.fileupload_id = _.uniqueId('o_fileupload');
            $(window).on(this.fileupload_id, function () {
                var args = [].slice.call(arguments).slice(1);
                self.on_file_uploaded.apply(self, args);
            });
        }
    },
})

});

