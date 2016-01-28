var required_anchor =["fs"];
$(document).ready(function() {
	$('.search_form_help').each (function () {
		this.onclick = function () {
			var help_div;
			field_id = $(this).parent().parent().find(".search_form_field").find ("input").attr("id");
			help_div = null;
			help_div = $("div[help_id='" + field_id + "']");
			help_div.dialog ({
					open: function () {
							$(this).load ("../static/html/"+field_id+".html");
						}, 
					height: 300, 
					width: 400 });
			help_div = null;
			delete help_div;
	};
	});
	$('.search-form input').css ({'width':460, 'font-size':'13px' });
	$('.search-form label').css ({'width':120, 'font':'bold 12px verdana', 'color':'#404040'});
	
	// Tells the form to submit on enter
    $('.search-form input').keypress(function(event){
		// If we push the "enter" key
		if (event.keyCode == '13') {
			event.preventDefault();
			$('.search-form').submit(); // need to update that with this. Right now, if you have several forms with the
						// search-form class, it will pick one of them only. (or?) 
		   }
		});
    $("input:text:visible:first").focus();
	
});
