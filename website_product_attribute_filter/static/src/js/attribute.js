odoo.define('website_product_attribute_filter.attribute', function (require) {
    "use strict";
		$(document).on('change','.mt-checkbox input[name="attrib"]',function(event){
        if (!event.isDefaultPrevented()) {
                event.preventDefault();
                $(this).closest("form").submit();
            }
		});

        $(document).on('change','.mt-checkbox input[name="category_attrib"]',function(event){
        if (!event.isDefaultPrevented()) {
                event.preventDefault();
                $(this).closest("form").find("input[name='category_remove']").val(0);
                $(this).closest("form").submit();
            }
        });
        
})
