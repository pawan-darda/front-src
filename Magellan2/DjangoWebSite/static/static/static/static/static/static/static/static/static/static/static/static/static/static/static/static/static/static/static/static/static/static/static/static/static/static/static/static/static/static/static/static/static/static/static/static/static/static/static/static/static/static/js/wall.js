var wTable = null;
var required_anchor =["fs"];

function create_portlet_url(){	
	var url = '';

	var portlet_args = $(this).find("input.portlet-data:first").attr("pargs");
	var portlet_type = $(this).find("input.portlet-data:first").attr("ptype");
	var urlargs = jQuery.parseJSON($(this).find("input.portlet-data:first").attr("pargs"));
	if (portlet_type == "asg_scenario") {
		url = '../magellan2/version?qv=' + urlargs['nicename'] +'#tab=0?set=' + urlargs['set'];
	}
	if (portlet_type == "perf_graph") {
		var label_selected = urlargs['pg_label'].replace (/ /g, "+");
		url = '../magellan2/graph?&qv=' + urlargs['pg_nicename'] + '&qs=name:"'+ urlargs['pg_scenario']+'"&ql=name:"'+label_selected+'"&qc=name:"'+urlargs['pg_column']+'"'        
	}
	if (portlet_type == "scenario_unittest") {
		url = '../magellan2/version?qv=' + urlargs['nicename'] + '#tab=1'
	}
	if (portlet_type == "unittest_grid_widget"){
		url = '../magellan2/version?qv=' + urlargs['nicename'] + '#tab=1'
	}
	return url ;
}

function style_portlet(){
	$(this).find( ".portlet-header" )
	$(this).addClass( "ui-widget ui-widget-content ui-helper-clearfix ui-corner-all" )
	.find( ".portlet-header" )
    .addClass( "ui-widget-error ui-corner-top" )
    
    var portlet_type = $(this).find("input.portlet-data:first").attr("ptype");
    if (portlet_type != "build_status"){
    	var url = create_portlet_url.call(this);
		$(this).find( ".portlet-header" )
		.prepend( "<a href=" + url + " title='Expand' class='left ui-icon ui-icon-extlink'></a>")
	}
    $(this).find( ".portlet-header" ).prepend( "<span class='ui-icon ui-icon-minusthick'></span>")
	.prepend("<span title='Edit' class='ui-icon ui-icon-wrench'></span>")
	.prepend("<span title='Delete' class='ui-icon ui-icon-closethick'></span>")
	.end()
}

function portlet_minimize(){
	$(this).click(function() {
		$( this ).toggleClass( "ui-icon-minusthick" ).toggleClass( "ui-icon-plusthick" );
		$( this ).parents( ".portlet:first" ).find( ".portlet-content-wrapper" ).toggle();
	});
};

function portlet_delete(){
	$(this).click(function() {
		if(confirm("Are you sure you want to delete this portlet")){
			var portlet_id = $(this).parents(".portlet:first").find("input.portlet-data:first").attr("portletid");
			function delete_success(response){
				this.parents(".portlet:first").remove();
			};
			$.ajax({
				url: "../portlets/delete_portlet",
				data: {"portlet_id": portlet_id},
				success: delete_success,
				context: $(this)
			});
		}
	});                          
}

function portlet_edit(){
	$(this).click(function() {
		var urlargs = jQuery.parseJSON($(this).parents(".portlet:first").find("input.portlet-data:first").attr('pargs'));
		var portlet_type = $(this).parents(".portlet:first").find("input.portlet-data:first").attr("ptype");
		var portlet_title = $(this).parents(".portlet:first").find("input.portlet-data:first").attr("ptitle")
		var editportlet = $("#add-portlet table[ptype='" + portlet_type + "']");
		$("#tabs li[href='#" + editportlet.attr('id') + "']").addClass('ui-selected').siblings().removeClass('ui-selected');
		editportlet.removeClass('hidden').siblings().addClass('hidden').find("input").attr("disabled", true);

		editportlet.find("input,textarea").removeAttr("disabled").each(function(){

			if ( $(this).attr("type")== "checkbox" ){
				if ( $(urlargs).attr($(this).attr('name')) == "true" ) { $(this).attr('checked', true) }
				else { $(this).attr('checked', false) }
			}
			else {
				$(this).val($(urlargs).attr($(this).attr('name')));            
			}
		})

		$("#widget-header").val(portlet_title)
		$( "#tabs" ).selectable("disable");
		$("#edit-portlet").show().attr("portletid", $(this).parents(".portlet:first").find("input.portlet-data:first").attr('portletid')).children().show();
		$("#create-portlet").hide().children().hide();
		$("#add-portlet").dialog("option", "title", "Edit Widget").dialog('open')
	});
}

function expand_onclick (){
	/*
	 * Add click event to body of a portlet to open expan view for the portlet
	*/
	this.click( function(event){
		event.stopPropagation();
		window.location.href = create_portlet_url.call($(this).parent(".portlet")) ; 
	})
}

function init_portlet(el){
	// apply styling and minimize and close buttons to portlet
	style_portlet.call(el);
	portlet_minimize.call(el.find('.portlet-header .ui-icon-minusthick'));
	portlet_delete.call(el.find('.portlet-header .ui-icon-closethick'));
	portlet_edit.call(el.find('.portlet-header .ui-icon-wrench'));
	portlet_type = el.find("input.portlet-data:first").attr("ptype");
	if (portlet_type != "build_status"){
		var content = el.find(".portlet-content-wrapper");
		expand_onclick.call(content);
		content.attr("title", "Click to expand")
		content.css("cursor", "pointer")
	}
}

function get_portlet_data(){
	var portletdiv = $(this) 
	//portletdiv.find('.portlet-content').effect( "fade", {}, 500);
	var portletdata = portletdiv.find('.portlet-data')
	var urlargs = jQuery.parseJSON(portletdata.attr('pargs'))
	var url = "../portlets/" + portletdata.attr('ptype') + "?" 
	for(key in urlargs) {
		if (url.substr(-1)=='?')        
			url += key + "=" + urlargs[key]
		else     
			url += "&" + key + "=" + urlargs[key]
	}

	$(this).find('.portlet-content').empty();
	$(this).find('.portlet-content').html("Loading ...");

	$.ajax({ 
		url : url,
		data : {},
		async : true,
		context: portletdiv,
		success : function(response,status){
			$response = $(response)
			if($response.hasClass('scenario_error') || $response.find('.unittest_crashed').len){
				$(this).addClass('red_border');
			}
			$(this).find('.portlet-content-wrapper').html($response);                     
			if (portletdata.attr('ptype') == "perf_graph") { get_graph_data.call($(this)); }
		},
		error : function(response,status){
			$(this).find('.portlet-content').html("Data unavailable at this moment.");                      
		},
		dataType : "html"
	});
};

function suffixFormatter(val, axis) {
	if (val > 1000000)
		return (val / 1000000).toFixed(1) + "M";
	else if (val > 1000)
		return (val / 1000).toFixed(axis.tickDecimals) + "K";
	else
		return val.toFixed(axis.tickDecimals);
};

function get_graph_data() {
	var portletdiv = $(this)
	var graphdiv = portletdiv.find(".pg_graph_div");    
	var labeldiv = portletdiv.find(".pg_label")

	var ni = graphdiv.attr('nicename');
	var sc = graphdiv.attr('scenario');
	var la = graphdiv.attr('label');
	var co = graphdiv.attr('column');
	var show_zero = graphdiv.attr('show_zero');

	url = "../portlets/graph_data?nice=" + ni + 
	"&sc=" + sc + 
	"&co=" + co + 
	"&la=" + la;

	function onDataReceived(series) {
		// we get all the data in one go
		// series = { label: "Baseline GC - Used Cpu_s",  data: points }
		data = [ series ];

		options = {
				lines: { show: true },
				points: { show: false },
				grid: {backgroundColor: { colors: ["#fff", "#eee"] }}
		};

		if (show_zero == "true") {
			options.yaxis = { min: 0, tickFormatter: suffixFormatter};
		} else {
			options.yaxis = { tickFormatter: suffixFormatter};
		}

		$.plot(graphdiv, data, options);
	}

	$.ajax({
		url: url,
		data : {},
		method: 'GET',
		async : true,
		context: portletdiv,
		dataType: 'json',
		success: onDataReceived
	});

};

function refresh_wall() {                         

	if ($( "#header" ).attr('refresh') == "true"){    
		if ( $(".portlet").length != 0 ){
			window.location.reload();                             
		}
	}
}; 

function init_autocompletes(){
	$( "#bs_nicename").autocomplete({
		source: function( request, response ) {
			$.getJSON( "../portlets/get_bs_nicename", {
				term: request.term,
				componentgroup: $( "#bs_componentgroup").val()
			}, response );
		},                  
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

	$( "#bs_componentgroup").autocomplete({
		source: "../portlets/get_bs_componentgroup",
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

	$( "#nicename").autocomplete({
		source: "../portlets/get_nice_name",
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

	$( "#set").autocomplete({
		source: "../portlets/get_branch_name",
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

	$( "#pg_nicename").autocomplete({
		source: "../portlets/get_nice_name",
		minLength: 0,
		appendTo : "#add-portlet"
	});

	$( "#pg_scenario").autocomplete({
		source: function( request, response ) {
			$.getJSON( "../portlets/get_pg_scenario", {
				term: request.term,
				nice: $( "#pg_nicename").val()
			}, response );
		},                                   
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	}); 

	$( "#pg_column").autocomplete({
		source: function( request, response ) {
			$.getJSON( "../portlets/get_pg_column", {
				term: request.term,
				nice: $( "#pg_nicename").val(),
				scenario: $('#pg_scenario').val(),
				label: $('#pg_label').val()                        
			}, response );
		},                                   
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	}); 

	$( "#pg_label").autocomplete({
		source: function( request, response ) {
			$.getJSON( "../portlets/get_pg_label", {
				term: request.term,
				nice: $( "#pg_nicename").val(),
				scenario: $('#pg_scenario').val()
			}, response );
		},                                  
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

	$( "#unit_nice, #unit_grid_nice").autocomplete({
		source: "../portlets/get_unittest_versions",
		minLength: 0,
		delay: 700,
		appendTo : "#add-portlet"
	});

};

jQuery(document).ready(function($){
	
	$('#radio0').attr('checked', 'checked');    
	$('#set_button').buttonset('refresh');

	$("#new-wall-btn, #new-wall-btn-1, #add-portlet-btn, #save-wall-btn, #create-portlet, #save-btn, #edit-portlet").button()          
	$("#del-wall-btn, #edit-wall-btn, #edit-wall-btn, #find-wall-btn, #find-wall-btn-1, #save-portlet-btn").button()

	$( ".portlet" ).each(function(){ 
		init_portlet($(this));
	});

	$('.noEnterSubmit').keypress(function(e){
		if ( e.which == 13 ) e.preventDefault();
	});

	$('.wall_name').click(function() {
		$("#error_rename").addClass("hidden");
		$("#new-wall").dialog("option", "title", "Edit Wall").dialog("open");
		$("input#input_wall_name").val($(this).attr('wall_name'));
		$("#edit-wall-btn").show().children().show();
		$("#save-wall-btn").hide().children().hide();         
		$("textarea#input_wall_description").val($(this).attr('description'));
	});
	$('#edit-wall-btn').click(function(e) {
		e.preventDefault();
		if($("input#input_wall_name").val() == ''){
			alert("Please provide a name for the wall");
			return false;
		}
		$( "#edit-wall-btn" ).attr('disabled',true);
		var formdata = {
				"new_name": $("input#input_wall_name").val(),
				"old_name": $("#wallname").attr('wall_name'),
				"description": $("textarea#input_wall_description").val()
		}

		function edit_wall_success(response){
			var url = "../magellan2/wall?name=" + encodeURIComponent( $("input#input_wall_name").val())
			$(location).attr('href', url);
		}

		$.ajax({
			type: "POST",
			url: "../portlets/edit_wall",
			data: formdata,
			context: formdata,
			success: edit_wall_success,
			error: function(response){
				$("#edit-wall-btn").removeAttr("disabled");
				if (response.responseText == "Wall name in use")
				{
					$("#error_rename").removeClass("hidden");
					$("#error_note").text ("Wall name "+$("input#input_wall_name").val() +" is not available.");
				}
				else{
					alert ("Changed not saved to database.");
				}
			}
		});
		return false;                              
	});

	$( ".column" ).sortable({
		connectWith: ".column",
		stop: function(event, ui) {
			var current_col = "col_1";
			var current_row = 1;
			var position_list = [];
			count = 0;
			$.each( $(".portlet"), function(){
				traverse_col = $(this).parent().attr("id");
				if (traverse_col == current_col){
					$(this).attr ("row-cord", current_row );
				}
				else{
					current_row = 1;
					current_col = traverse_col;
					$(this).attr ("row-cord", current_row );
				}
				position_list[count] = "'" + $(this).attr ("portletid") + "':'"+  $(this).parent().attr ("col_num") + "," + current_row + "'";
				current_row = current_row + 1;
				count = count + 1
			});
			data_list = "";
			data_list = "{"  + position_list.join (",") + "}";
			data_1 = { port_data:data_list };
			$.ajax
			({
				type : "GET",
				url : "../portlets/update_postion",
				data : data_1,
				success : function(response){
					//alert ("Save done!");                         
				},
				error : function(response){
					alert("Error :" + response.responseText);                      
				}
			});
		}    
	});

	$( ".column" ).disableSelection();

	$('#new-wall-btn, #new-wall-btn-1').click(function() {
		$("#error_rename").addClass("hidden");
		$("input#input_wall_name").val("");
		$("textarea#input_wall_description").val("");
		$("#save-wall-btn").show().children().show();
		$("#edit-wall-btn").hide().children().hide();
		$("#new-wall").dialog("option", "title", "Edit Wall").dialog("open");
	});   

	$('#del-wall-btn').click(function() {
		if(confirm("Are you sure you want to delete this wall")){
			var data = {
					"wall_name":$(this).attr('wall_name')
			}

			function delete_wall_success(response){
				var url = "../magellan2/wall"
					$(location).attr('href', url);
			}

			$.ajax({
				type: "POST",
				url: "../portlets/delete_wall",
				data: data,
				context: data,
				success: delete_wall_success
			});
			return false;             
		}
		else{
			return false;
		}        
	});

	$( "#tabs" ).selectable({
		// when a particular type of portlet is select in the add portlet form
		// show only the fields relevant to the selected portlet
		// and hide others
		stop: function() {
			$( ".ui-selected", this ).each(function() {
				// iterate over the fields of each type of portlet
				$(this).siblings().each(function(index){
					// disable and hide the input fields for non-selected portlets
					$($(this).attr("href")).addClass('hidden').each(function(i){
						$(this).find("input,textarea").attr("disabled", true);
					});
				})
				// show and enable the inputs corresponding to the selected item
				$($(this).attr("href")).removeClass('hidden').find("input,textarea").removeAttr("disabled").val('');
				$("#widget-header").val("");
			});
		}
	});

	$.each( $(".portlet"), get_portlet_data);          

	$( "#add-portlet").dialog({
		autoOpen: false,
		modal: "true",
		width: 700,
		height: 435,
		position: "center",
		resizable: false
	});

	$("#new-wall").dialog({
		autoOpen: false,
		modal:"true",
		width: 400,
		height: 215,
		position: "center",
		resizable: false
	});

	$( '#add-portlet-btn' ).click(function() {
		$("#tabs").selectable( "enable");
		$("#create-portlet").show().children().show();
		$("#edit-portlet").hide().children().hide();
		$("#add-portlet").dialog("option", "title", "Add Widget").dialog("open");
	});



	$('#create-wall-form').submit(function(event){
		event.preventDefault();                                      
	});

	$('#save-wall-btn').click(function(event){
		event.preventDefault(); 
		if($("input#input_wall_name").val() == ''){
			alert("Please provide a name for the wall");
			return false;
		}
		$( "#save-wall-btn" ).attr('disabled',true);
		var formdata = {
				"name": $("input#input_wall_name").val(),
				"description": $("textarea#input_wall_description").val()        
		}

		function create_wall_success(response){
			var url = "../magellan2/wall?name=" + encodeURIComponent(this.name)
			$(location).attr('href', url);
		}

		$.ajax({
			type: "POST",
			url: "../portlets/create_wall",
			data: formdata,
			context: formdata,
			success: create_wall_success,
			error: function(response){
				if (response.responseText == "Wall name in use")
				{
					$("#save-wall-btn").removeAttr("disabled");
					$("#error_rename").removeClass("hidden");
					$("#error_note").text ("Wall name "+$("input#input_wall_name").val() +" is not available.");
				}
				else{
					alert ("Wall can not be created.");
				}
			}
		});
		return false;                              
	});

	$("#add-portlet-form").submit(function(){
		var portlet = $($(this).find(".ui-selected").attr("href"));                                                                        
		var portlet_data = {};
		portlet.find("input,textarea").each(function(){
			// validate that none of the fields are empty        
			if ( ! $(this).val() ){
				if ( $(this).attr("type")!= "checkbox" ){
					portlet_data = false;
					return false; }
			}
			if ( $(this).attr("type")== "checkbox" ){
				if ( $(this).is(':checked')) {portlet_data[$(this).attr("name")] = "true"; }
				else {portlet_data[$(this).attr("name")] = "false";}
			}
			else {
				portlet_data[$(this).attr("name")] = $(this).val();     
			}
		});

		if (! portlet_data){
			alert("Please provide all the values for the Widget");
			return false;
		}
		var data = {
				"portlet_position": "1,0",
				"ptype" : portlet.attr("ptype"),
				"wall_id" : $("#wall_id").val(),
				"title" : $("#widget-header").val(),
				"data" : JSON.stringify(portlet_data)
		};
		function add_portlet_success(response){          
			var $added_portlet = $(response);
			get_portlet_data.call($added_portlet);
			$(".column:first").prepend($added_portlet);
			init_portlet($added_portlet);
			$( "#add-portlet" ).dialog( "close" );
		}
		$.ajax({
			type: "GET",
			url: "../portlets/add_portlet",
			data: data,
			success: add_portlet_success,
			error: function(response){
				$("#create_portlet").removeAttr("disabled");
				$("#add-portlet").dialog("close");
				alert("Error :" + response.responseText);
			}
		});
		$("#create_portlet").attr("disabled", true);
		return false;
	});

	init_autocompletes();

	$("#edit-portlet").click(function(e){
		e.preventDefault();
		var form = $(this).parents('form:first');
		var portlet = $($(form).find(".ui-selected").attr("href"));                                                                        
		var portlet_data = {};

		portlet.find("input,textarea").each(function(){
			// validate that none of the fields are empty

			if ( ! $(this).val() ){
				if ( $(this).attr("type")!= "checkbox" ){
					portlet_data = false;
					return false;
				}
			}

			if ( $(this).attr("type")== "checkbox" ){
				if ( $(this).is(':checked')) {portlet_data[$(this).attr("name")] = "true"; }
				else {portlet_data[$(this).attr("name")] = "false";}
			}
			else { 
				portlet_data[$(this).attr("name")] = $(this).val();     
			}

		});

		if (! portlet_data){
			alert("Please provide all the values for the Widget");
			return false;
		}

		var data = {
				"data" : JSON.stringify(portlet_data),
				"title" : $("#widget-header").val(),
				"portletid": $(this).attr("portletid")
		}
		function edit_portlet_success(response){
			var $edited_portlet = $(response);
			get_portlet_data.call($edited_portlet);
			$(".column").find(".portlet [portletid='" + this.portletid + "']").parent().replaceWith($edited_portlet);
			init_portlet($edited_portlet);
			$( "#add-portlet" ).dialog( "close" );
		}

		$.ajax({
			type: "GET",
			url: "../portlets/edit_portlet",
			data: data,
			context: data,
			success: edit_portlet_success,
			error: function(response){
				$("#create_portlet").removeAttr("disabled");
				$("#add-portlet").dialog("close");
				alert("Error :" + response.responseText);
			}
		});    
	});

	$("#wall_table tbody").click(function(event) {
		if (event.target.attributes.getNamedItem("wallname"))
		{
			wall_name = event.target.attributes.getNamedItem("wallname").value;
			var url = "../magellan2/wall?name=" + encodeURIComponent(wall_name)
			$(location).attr('href', url);
		}
		else
		{
			return false;
		}
	});  

	$( '#find-wall-btn' ).click(function() {
		$( "#select-wall-form" ).dialog( "open" );
	});

	$( '#find-wall-btn-1' ).click(function() {
		$( "#select-wall-form" ).dialog( "open" );
	});

	$( "#select-wall-form" ).dialog({
		modal: "true",
		autoOpen: false,
		width: 750,
		height: 440,
		position: "center",
		resizable: false
	});
	
	jQuery.fn.dataTableExt.oApi.fnSetFilteringDelay = function ( oSettings, iDelay ) {
		var _that = this;
		this.each( function ( i ) {
			$.fn.dataTableExt.iApiIndex = i;
			var iDelay = (iDelay && (/^[0-9]+$/.test(iDelay)) ? iDelay : 750),
			$this = this,
			oTimerId = null,
			sPreviousSearch = null,
			anControl = $( 'input', _that.fnSettings().aanFeatures.f );

			anControl.unbind( 'keyup' ).bind( 'keyup', function() {
				var $$this = $this;

				if (sPreviousSearch === null || sPreviousSearch != anControl.val()) {
					window.clearTimeout(oTimerId);
					sPreviousSearch = anControl.val(); 
					oTimerId = window.setTimeout(function() {
						$.fn.dataTableExt.iApiIndex = i;
						_that.fnFilter( anControl.val() );
					}, iDelay);
				}
			}); 
			return this;
		} );
		return this;
	}

	wTable = $("#wall_table").dataTable({
		"bAutoWidth": false,
		"bSort": false,
		"bProcessing": true,
		"bServerSide": true,
		"sPaginationType": "full_numbers",
		"sAjaxSource": "../portlets/find_wall",
		"sDom": '<"top"f>rt<"bottom"ip>',

		"fnServerData": function (sSource, aoData, fnCallback) {                    
			$.getJSON(sSource, aoData, function (json) {
				fnCallback(json)
			});                
		}
	})        
	wTable.fnSetFilteringDelay(1500);
	setInterval( "refresh_wall()", 300000 ); /// 300 Seconds refresh
}); 
