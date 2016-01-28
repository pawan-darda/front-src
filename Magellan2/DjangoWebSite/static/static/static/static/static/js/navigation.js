$(document).ready(function(){
    $('#set_button').buttonset();
    
    $('.navigation-inputs input').click(function (e){                                                     
        window.location=$(this).attr('url');
    });
    
    $('#fullscreen').button({
        icons: {
            primary: 'ui-icon-newwin'
        },
        text: false
    });
    
    $('.pagination_button').click(function (e){
        new_url = setUrlParameter ('page',this.getAttribute('page'));
        window.location=new_url;
    });
    
    if (getAnchorParameter('fs') == 'True'){
        document.getElementById('filter').style.display='none';
        //document.getElementById('header-row').style.display='none';
    }
    else{
        document.getElementById('filter').style.display='block';
        //document.getElementById('header-row').style.display='block'     
    }

    $('#fullscreen').click(function (e){    
        if (getAnchorParameter('fs') == 'True'){
            setAnchorParameter({fs:"False"});
            document.getElementById('filter').style.display='block';
            document.getElementById('header-row').style.display='block';    
        }
        else{
            setAnchorParameter({fs:"True"});
            document.getElementById('filter').style.display='none';
            document.getElementById('header-row').style.display='none';
        }
    });

	jQuery.download = function(url, data, method){
		//url and data options required
		if( url && data ){ 
			//data can be string of parameters or array/object
			data = typeof data == 'string' ? data : jQuery.param(data);
			//split params into form inputs
			var inputs = '';
			jQuery.each(data.split('&'), function(){ 
				var pair = this.split('=');
				inputs+='<input type="hidden" name="'+ pair[0] +'" value="'+ pair[1] +'" />'; 
			});
			//send request
			jQuery('<form action="'+ url +'" method="'+ (method||'post') +'">'+inputs+'</form>')
			.appendTo('body').submit().remove();
		};
	};

});

function decorate_pagination_buttons(pagination_id){
	$(pagination_id).find( ".next_page").button({
        icons: {
            primary: 'ui-icon-seek-next'
        },
        text: false
    });    
	$(pagination_id).find('.previous_page').button({
        icons: {
            primary: 'ui-icon-seek-prev'
        },
        text: false
    });
	$(pagination_id).find('.last_page').button({
        icons: {
            primary: 'ui-icon-seek-end'
        },
        text: false
    });
	$(pagination_id).find('.first_page').button({
        icons: {
            primary: 'ui-icon-seek-first'
        },
        text: false
    });
    
    try{
        p_button = $(pagination_id).find('#move_previous')
    	prev_val = p_button[0].getAttribute('page') 
    }
    catch (err){
        prev_val = 'Not Available' 
    }
    try{
    	n_button = $(pagination_id).find('#move_next')
        next_val = n_button[0].getAttribute('page')
    }
    catch (err){
        next_val = 'Not Available'
    }
    
    if (prev_val == 'Not Available' && next_val == 'Not Available'){
      $(pagination_id).css('display','none');
    }
    if (next_val == 'Not Available'){
        $(pagination_id).find('.next_page').button({ disabled: true });
       	$(pagination_id).find( '.last_page' ).button({ disabled: true });
    }
    if (prev_val == 'Not Available'){
        $(pagination_id).find( '.previous_page' ).button({ disabled: true });
        $(pagination_id).find( '.first_page' ).button({ disabled: true });
    }
}