function scenario_fix(){
							
	$('.cell[f_actual!="None"]') // all cells that have f_actual as not None
		.css ({'font-style': 'italic', "text-align": "right"}) // move them italic
		.each (function (n, elt) {                     // then put the float value in the html place
			$(this).html($(this).attr("f_actual"));
		})
		.filter('[f_actual$=".0"]')         // if the value ends with .0 (ie float that is an int)
		.each (function(n, elt){
			$(this).html($(this).html().replace(".0", ""));  // remove the .0 at the end
	});
}

$(document).ready(function() {
	decorate_pagination_buttons($('#base-table').find( "#top_pagination"));
	decorate_pagination_buttons($('#base-table').find( "#bottom_pagination"));

	document.getElementById('radio2').checked=true;
	$('#set_button').buttonset('refresh');
	scenario_fix();
});