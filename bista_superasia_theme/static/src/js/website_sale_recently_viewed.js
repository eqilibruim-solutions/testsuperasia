odoo.define('bista_superasia_theme.recently_viewed_ept', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var wSaleUtils = require('website_sale.utils');
    var session = require('web.session');
    var config = require('web.config');

    publicWidget.registry.productsRecentlyViewedSnippet.include({
        
        /**
         * @override
         * Hide carousal footer(product price and Add to cart) for guest user
         */
        _addCarousel: function () {
            var carousel = config.device.size_class <= config.device.SIZES.SM ? this.mobileCarousel : this.webCarousel;
            if(!session.user_id) {
                carousel.find(".o_carousel_product_card_footer").remove();
            }
            this.$('.slider').html(carousel).css('display', ''); // TODO removing the style is useless in master
        },
        /**
         @override
         Reload the page after adding product.
         So that data-max value update after reload.
        **/
         _onAddToCart: function (ev){
            var self = this;
            var $card = $(ev.currentTarget).closest('.card');
            this._rpc({
                route: "/shop/cart/update_json",
                params: {
                    product_id: $card.find('input[data-product-id]').data('product-id'),
                    add_qty: 1
                },
            }).then(function (data) {
                wSaleUtils.updateCartNavBar(data);
                window.location.reload();
                // var $navButton = wSaleUtils.getNavBarButton('.o_wsale_my_cart');
                // var fetch = self._fetch();
                // var animation = wSaleUtils.animateClone($navButton, $(ev.currentTarget).parents('.o_carousel_product_card'), 25, 40);
                // Promise.all([fetch, animation]).then(function (values) {
                //     self._render(values[0]);
                // });
            });
        },
    });
});
