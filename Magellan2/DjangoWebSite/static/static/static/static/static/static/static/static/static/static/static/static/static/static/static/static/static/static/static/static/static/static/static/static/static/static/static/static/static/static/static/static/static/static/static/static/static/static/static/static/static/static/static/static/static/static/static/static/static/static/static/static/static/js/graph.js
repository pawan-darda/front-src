var required_anchor =["fs"];
$(document).ready(function() {
	decorate_pagination_buttons($('#base-table').find( "#top_pagination"));
	decorate_pagination_buttons($('#base-table').find( "#bottom_pagination"));
	
	var main_lbl = '';
	var sub_lbl = '';
	main_lbl = $("input[id$='main']");
	sub_lbl = $("input[id$='sub']");		
	var main_val = $.trim(main_lbl.val());
	var sub_val = $.trim(sub_lbl.val());

	document.getElementById('radio3').checked=true;
	$('#set_button').buttonset('refresh');
	$(".spr-build-tabs").tabs();
	//alert($(".spr-build-tabs").html());
	var ann_data = [];
	var g_data = [];
	
	$(".doc_label").click(function(){
		funcGetDocument($(this).attr("data_counter"),$(this).attr("doc_type"));
	});	

	var user_options = {
	    //Texts displayed below the chart's x-axis and to the left of the y-axis 
	    titleFont: "bold 18px serif",
	    
	    //Texts displayed below the chart's x-axis and to the left of the y-axis 
	    axisLabelFont: "bold 18px serif",
	
	    // Texts for the axis ticks
	    labelFont: "normal 14px serif",
	
	    // Text for the chart legend
	    legendFont: "bold 18px serif",
	
	    legendHeight: 30    // Height of the legend area
	}; 

	funcGetDocument = function(dtt,dct){
	
		if (dct == "png"){			
			g = g_data[dtt - 1];
			Dygraph.Export.asPNG(g, user_options);

		}
	};

    unZoomGraph = function (index) {
    	g = g_data[index - 1];
    	g.updateOptions({
          dateWindow: null,
          valueRange: null
        });
    };

    funcGetBuildNumbers = function() {
											
		var url_ann = "../api/get_annotations?main="+main_val+"&sub="+sub_val;
		get_builds = function(response, status) {
			$.each(response.split(","), function(index,
					value) {
				if (value != "") {
					ann_data.push(value);
				}
			});
		}
		$.ajax({
			url : url_ann,
			data : {},
			success : get_builds,
			async : false,
			dataType : "text"
		});
	};
	if ($("input#id_qv").val() != ''){
	   funcGetBuildNumbers();
	}
	
	funcUpdateSprBuildData = function(col){

    	var sprnu = $.trim($(col).text());
		var annot = [];
		var annot_refreshed = [];
    	
    	var gdiv = $(col).parent().parent().parent().parent().parent().parent().parent().parent();
		var gcount = parseInt(gdiv.attr("counter"))-1;
		
    	$.get("../api/get_spr_build_maping", {format : "html", sprno : sprnu, main : main_val, sub : sub_val },
			function(data) {				
				annot = g_data[gcount].annotations();
		  		tmp_series_val = "x-axis\r";

		  		$.each(annot, function(index, annot_v) {
					if (annot_v.attachAtBottom == true) {
						annot_refreshed.push(annot_v);
					}
				});
				
				$.each(data.split(","), function(index,value) {
					if (value != "") {
						annot_refreshed.push({
						series : tmp_series_val,
						x : value,
						icon : '../static/images/slider_red.png',
						width : 18,
						height : 18,
						tickHeight : 7,
						attachAtBottom : false,
						text : 'Build ' + value +' SPR ' + sprnu
						});		
					}
				});
				
				g_data[gcount].setAnnotations(annot_refreshed);
				
				delete annot;
				delete annot_refreshed;
				delete tmp_series_val;
				
			});
			
		delete sprnu;
		delete gdiv;
		delete gcount;
    	
	};
	
	funcClearSprBuildData = function(g){
		var annot = [];
		var annot_refreshed = [];
 
		annot = g.annotations();
  		$.each(annot, function(index, annot_v) {
			if (annot_v.attachAtBottom == true) {annot_refreshed.push(annot_v);}
		});
		
		g.setAnnotations(annot_refreshed);
		delete annot;
		delete annot_refreshed;
		delete g;
	};

	funcUpdateBuildData = function(
			buildcomment_datadiv,
			spr_datadiv,
			last_ann,
			x_val, main_val, sub_val) {
									
		if (last_ann != x_val) {
			last_ann = x_val
			$(buildcomment_datadiv).html($("#loading_img_sm").html());
			$(spr_datadiv).html($("#loading_img_sm").html());
			$.get("../api/build_sprs", {
				format : "html",
				build : x_val,
				main : main_val,
				sub : sub_val
			}, function(data) {
				$(spr_datadiv).empty();
				$(spr_datadiv).html(data);
			});

			$.get("../api/build_comments", {
				format : "html",
				build : x_val,
				main : main_val,
				sub : sub_val
			}, function(data) {
				$(buildcomment_datadiv).empty();
				$(buildcomment_datadiv).html(data);
			});
		}
	};
	$('.graphdiv').each(function() {
		var url = "../api/hist_data?format=csv&label="
				+ $(this).attr("label")
				+ "&col="
				+ $(this).attr("column")
				+ "&vfilter="
				+ $(this).attr("version_filter")
				+ "&baseline="
				+ $(this).attr("baseline")
				+ "&scenario="
				+ $(this).attr("scenario");
		var div = this;
		var v4Canvas = null;
		var buildcomment_datadiv = "#buildcomment-tab-" + $(div).attr("counter");
		var spr_datadiv = "#spr-tab-" + $(div).attr("counter");
		var tabdiv = "#tab-" + $(div).attr("counter");
		var labeldiv = "#build-label-" + $(div).attr("counter");
		var main_val = $(this).attr("main");
		var sub_val = $(this).attr("sub");
		var label_text = " Build : " + main_val + "." + sub_val + "."
		var last_ann = -1;
		
		var seriesval = $(div).attr( "column");
		
		var scenario = $(div).attr("scenario");		
		var label = $(div).attr("label");
		
		counter = $(div).attr("counter");


		mouse_down = function(event, g, context){
	    	Dygraph.defaultInteractionModel.mousedown(event, g, context);
	    };
	    mouse_up = function(event, g, context){
	    	Dygraph.defaultInteractionModel.mouseup(event, g, context);
	    };
	    mouse_move = function(event, g, context){
	    	Dygraph.defaultInteractionModel.mousemove(event, g, context);
	    };
	    double_click = function(event, g, context){
	    	Dygraph.cancelEvent(event);
	    };

		labelsKMB = true;
		colors = [ 'Teal', 'Black'];
		
		var yLable = seriesval;
		
		if ($(this).attr("baseline")) {
						
			labelsKMB = false;
			colors = [ 'Blue', 'FireBrick', 'Black'];
			yLable = seriesval + " (%) ";
		}
        
        function captureCanvas(canvas, area, g) {
        				v4Canvas = canvas;
      	}
        
		// Creating a closure with a div reference that will iteself create the graph
		success = function(response, status) {
			g = new Dygraph(
					div,
					response,
					{
						title: scenario,				
						ylabel: yLable,
						xlabel: label + " for Prime "  + main_val + "." + sub_val ,
						showRoller : true,
						includeZero : true,
						drawPoints : false,
						labelsKMB : labelsKMB,
						pointSize : 2,
						strokeWidth : 1.5,
						rightGap : 10,
						highlightCircleSize : 4,
						
						xAxisLabelWidth: 60,
						yAxisLabelWidth: 60,
						
						fillGraph : false,
						labelsShowZeroValues : false,
						colors : colors,
						labelsDiv : $(div).attr("value_div"),
						
						underlayCallback : captureCanvas,
								
						connectSeparatedPoints : false,						
						interactionModel : {
				            'mousedown' : mouse_down,
				            'mousemove' : mouse_move,
				            'mouseup' : mouse_up,
				            'dblclick' : double_click
				           }
					});
			
			annotations = [];
			$.each(ann_data,function(index,value) {
				annotations.push({
							series : seriesval,
							x : value,
							icon : '../static/images/slider.png',
							width : 18,
							height : 18,
							tickHeight : 7,
							attachAtBottom : true,
							text : 'Build '	+ value
						});
				});
			g.setAnnotations(annotations);
			g.updateOptions({annotationClickHandler : 
				function( ann, point, dg, event) {
					g.updateOptions({ });
					$(labeldiv).text(label_text + ann.x);
					funcUpdateBuildData(
							buildcomment_datadiv,
							spr_datadiv,
							last_ann,
							ann.x,
							main_val,
							sub_val);
							
					last_ann = ann.x;
					
					if (ann.attachAtBottom == true) {
						$(tabdiv).tabs('select', 1);
					}
					else {$(tabdiv).tabs('select', 0);
					}

				},
				clickCallback : function(event, p) 
				{
					build_num = p;
					funcUpdateBuildData(
							buildcomment_datadiv,
							spr_datadiv,
							last_ann,
							build_num,
							main_val,
							sub_val);
					last_ann = build_num;
					$(tabdiv).tabs('select', 0);
					$(labeldiv).text(label_text + build_num);
				},
				annotationMouseOverHandler : function(
						ann, point,
						dg, event) {
					ann.div.style.cursor='pointer';
				}
			});
		g_data.push(g);
		}
		error = function(response, status) {
			$(div).replaceWith( 'Data unavailable: Most likely, the data does not exist in the baseline version.');
		}
		// create an ajax call that will trigger the closure with the values that come from the get. 
		//points = $.get (url, {}, func, "text");
		$.ajax({
			url : url,
			data : {},
			async : false,
			success : success,
			error : error,
			dataType : "text"
		});
	});
});