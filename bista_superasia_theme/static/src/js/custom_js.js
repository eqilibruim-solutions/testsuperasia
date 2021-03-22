odoo.define('bista_superasia_theme.recent_product', function (require) {
"use strict";
var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;

ajax.loadXML('/bista_superasia_theme/static/src/xml/website_sale_recent_product_inherit.xml', qweb);
})
var a = 0;
$(window).scroll(function() {

  if($('.counter-value').length){
  var oTop = $('#counter').offset().top - window.innerHeight;
  if (a == 0 && $(window).scrollTop() > oTop) {
    $('.counter-value').each(function() {
      var $this = $(this),
        countTo = $this.attr('data-count');
      $({
        countNum: $this.text()
      }).animate({
          countNum: countTo
        },

        {

          duration: 7000,
          easing: 'swing',
          step: function() {
            $this.text(Math.floor(this.countNum));
          },
          complete: function() {
            $this.text(this.countNum);
          }

        });
    });
    a = 1;
  }
  }

});


$(document).ready(function(){

$(".top_search").change(function(){
  if ($(this).val()){
   var redirect_link = '/shop/product/'
   redirect_link  += $(this).val()
   window.location.href = redirect_link

  }})

$(".top_search").select2({
        theme:"bootstrap",
        allowClear: true,
        formatResult: function (opt) {
        var opt_text = opt.text;
        var opt_thumb_image = $(opt.element).attr('src');
        var $res = opt_thumb_image ? $('<span><img src="' + opt_thumb_image + '" width="33px" /> ' + opt.text + '</span>') : opt_text;
        return $res;
},});



if ($('.typing').length){


var typed = new Typed(".typing", {
    strings: ["Hello.!!!","Welcome to SuperAsia Food."],
    typeSpeed: 100,
    backSpeed: 60,
    loop: false,
  });
  console.log(":::::::::::::::::::::v::::::::",typed)
// setTimeout(function () {
//           $('.catalogue_btn').removeClass('d-none');
//          }, 10000);
}



      $('[data-toggle="tooltip"]').tooltip();
    });

    $(document).ready(function(){
        $(".hover-flag-dropdown").hover(function(){
            var dropdownMenu = $(this).children(".dropdown-menu-toggle");
            if(dropdownMenu.is(":visible")){
                dropdownMenu.parent().toggleClass("open");
            }
        });
    });



$(document).ready(function(){

  var $clientcarousel = $('#clients-list');
  var clients = $clientcarousel.children().length;
  var clientwidth = (clients * 220); // 140px width for each client item
  $clientcarousel.css('width',clientwidth);

  var rotating = true;
  var clientspeed = 0;
  var seeclients = setInterval(rotateClients, clientspeed);

  $(document).on({
    mouseenter: function(){
      rotating = false; // turn off rotation when hovering
    },
    mouseleave: function(){
      rotating = true;
    }
  }, '#clients');

  function rotateClients() {
    if(rotating != false) {
      var $first = $('#clients-list li:first');
      $first.animate({ 'margin-left': '-220px' }, 2000, "linear", function() {
        $first.remove().css({ 'margin-left': '0px' });
        $('#clients-list li:last').after($first);
      });
    }
  }


    });



    $('#recipeCarousel').carousel({
      interval :50000
    });

    $('.carousel .carousel-item').each(function(){
        var next = $(this).next();
        if (!next.length) {
        next = $(this).siblings(':first');
        }
        next.children(':first-child').clone().appendTo($(this));

        for (var i=0;i<1;i++) {
            next=next.next();
            if (!next.length) {
              next = $(this).siblings(':first');
            }

            next.children(':first-child').clone().appendTo($(this));
          }
    });
