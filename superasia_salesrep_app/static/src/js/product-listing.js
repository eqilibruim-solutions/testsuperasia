odoo.define('superaia_salesrep_app.sales_rep_product_list', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');

    
    publicWidget.registry.imageModalPopup = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click .img-pop': '_imgModalPopUp',
        },

        _imgModalPopUp: function (ev) {
            ev.preventDefault()
            $('.imagepreview').attr('src', $(ev.currentTarget).find('img').attr('src'));
            $('#imagemodal').modal('show'); 
        }


    });

    publicWidget.registry.salesRepShopHeader = publicWidget.Widget.extend({
        selector: '.sale_rep_product_list #function_top_menu',
        events:{
            'change form.js_attributes input, form.js_attributes select': '_onChangeAttributeApp',
         },
         _onChangeAttributeApp: function (ev) {
            if (!ev.isDefaultPrevented()) {
                ev.preventDefault();
                $(ev.currentTarget).closest("form").submit();
            }
          },
        });
    
    publicWidget.registry.salesRepProductCategory = publicWidget.Widget.extend({
        selector: '.sale_rep_product_list',
        events: {
            'change select#product-category': '_onChangeProductCategory',
            },
            _onChangeProductCategory: function (ev) {
                let categoryUrl = $(ev.currentTarget).val();
                window.location.href = categoryUrl;
            },
        });
});


// TODO: create separate file for below code
odoo.define('superasia_salesrep_app.cart', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var VariantMixin = require('sale.VariantMixin');
    var wSaleUtils = require('website_sale.utils');
    var websiteSale = require('website_sale.website_sale');
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
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            let discountPrice = parseFloat($input.val() || 0, 10);
            var $unitPrice = $dom.find("input[name='unit_price']");
            var $productQty = $dom.find("input.quantity");
            var line_id = parseInt($productQty.data('line-id'), 10);
            var product_id = parseInt($productQty.data('product-id'), 10);
            var productIDs = [parseInt($productQty.data('product-id'), 10)];
            var qty = parseInt($productQty.val())
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
                //     $productQty.on('finished', function() {

                //         console.log("clicked the input");
                //         debugger;
                //         $.when(websiteSale._changeCartQuantity($productQty, qty, $dom_optional, line_id, productIDs)).done(function () {
                //             $.unblockUI();
                //           });
                        
                //    });

                //     $productQty.trigger('finished');
                //     // $.when($productQty.trigger('change')).done(function(){
                //     //     $.unblockUI();
                //     // });
                //     // this._changeCartQuantity($productQty, value, $dom_optional, line_id, productIDs);
                    wSaleUtils.updateCartNavBar(data);
                    $.unblockUI();

                });
            }
        },


    });
    
});