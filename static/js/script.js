// preloader
$(window).on("load", function () {
    $("#preloader").fadeOut();
});

$(document).ready(function () {
    $(".dropdown-trigger").dropdown(); // navbar dropdown
    $(".sidenav").sidenav({edge: "right"}); // mobile sidenav
    $("select").formSelect(); // select dropdowns
    $(".modal").modal(); // modals
    $(".tabs").tabs(); // tabs
    $('.tooltipped').tooltip(); // tooltip

    // custom flash messages
    function flashToast() {
        $("#flashToast").addClass("show");
        setTimeout(function () {
            $("#flashToast").removeClass("show");
        }, 4000);
    }
    flashToast();

    // check for valid image to display on entry
    $("input#cover.validate").blur(function () {
        // add image tag, with fallback option for no-image.png default image
        $("#img_new").empty().prepend(`<img class="small-img" src="${$(this).val()}" onError="this.onerror=null;this.src='../../../static/images/no_img.png';">`);
    });

    // update "active" sub-navbar link
    if (window.location.pathname.indexOf("/category/artwork") > -1) {
        $(".subnav").removeClass("active");
        $("#artwork-nav").addClass("active");
    } else if (window.location.pathname.indexOf("/category/books") > -1) {
        $(".subnav").removeClass("active");
        $("#book-nav").addClass("active");
    } else if (window.location.pathname.indexOf("/category/movies") > -1) {
        $(".subnav").removeClass("active");
        $("#movie-nav").addClass("active");
    } else if (window.location.pathname.indexOf("/category/music") > -1) {
        $(".subnav").removeClass("active");
        $("#music-nav").addClass("active");
    } else if (window.location.pathname.indexOf("/category/podcasts") > -1) {
        $(".subnav").removeClass("active");
        $("#podcast-nav").addClass("active");
    }

    // passwords must match
    $("#register").attr("disabled", true);
    let password = "";
    let passwordConfirm = "";
    $("#password").on("keyup", function() {
        password = $(this).val();
    });
    $("#password-confirm").on("keyup focusout", function() {
        passwordConfirm = $(this).val();
        if (passwordConfirm != password) {
            // passwords do not match
            $("#password-confirm").removeClass("valid");
            $("#password-confirm").addClass("invalid");
        } else {
            // password match
            $("#password-confirm").removeClass("invalid");
        }
    });
    $("#username, #password, #password-confirm").on("keyup focusout", function() {
        if ($("#username").hasClass("valid") && $("#password").hasClass("valid") && $("#password-confirm").hasClass("valid")) {
            // all fields are valid
            $("#register").attr("disabled", false);
        } else {
            // one or more fields are invalid
            $("#register").attr("disabled", true);
        }
    });

    // custom code for Materialize select dropdown validation
    validateMaterializeSelect();
    function validateMaterializeSelect() {
        let classValid = { "border-bottom": "1px solid #4caf50", "box-shadow": "0 1px 0 0 #4caf50" };
        let classInvalid = { "border-bottom": "1px solid #f44336", "box-shadow": "0 1px 0 0 #f44336" };
        if ($("select.validate").prop("required")) {
            $("select.validate").css({ "display": "block", "height": "0", "padding": "0", "width": "0", "position": "absolute" });
        }
        $(".select-wrapper input.select-dropdown").on("focusin", function () {
            $(this).parent(".select-wrapper").on("change", function () {
                if ($(this).children("ul").children("li.selected:not(.disabled)").on("click", function () { })) {
                    $(this).children("input").css(classValid);
                }
            });
        }).on("click", function () {
            if ($(this).parent(".select-wrapper").children("ul").children("li.selected:not(.disabled)").css("background-color") === "rgba(0, 0, 0, 0.03)") {
                $(this).parent(".select-wrapper").children("input").css(classValid);
            } else {
                $(".select-wrapper input.select-dropdown").on("focusout", function () {
                    if ($(this).parent(".select-wrapper").children("select").prop("required")) {
                        if ($(this).css("border-bottom") != "1px solid rgb(76, 175, 80)") {
                            $(this).parent(".select-wrapper").children("input").css(classInvalid);
                        }
                    }
                });
            }
        });
    }
});
