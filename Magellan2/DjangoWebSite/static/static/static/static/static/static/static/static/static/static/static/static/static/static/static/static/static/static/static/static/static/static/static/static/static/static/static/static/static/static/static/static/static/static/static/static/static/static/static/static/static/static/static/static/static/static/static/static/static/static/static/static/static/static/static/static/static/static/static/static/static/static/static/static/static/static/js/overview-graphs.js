var required_anchor =["fs"];
$(document).ready(function(){ 

	document.getElementById('radio5').checked=true;
	$('#set_button').buttonset('refresh');
		
	$("#lined_img").click(function (){
		$('.subgraphdiv').each (function (){
			if ($(this).css("width")=="101%") { $(this).css({width:"47%"}); }
			else { $(this).css({width:"101%"}); }
		});
		funcUpdate();
	});

	funcUpdate = function() {
	$('.graphdiv').each (function (){
		
		var divThis = this;
		var url = "../api/hist_data?format=csv&label=" + $(this).attr ("label")+
			"&col=" + $(this).attr ("column")+
			"&vfilter=" + $(this).attr ("version_filter")+
			"&baseline=" + $(this).attr ("baseline")+
			"&scenario=" + $(this).attr ("scenario");

		formatter = function(x) { return x; }
			
		labelsKMB = true;
		colors = ['Teal'];
		strokeWidth = 1.5; 
		
		if ($(this).attr ("baseline")){
			formatter = function(x) {
			    return "" + x + "%"
			};
			labelsKMB = false;
			strokeWidth = 1;
			colors = ['Blue', 'FireBrick'];
		}	
			
		// Creating a closure with a div reference that will itself create the graph
		success = function (response, status){
			var restext = $.trim(response);

			if (restext == 'Data Unavailable,0'){
				$(divThis).replaceWith('Data Unavailable');
			} 
			else {
			new Dygraph(divThis, response, {
				showRoller: true,
				includeZero: true,
				drawPoints: false,
				pointSize: 2,
				strokeWidth: strokeWidth,
				rightGap: 10,
				labelsKMB: labelsKMB,
				colors: colors,
				fillGraph : false,
				yAxisLabelFormatter : formatter,
				highlightCircleSize: 3,
				labelsDiv : $(divThis).attr ("value_div")
				
			});
			}
		}
		error = function (response, status){
			$(divThis).replaceWith('Data unavailable');
		}
		
		// create an ajax call that will trigger the closure with the values that come from the get. 
		//points = $.get (url, {}, func, "text");
		$.ajax({
			  url: url,
			  data: {},
			  success: success,
			  error: error,
			  dataType: "text"
		});

	});
	};
	
	funcUpdate();

});
