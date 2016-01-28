var oTable = null;
var required_anchor =["fs"];
$(function() {			
		document.getElementById('radio4').checked=true;
		$('#set_button').buttonset('refresh');		 
		$("#build_table").find("td").mouseenter(function() { $(this).addClass('ui-state-hover');})
		$("#build_table").find("td").mouseleave(function() { $(this).removeClass("ui-state-hover");});
		//$("#build_table").find("tr").eq(0).addClass('ui-state-focus');
});
	
$(document).ready(function() {

	oTable = $('#build_table').dataTable({
		"bJQueryUI":false,
		"bLengthChange":true,
		"bPaginate":false,
		"bProcessing":true,
		"bFilter":true,
		"iDsiplayLength":50,
		"sScrollY":"620px",
//		"sScrollX":100px,
//		"bScrollCollapse": true,
		"aoColumnDefs":{"bVisible":true,
			"bSearchable":true},
		"sPaginationType": "full_numbers"

	});
	
	sc_node = oTable.fnGetNodes(0);
	$(sc_node.firstChild).addClass('ui-state-focus');
	sc_name = sc_node.firstChild.attributes.getNamedItem("scenario").value;
	funcSelect(sc_name);

	
	$("#build_table tbody").click(function(event) {
		$(oTable.fnSettings().aoData).each(function (){
			$(this.nTr.firstChild).removeClass('ui-state-focus');
		});
		$(event.target).addClass('ui-state-focus');
		scr_name = event.target.attributes.getNamedItem("scenario").value;
		funcSelect(scr_name);
	});
});


funcSelect = function(scr_name) {
	$("#select-result").empty();
	$("#select-result").html($("#loading_img").html());
	$.get("../api/graph_list", 
		{format:"html", scenario: scr_name }, 
		function(data){
		   $("#select-result").html (data);
		}
	);
	$("#loading_img").hide();
};
