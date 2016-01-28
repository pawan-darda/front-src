var required_anchor = [ "iDisplayStart", "iDisplayLength", "sSearch",
		"b1", "b2", "filter_data", "tab", "fs", "set", "page", "tag" ]
var sPreviousSearch = null;
var oTimerId = null;
var get_data_ajax = null;

// Tab indexes
var tab_indexes = {
	"scenarios" : 0,
	"unit" : 1,	
	"sprs" : 2,
	"checkins" : 3,
	"cvcsetup" : 4
};
// Tabs in which differece slider is to disabled.
var hide_diff_slider = [ "scenarios", "unit" ];
var $overlay = $('#scenario_step_data_overlay');
var $exception_overlay = $('#scenario_exception_overlay');
var $unittest_overlay = $('#unittest_exception_overlay');

$(document).ready(function() {
	jQuery.fn.dataTableExt.oApi.fnSetFilteringDelay = function(oSettings, iDelay) {
	var _that = this;
	this.each(function(i) {
		$.fn.dataTableExt.iApiIndex = i;
		var iDelay = (iDelay&& (/^[0-9]+$/.test(iDelay)) ? iDelay: 1000), 
		$this = this, 
		oTimerId = null, 
		sPreviousSearch = null, 
		anControl = $('input',_that.fnSettings().aanFeatures.f);

		anControl.unbind('keyup').bind('keyup',function() {
			var $$this = $this;

			if (sPreviousSearch === null || sPreviousSearch != anControl.val()) {
				window.clearTimeout(oTimerId);
				sPreviousSearch = anControl.val();
				oTimerId = window.setTimeout(
				function() {
					$.fn.dataTableExt.iApiIndex = i;
					_that.fnFilter(anControl.val());
				},iDelay);
				}
			});
			return this;
		});
	return this;
	}
	
	document.getElementById('radio1').checked = true;
	$('#set_button').buttonset('refresh');
	var gloablVersions = [];
	
	firstLoad = true;
	
	// select proper tab if navigating from a bookmark
	var urlData = urlDecoder();
	tabSelected = urlData["tab"] == undefined ? 0
			: parseInt(urlData["tab"]);
	// Disable the diff slider and its label
	// if we are on the alerts tab.
	
	$("#display-tabs").tabs({
		select : function(event, ui) {
			funcVerSelect(ui.index);
		},
		selected : tabSelected
	});
	/*
	if (urlData["txt_tolerance"] == undefined
			|| urlData["txt_tolerance"] == "") {
		$("#txt_tolerance").val(5);
	} else {
		$("#txt_tolerance").val(urlData["txt_tolerance"]);
	}*/
	// set the initial global variables build_1, build_2,
	// dataFiltered from url
	setInitParams()
	
	$("#info1").hide();
	$("#info2").hide();
	$("#info-btn2").buttonset();
	
	if (typeof dataFiltered != "undefined" && dataFiltered == 1) {
		// set the correct filter setting for rel searches
		document.getElementById('radio22').checked = true;
		$('#info-btn2').buttonset('refresh');
	}
	
	$("#info-btn2 input").click(function(e) {
		if (dataFiltered == 0) { dataFiltered = 1 } 
		else { dataFiltered = 0 }
		funcVerSelect(-1);
	});
	
	var sprDataRetrieved = 0;
	/*
	$(".doc_label").click(
			function() {
				funcGetDocument($(this).attr("data_type"), $(
						this).attr("doc_type"));
			});
	*/
	$("#main-slider").slider({
		slide : function(event, ui) {
			$("#diff-slider").slider("value", ui.value);
			renderlabel(ui.value, ui.handle, "#s1");
			renderlabel(ui.value, ui.handle, "#s2");
		},
		stop : function(event, ui) {
			$("#diff-slider").slider("value", ui.value);
			renderlabel(ui.value, ui.handle, "#s1");
			renderlabel(ui.value, ui.handle, "#s2");
		},
		change : function(event, ui) {
			$("#diff-slider").slider("value", ui.value);
			renderlabel(ui.value, ui.handle, "#s1");
			renderlabel(ui.value, ui.handle, "#s2");
		}
	});
	
	$("#diff-slider").slider({
		change : function(event, ui) {
			renderlabel(ui.value, ui.handle, "#s2");
	
			// Abort running ajax query if any.
			get_data_ajax && get_data_ajax.abort();
			window.clearTimeout(oTimerId);
			oTimerId = window.setTimeout(function() {
				funcVerSelect(-1);
			}, 1000);
		},
		slide : function(event, ui) {
			renderlabel(ui.value, ui.handle, "#s2");
		},
		stop : function(event, ui) {
			renderlabel(ui.value, ui.handle, "#s2");
		}
	});
	
	globalSprs = "";
	dataFiltered = typeof dataFiltered == "undefined" ? 0: dataFiltered;
	
	funcGetVersion();
	funcGetReleasedSprs();
	funcGetScenarioSets();
	
	$("#scenario_search, #unit_tag_filter, #unit_search").unbind('keyup')
		.bind('keyup',function(event) {
				window.clearTimeout(oTimerId);
				function search_filters_function(target) {
					// function to update the url on filtering or searching for tag
					if(target.attr("id") == "scenario_search" || target.attr("id") == "unit_search"){
						setAnchorParameter({
							"sSearch" : target.val()
						});
					}
					else if(target.attr("id") == "unit_tag_filter"){
						setAnchorParameter({
							"tag" : target.val()
						});
					}
					setAnchorParameter({
						"page" : 1
					});
//					funcGetScenarioGrid();
					funcVerSelect(-1);
			}	
			var search_filters = function(){search_filters_function($(event.target));};
			oTimerId = window.setTimeout(search_filters, 1000);
		});
	// set initial value of tag and search filters on page load
	
	if(tabSelected == tab_indexes["unit"]){
		$("#unit_tag_filter").val(
				typeof (urlData["tag"]) == undefined ? "" : urlData["tag"])
		$("#unit_search").val(
				typeof (urlData["sSearch"]) == undefined ? "" : urlData["sSearch"])
	}
	else if(tabSelected == tab_indexes["scenarios"]){
		$("#scenario_search").val(
				typeof (urlData["sSearch"]) == undefined ? "" : urlData["sSearch"])
	}
	/*
	$("#txt_tolerance").keyup(
			function() {
				if (sPreviousSearch === null
						|| sPreviousSearch != this.value) {
					window.clearTimeout(oTimerId);
					sPreviousSearch = this.value;
					oTimerId = window.setTimeout(function() {
						alertsTable.fnDraw()
					}, 1000);
				}
			});
	
	$("#txt_tolerance").focus(function() {
		sPreviousSearch = this.value;
	});
	*/
	// Control slider on buils selector click.
	
	$(".build_selector").click(
		function() {
			var button_clicked = this.getAttribute('id');

			var max_value = $("#main-slider").slider(
					"option", "max");
			var min_value = 0;

			switch (button_clicked) {
			case "main_previous_build":
				step = $("#main-slider").slider("option","value");
				if (step != min_value) {
					$("#main-slider").slider("option","value", step - 1);
				};
				break;
			case "main_next_build":
				step = $("#main-slider").slider("option","value");
				if (step != max_value) {
					$("#main-slider").slider("option","value", step + 1);
				};
				break;
			case "difference_previous_build":
				step = $("#diff-slider").slider("option","value");
				if (step != min_value) {
					$("#diff-slider").slider("option","value", step - 1);
				};
				break;
			case "difference_next_build":
				step = $("#diff-slider").slider("option","value");
				if (step != max_value) {
					$("#diff-slider").slider("option","value", step + 1);
				};
				break;
		}
	});
	component = $("div #base-data").attr("component")	
	// Spr datatable properties
	oTableInitData = {
		"bAutoWidth" : false,
		"bSort" : false,
		"bProcessing" : true,
		"bServerSide" : true,
		"sPaginationType" : "full_numbers",
		"sAjaxSource" : "../api/spr_detailed_list",
		"sDom" : '<"top"ilfp>rt<"bottom"lp>',
	
		"fnServerData" : function(sSource, aoData, fnCallback) {
			aoData = updateObject(aoData, [ {
				"name" : "b1",
				"value" : build_1
			}, {
				"name" : "b2",
				"value" : build_2
			}, {
				"name" : "rel_spr",
				"value" : globalSprs
			},
			{
				"name" : "component",
				"value" : component
			}
			  ])
			writeAnchor(aoData)
			get_data_ajax = $.ajax({
				"dataType" : 'json',
				"type" : 'get',
				"url" : sSource,
				"data" : aoData,
				"success" : fnCallback
			})
		}
	}
	// Checkin datatable properties
	checkinTableInitData = {
		"bAutoWidth" : false,
		"bSort" : false,
		"bProcessing" : true,
		"bServerSide" : true,
		"sPaginationType" : "full_numbers",
		"sAjaxSource" : "../api/checkin_detailed_list",
		"sDom" : '<"top"ilfp>rt<"bottom"lp>',
		"fnDrawCallback" : function() {
			redraw_in_process = false;
		},
	
		"fnServerData" : function(sSource, aoData, fnCallback) {
			aoData = updateObject(aoData, [ {
				"name" : "b1",
				"value" : build_1
			}, {
				"name" : "b2",
				"value" : build_2
			}, {
				"name" : "rel_spr",
				"value" : globalSprs
			}, {
				"name" : "filter_data",
				"value" : dataFiltered
			} ]);
			writeAnchor(aoData)
			get_data_ajax = $.ajax({
				"dataType" : 'json',
				"type" : 'get',
				"url" : sSource,
				"data" : aoData,
				"success" : fnCallback
			})
		}
	}
	/*
	alertsTableInitData = {
		"bJQueryUI" : false,
		"bSort" : true,
		"bPaginate" : true,
		"bProcessing" : true,
		"bFilter" : true,
		"bServerSide" : true,
		"sAjaxSource" : "../api/alerts_list",
		"sPaginationType" : "full_numbers",
		"sDom" : '<"top"ilpf> rt <"bottom"ilpf>',
		"bAutoWidth" : false,
	
		"aoColumnDefs" : [ {
			"bVisible" : false,
			"aTargets" : [ 0 ]
		}, {
			"sClass" : "alert-number",
			"aTargets" : [ 5, 6, 7 ]
		} ],
	
		"fnServerData" : function(sSource, aoData, fnCallback) {
			aoData.push({
				"name" : "b1",
				"value" : build_1
			});
			aoData.push({
				"name" : "txt_tolerance",
				"value" : document
						.getElementById('txt_tolerance').value
			});
			writeAnchor(aoData)
			get_data_ajax = $.ajax({
				"dataType" : 'json',
				"type" : 'get',
				"url" : sSource,
				"data" : aoData,
				"success" : fnCallback
			})
		},
		"oLanguage" : {
			"sSearch" : "Search:"
		}
	};
	
	
	$("#alerts-table tbody").click(function(event) {
		$(alertsTable.fnSettings().aoData).each(function() {
			$(this.nTr).removeClass('row_selected');
		});
		$(event.target.parentNode).addClass('row_selected');
		redirect_link = fnGetGraphRedirectLink();
		window.location = redirect_link
	});
	*/
	
	var initial_data = getInitParams();
	var selectedTab = $("#display-tabs").tabs("option",
			"selected")
	if (getAnchorUrl() != "") {
		for (data in initial_data) {
			switch (selectedTab) {
			case tab_indexes["sprs"]:
				oTableInitData[data] = initial_data[data];
				break;
			case tab_indexes["checkins"]:
				checkinTableInitData[data] = initial_data[data];
				break;
			//case tab_indexes["alerts"]:
			//	alertsTableInitData[data] = initial_data[data];
			//	break;
			}
		}
	}
	
	delete firstLoad;
	/*
	 * click events on scenario grid
	 * if(event.target.getAttribute("sc_id") != null){
	 * funcGetScenarioStep(event.target.getAttribute("sc_id")) } })
	 */
	
	
	$overlay.click(function(event) {
		show_details(event)
	});
	
	$("#scenario_grid_data, #unittest_grid_data").click(function(event) {
		// event.stopPropagation();
		// $('div').slideDown();
		function update_step_data(response, status) {
			this.html(response);
			scenario_fix();
		}
		var $this = $(this);
		var data = {}
		
		if ($this.attr("id") == "scenario_grid_data"){
			// cell in scenario grid clicked
			
			var target_overlay = $overlay;
			var uri = "../api/get_scenario_steps";
			var target_id = event.target.getAttribute("sc_id");
			data["sc_id"] = target_id;
		}
		else if($this.attr("id") == "unittest_grid_data"){
			// cell in unittest grid clicked
			
			var target_overlay = $unittest_overlay;
			var uri = "../api/get_unittest_exception";
			target_id = event.target.getAttribute("test_id");
			data["unit_id"] = target_id;
		}
		
		target_overlay.html("<i>Loading data</i>");
		if (target_id) {
			$.ajax({
				url : uri,
				data : data,
				success : update_step_data,
				dataType : "text",
				context : target_overlay
			});
			target_overlay.dialog({
				width : $(window).width() * 0.8,
				height : $(window).height() * 0.8,
				modal : true,
				open: function(event, ui){$('body').css('overflow','hidden');$('.ui-widget-overlay').css('width','100%')},
				close: function(event, ui){$('body').css('overflow','auto')}
			}).fadeIn();
		}
	});
// document ready end	
});

show_details = function(event) {
	if($(event.target).hasClass("ui-icon-circle-minus")){
		var sibling = $(event.target).closest("tr").next("tr")
		if(sibling.hasClass("scen_error_details")){
			sibling.remove();
		}
		$(event.target).toggleClass("ui-icon-circle-minus", 0).toggleClass("ui-icon-circle-plus", 1)
		return;
	}
	$exception_overlay.html("<i>Loading data</i>");
	var cell_id = $(event.target).attr("cell_id");
	var row_id = $(event.target).attr("row_id");
	var step_id = $(event.target).attr("step_id");
	var url = "";
	if (cell_id) {
		url = "../api/get_cell_exception_details";
		var data = { "cell_id" : cell_id };
	} 
	else if (row_id) {
		url =  "../api/get_step_row_exception_details";
		var data = { "row_id" : row_id };
	} 
	else if (step_id) {
		url = "../api/get_step_row_exception_details";
		var data =  { "step_id" : step_id };
	}

	if( url != ''){
		$(event.target).toggleClass("ui-icon-circle-plus", 0).toggleClass("ui-icon-circle-minus", 1);
		$(event.target).closest("tr").find(".ui-icon-circle-minus")
			.toggleClass("ui-icon-circle-minus", 0)
			.toggleClass("ui-icon-circle-plus", 1);
		var sibling = $(event.target).closest("tr").next("tr")
		if(sibling.hasClass("scen_error_details")){
			sibling.remove()
		}
		$.ajax({
			url : url,
			data : data,
			success : function(response, status) {
				var colspan = this.closest("tr").children().length + 1;
				var row_width = this.closest("tr").width();
				var dialog_width = $overlay.dialog( "option", "width");
				var width =  row_width - 70 ? row_width < dialog_width : dialog_width - 70 ;
				var $response = $(response)
				$response.css("width", width);
				var $err_data = $('<tr class="scen_error_details"><td colspan="' + colspan + '"></td></tr>');
				$err_data.find("td").first().html($response);
				this.closest("tr").after($err_data);				
			},
			error : function(response, status) {
				this.closest("tr").after('<tr class="scen_error_details"><td style="color: red; font-weight:bold" colspan="3"> ERROR: Unable to fetch the Data. If issue persist please contact us.</td></tr>');
			},
			dataType : "text",
			context : $(event.target)
		});
	}
};

funcGetScenarioSets = function() {

	var url_vers = "../api/get_sets";
	var sc_comp = $.trim($("#base-data").attr("component"));

	function set_success(response, status) {

		$('#scenario_set_filter').append(
				$("<option></option>").attr("value", "none").text(
						"all sets ..."));

		$.each(response, function(index, value) {
			$('#scenario_set_filter').append(
					$("<option></option>").attr("value", value).text(value));
		});

		var uriData = urlDecoder();

		if (uriData["set"] != undefined) {
			var sc_set = "#scenario_set_filter option[value='"
					+ uriData["set"] + "']"
			$(sc_set).attr("selected", "selected");
		} else {
			$('#scenario_set_filter option:first-child').attr("selected",
					"selected");
		}
		setAnchorParameter({
			"set" : $("#scenario_set_filter option:selected").val()
		});
		$('#scenario_set_filter').change(
			function() {
				setAnchorParameter({
					"set" : $( "#scenario_set_filter option:selected").val()
				});
				setAnchorParameter({ "page" : 1 });
				funcGetScenarioGrid();
			})
	}
	$.ajax({
		url : url_vers,
		data : {
			"sc_comp" : sc_comp
		},
		async : false,
		success : set_success,
		dataType : "json"
	});
}

/*
funcGetDocument = function(dtt, dct) {
	if (dtt == "spr") {
		url_spr = "../document/spr_document"
		data = {
			"doc_type" : dct,
			"build_1" : build_1,
			"b2" : build_2
		};
		$.download(url_spr, data, 'get');

	} else if (dtt == "checkin") {
		url_checkin = "../document/checkin_document"
		data = {
			"doc_type" : dct,
			"b1" : build_1,
			"b2" : build_2,
			"rel_spr" : globalSprs,
			"filter_data" : dataFiltered
		};
		$.download(url_checkin, data, 'get');
	}
};
*/

ajaxErrorCallback = function() {

	// This global function needs to be called when a Ajax call fails for any
	// error or has a timeout
	// This will give and overlay saying something is broken please contact us
	// Needs to implemented though

};

funcGetVersion = function() {
	var ver_name = $("input#id_qv").val();
	var url_vers = "../api/get_versions?vfilter=" + ver_name;
	get_vers = function(response, status) {
		funcUpdateSlider(response);
	}
	$.ajax({
		url : url_vers,
		data : {},
		success : get_vers,
		async : false,
		dataType : "text"
	});
	hideDiffSlider(tabSelected);
};

funcGetReleasedSprs = function() {

	var release = $.trim($("#base-data").attr("release"));
	var component = $.trim($("#base-data").attr("component"));

	if (release != "" & component != "") {

		$("#info-btn2").hide();
		$("#info1").show();
		$("#info2").show();
		$("#info-l1").text(
				"Fetching SPR Details from FAST for " + component + " and "
						+ release);
		$("#info-l2").text(
				"Fetching SPR Details from FAST for " + component + " and "
						+ release);

		var url_sprs = "../api/get_spr_release_information?rel=" + release
				+ "&comp=" + component;

		get_sprs = function(response, status) {
			globalSprs = $.trim(response);
		}
		$.ajax({
			url : url_sprs,
			data : {},
			success : get_sprs,
			async : false,
			dataType : "text"
		});

		if (globalSprs != '') {
			tmpLth = globalSprs.split(",").length;
		} else {
			tmpLth = 0;
			// $("#info-btn2 input").attr("disabled", true);
			// $("#radio22").hide();
		}

		strS = " release ( " + tmpLth + " SPR found )";
		$("#info-l1").text(
				"SPR Details retrieved from FAST for " + component
						+ " component and " + release + strS);
		$("#info-l2").text(
				"SPR Details retrieved from FAST for " + component
						+ " component and " + release + strS);
		$("#info-btn2").show();

	}
	sprDataRetrieved = 1;
};

// Ajax call to retrieve grid data for Scenario Tab
funcGetScenarioGrid = function() {

	$("#scenario_processing").show();
	get_data_ajax && get_data_ajax.abort();
	var data = []
	var uriData = urlDecoder();
	var page_number = 1;
	var selectedTab = $("#display-tabs").tabs("option","selected")
	if(selectedTab == tab_indexes["scenarios"] && uriData["page"] != undefined){
		page_number = uriData["page"]
	}
	
	data.push({ "name" : "page", "value" : page_number });
	
	var scenset = uriData["set"] == undefined ? 
			$("#scenario_set_filter").val() : uriData["set"];
	var scensearch = $("#scenario_search").val()
	var component = $.trim($("#base-data").attr("component"));

	data.push({ "name" : "set", "value" : scenset });
	data.push({ "name" : "sSearch", "value" : scensearch });
	data.push({ "name" : "b1", "value" : build_1 });
	data.push({ "name" : "b2", "value" : build_2 });
	data.push({ "name" : "component", "value" : component });

	writeAnchor(data);

	var idx = $("#main-slider").slider("value")
	var start = idx - 12
	var stop = idx + 12
	if (gloablVersions.length - idx < 12) {
		start = start - (12 - (gloablVersions.length - idx))
	}
	if (idx - 12 < 0) 
	{   start = 0;
		stop = stop + (12 - idx);
	}

	data.push({
		"name" : "versions_list",
		"value" : gloablVersions.slice(start, stop).join(",")
	})

	var update_scenario_grid_data = function(response, status) {

		$("#scenario_grid_data").html(response);
		// decorate and add clicks to pagination links on scenario grid
		decorate_pagination_buttons($('#scenario_grid_data').find( "#scenario_pagination"));
		
		$('.pagination_button').click(function(e) {
			e.stopPropagation();
			setAnchorParameter({
				"page" : this.getAttribute('page')
			});
			funcGetScenarioGrid();
		});
		$("#scenario_processing").hide();
	};

	get_data_ajax = $.ajax({
		url : "../api/get_scenario_grid",
		data : data,
		success : update_scenario_grid_data,
		dataType : "text"
	});

};

// Ajax call to retrieve grid data for Unit Test Tab
funcGetUnittestGrid = function() {

	$("#unittest_processing").show();
	get_data_ajax && get_data_ajax.abort();
	var data = []
	var uriData = urlDecoder();
	var page_number = 1;
	var selectedTab = $("#display-tabs").tabs("option","selected")
	
	if(selectedTab == tab_indexes["unit"] && uriData["page"] != undefined){
		page_number = uriData["page"]
	}
	
	data.push({ "name" : "page", "value" : page_number });
	
	var unittag = $("#unit_tag_filter").val();
	var usearch = $("#unit_search").val();
	var component = $.trim($("#base-data").attr("component"));

	data.push({ "name" : "tag","value" : unittag });
	data.push({ "name" : "sSearch", "value" : usearch });
	data.push({ "name" : "b1", "value" : build_1 });
	data.push({ "name" : "b2", "value" : build_2 });
	data.push({ "name" : "component", "value" : component });

	writeAnchor(data);

	var idx = $("#main-slider").slider("value")
	var start = idx - 10
	var stop = idx + 10
	if (gloablVersions.length - idx < 10) {
		start = start - (10 - (gloablVersions.length - idx))
	}
	if (idx - 10 < 0) { 
		start = 0;
		stop = stop + (10 - idx) ;
	
	}

	data.push({
		"name" : "versions_list",
		"value" : gloablVersions.slice(start, stop).join(",")
	})

	var update_unittest_grid_data = function(response, status) {

		$("#unittest_grid_data").html(response);
		// decorate and add clicks to pagination links on scenario grid
		//decorate_pagination_links();
		decorate_pagination_buttons($('#unittest_grid_data').find( "#unittest_pagination"));
		$('.pagination_button').click(function(e) {
			e.stopPropagation();
			setAnchorParameter({ "page" : this.getAttribute('page') });
			funcGetUnittestGrid();
		});
		$("#unittest_processing").hide();
	};

	get_data_ajax = $.ajax({
		url : "../api/get_unittest_grid",
		data : data,
		success : update_unittest_grid_data,
		dataType : "text"
	});

};

// Ajax call to retrieve data for CVC setup tab
funcGetCvcSetup = function() {

	var data = []
	data.push({
		"name" : "b1",
		"value" : build_1
	});
	data.push({
		"name" : "b2",
		"value" : build_2
	});
	writeAnchor(data);
	if (build_2 == "") {

		$("#cvc_info").text(
				"Please select Build 1 and Build 2 to compare CVC Setup");
		$("#cvc_setup_data").html("");

	} else {

		$("#cvc_info").text(
				"Fetching CVC setup details for '"
						+ beautifyLabel(build_1).split("-")[0] + "' and '"
						+ beautifyLabel(build_2).split("-")[0]
						+ "' Please wait ... ");
		$("#cvc_setup_data").html("");

		var url_sprs = "../api/get_cvc_setup";

		update_cvc_data = function(response, status) {
			$("#cvc_setup_data").html(response);
			$("#cvc_info").text(
					"CVC setup details for '"
							+ beautifyLabel(build_1).split("-")[0] + "' and '"
							+ beautifyLabel(build_2).split("-")[0]);
		}
		get_data_ajax = $.ajax({
			url : url_sprs,
			data : data,
			success : update_cvc_data,
			dataType : "text"
		});
	}
};

funcUpdateSlider = function(lstVer) {
	gloablVersions = lstVer.split(",");
	gloablVersions = gloablVersions.reverse();

	$("#main-slider").slider("option", "min", 0);
	$("#main-slider").slider("option", "max", gloablVersions.length - 1);
	release = $.trim($("#base-data").attr("release"));

	var build_1_index = typeof build_1 == "undefined" ? gloablVersions.length - 1
			: jQuery.inArray(build_1, gloablVersions)
	var init_label = beautifyLabel(gloablVersions[build_1_index]);
	
	$("#main-slider").slider("option", "value", build_1_index);
	$("#diff-slider").slider("option", "min", 0);
	$("#diff-slider").slider("option", "max", gloablVersions.length - 1);
	$("#s1").text(init_label);
	$("#s1").css('margin-left', "5px");
	
	build_1 = gloablVersions[$("#main-slider").slider("value")];
	// set label position for main-slider
	renderlabel($("#main-slider").slider("value"), $("#main-slider").find(
			"a.ui-slider-handle:first")[0], "#s1")

	var build_2_init_idx = release == "" ? getPreviousPrimeIndex() : 0;
	var build_2_index = typeof build_2 == "undefined" ? build_2_init_idx
			: jQuery.inArray(build_2 == "" ? build_1 : build_2, gloablVersions)
	var last_label = beautifyLabel(gloablVersions[build_2_index]);
	$("#diff-slider").slider("option", "value", build_2_index);
	$("#s2").text(last_label);
	build_2 = gloablVersions[$("#diff-slider").slider("value")];
	build_2 = build_2 == build_1 ? "" : build_2;

	// set label position for diff-slider
	renderlabel($("#diff-slider").slider("value"), $("#diff-slider").find(
			"a.ui-slider-handle:first")[0], "#s2")
};

beautifyLabel = function(ilabel) {

	ilabels = ilabel.split("-");
	if (ilabels.length == 3) {
		init_date = $.datepicker.formatDate('dd M yy', $.datepicker.parseDate(
				'yymmdd', ilabels[2]));
		inewLabel = ilabels[1] + " - " + init_date;
	} else {
		inewLabel = ilabel;
	}

	return inewLabel;
}

hideDiffSlider = function(tabSelected) {
	for ( var i = 0; i < hide_diff_slider.length; i++) {
		if (tab_indexes[hide_diff_slider[i]] == tabSelected) {
			$("#diff-slider").slider("disable");
			//$("#s2").css('opacity','0.4');
			//$("#s2").css('filter','alpha(opacity=40)');
			$("#difference_previous_build").hide();
			$("#difference_next_build").hide();
			break;
		} else {
			$("#diff-slider").slider("enable");
			//$("#s2").css('opacity','1.0');
			//$("#s2").css('filter','alpha(opacity=100)');
			$("#difference_previous_build").show();
			$("#difference_next_build").show();
		}

	}
}

getPreviousPrimeIndex = function() {
	/* gets the previous index of prime for showing diff on first load of page */
	var prev_date_idx = 0;
	var final_date = gloablVersions[gloablVersions.length - 1].split("-")
	if (final_date.length == 3) {
		final_date = $.datepicker.parseDate('yymmdd', final_date[2])
		for ( var i = gloablVersions.length - 1; i >= 0; i--) {
			var pdate = $.datepicker.parseDate('yymmdd', gloablVersions[i]
					.split("-")[2])
			if (Math.floor((final_date - pdate) / (1000 * 60 * 60 * 24)) > 1) {
				prev_date_idx = i;
				break;
			}
		}
	}
	return prev_date_idx
}

renderlabel = function(value, handle, control) {
	var label = null;
	label = gloablVersions[value];

	if (label != null) {

		var newLabel = beautifyLabel(label);

		if (handle.offsetLeft < handle.offsetParent.clientWidth / 2) {
			$(control).text(newLabel);
			$(control).css('margin-left',
					handle.offsetLeft + (("" + label).length) + 25 + 'px');
		} else {
			$(control).text(newLabel);
			$(control).css('margin-left',
					handle.offsetLeft - (("" + label).length) - 125 + 'px');
		}
	}
};

funcVerSelect = function(selected) {

	var ver1_sel_idx = $("#main-slider").slider("value");
	var ver2_sel_idx = $("#diff-slider").slider("value");

	var ver_name1 = gloablVersions[ver1_sel_idx];
	var ver_name2 = gloablVersions[ver2_sel_idx];

	if (ver_name1 == ver_name2) {
		ver_name2 = ""
	}
	build_1 = ver_name1;
	build_2 = ver_name2;

	if (selected == -1) {
		selected = $("#display-tabs").tabs("option", "selected");
	}

	tabSelected = selected;
	setAnchorParameter({"tab" : tabSelected});

	hideDiffSlider(selected);
	get_data_ajax && get_data_ajax.abort();
	
	switch (selected) {
	case tab_indexes["scenarios"]:
		funcGetScenarioGrid();
		break;
	case tab_indexes["unit"]:
		funcGetUnittestGrid();
		break;
	case tab_indexes["sprs"]:
		if (typeof (oTable) != 'undefined') {
			bResetDisplay = false;
			oTable.fnDraw();
			bResetDisplay = true;
		} else {
			oTable = $("#spr-info").dataTable(oTableInitData);
			oTable.fnSetFilteringDelay(1000);
			delete oTableInitData;
		}
		break;
	case tab_indexes["checkins"]:
		if (typeof (checkin_Table) != 'undefined') {
			bResetDisplay = false;
			checkin_Table.fnDraw();
			bResetDisplay = true;
		} else {
			checkin_Table = $("#checkin-info").dataTable(checkinTableInitData);
			checkin_Table.fnSetFilteringDelay(1000);
			delete checkinTableInitData;
		}
		break;
	/*case tab_indexes["alerts"]:
		if (typeof (alertsTable) != 'undefined') {
			bResetDisplay = false;
			alertsTable.fnDraw();
			bResetDisplay = true;
		} else {
			alertsTable = $("#alerts-table").dataTable(alertsTableInitData);
			alertsTable.fnSetFilteringDelay(1000);
			delete alertsTableInitData;
		}
		break;*/
	case tab_indexes["cvcsetup"]:
		funcGetCvcSetup();
	}

	if (sprDataRetrieved == 0) {
		funcGetReleasedSprs();
	}

	delete ver_name1, ver1_sel_idx;
	delete ver_name2, ver2_sel_idx;
	delete selected;

};

getAnchorUrl = function() {
	/* return the anchor parth of the url, minus the # */
	return window.location.hash.substring(1);
}

updateObject = function(obj, params) {
	/* update a given javascript object with given values */
	for ( var i = 0; i < params.length; i++) {
		var flag = 0;
		var par = params[i]["name"];
		for ( var j = 0; j < obj.length; j++) {
			if (obj[j]["name"] == params[i]["name"]) {
				obj[j]["value"] = params[i]["value"];
				flag = 1
				break;
			}
		}
		if (flag == 0) {
			obj.push(params[i])
		}
	}
	return obj
}

getInitParams = function() {
	/*
	 * calculates and returns corresponding init params for a data table based
	 * on saved state of a table
	 */
	var uriData = urlDecoder();
	var initParams = {};
	uriData["sSearch"] == undefined ? null : initParams["oSearch"] = {
		"sSearch" : uriData["sSearch"]
	};
	uriData["iDisplayStart"] == undefined ? null
			: initParams["iDisplayStart"] = parseInt(uriData["iDisplayStart"]);
	uriData["iDisplayLength"] == undefined ? null
			: initParams["iDisplayLength"] = parseInt(uriData["iDisplayLength"]);
	return initParams;
}

setInitParams = function() {
	/*
	 * sets the global params like build_1, build_2 from the url at
	 * initialization
	 */
	var uriData = urlDecoder();

	uriData["b1"] == undefined ? null : build_1 = uriData["b1"];
	uriData["b2"] == undefined ? null : build_2 = uriData["b2"];
	uriData["filter_data"] == undefined ? null
			: dataFiltered = uriData["filter_data"];
}

fnGetGraphRedirectLink = function() {
	var aTrs = alertsTable.fnGetNodes();
	var href = "";
	for ( var i = 0; i < aTrs.length; i++) {
		if ($(aTrs[i]).hasClass('row_selected')) {
			var aData = alertsTable.fnGetData(i);
			href = 'graph?ql=name:"' + aData[4] + '"&qc=name:"' + aData[3]
					+ '"&qs=name:"' + aData[0] + '"&qv=' + build_1;
			break;
		}
	}
	return href;
}

writeAnchor = function(paramSet) {
	/*
	 * Writes the new anchor with the given set of values
	 */
	var obj = []
	for ( var i in paramSet) {
		obj[paramSet[i]["name"]] = paramSet[i]["value"];
	}
	var uriData = urlDecoder();
	typeof (uriData["tab"]) == "undefined" ? null : obj["tab"] = uriData["tab"]
	typeof (uriData["fs"]) == "undefined" ? null : obj["fs"] = uriData["fs"]
	var new_url = urlEncoder(obj);
	window.location.href = "#" + new_url;
}