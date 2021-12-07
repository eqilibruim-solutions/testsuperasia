odoo.define('superasia_salesrep_app.cart_extension', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var VariantMixin = require('sale.VariantMixin');
    var wSaleUtils = require('website_sale.utils');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';

    publicWidget.registry.SalesRepWebsiteSale = publicWidget.Widget.extend(VariantMixin, {
        selector: '.oe_website_sale',
        events: _.extend({}, VariantMixin.events || {}, {
            'change .oe_cart input.price_after_disc': '_onChangePriceAfterDisc',
        }),
    
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this._onChangePriceAfterDisc = _.debounce(this._onChangePriceAfterDisc.bind(this), 500);

            this.isWebsite = true;
        },

        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            return def;
        },

        _onChangePriceAfterDisc: function (ev) {
            var $input = $(ev.currentTarget);
            var $dom = $input.closest('tr');
            let discountPrice = parseFloat($input.val() || 0, 10);
            var $unitPrice = $dom.find("input[name='unit_price']");
            var $productQty = $dom.find("input.quantity");
            var line_id = parseInt($productQty.data('line-id'), 10);
            var product_id = parseInt($productQty.data('product-id'), 10);

            if ($unitPrice.length) {
                let unitPrice = parseFloat($unitPrice.val());
                let discountAmount = parseFloat((unitPrice-discountPrice)*100/unitPrice);
                let msg = "Updating ...";
                $.blockUI({
                    'message': '<h2 class="text-white">' +
                        '<img alt="spinner" src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                        '<br />' + msg + '</h2>'
                });
                this._rpc({
                    route: "/sales-rep/cart/update_discount",
                    params: {
                        line_id: line_id,
                        product_id: product_id,
                        set_discount: discountAmount
                    },
                }).then(function (data) {
                    if (!('done' in data)) {
                        console.log("Discount not updated");
                    }
                    wSaleUtils.updateCartNavBar(data);
                    $.unblockUI();

                });
            }
        },

    });
    
});