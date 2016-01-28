//a brutal cut and paste from graph.xhtml
//it has to be refornmatted to work and included in the page


function addBookmark(){

	var url= location.href; 
	bookmarkurl = url;
	bookmarktitle="Developer Snippets";
	if (document.all)
		window.external.AddFavorite(bookmarkurl,bookmarktitle)
		else if ( window.sidebar ) {
			window.sidebar.addPanel(bookmarktitle, bookmarkurl,"");}
}


$(document).ready(function(){
	$("button.bookmark_page").click(function () {
		// e.preventDefault();
		var bookmarkUrl = location.href;
		var bookmarkTitle = "Magellan Graphs";

		if (window.sidebar) { // For Mozilla Firefox Bookmark
			window.sidebar.addPanel(bookmarkTitle, bookmarkUrl,"");
		} else if( window.external || document.all) { // For IE Favorite
			window.external.AddFavorite( bookmarkUrl, bookmarkTitle);
		} else if(window.opera) { // For Opera Browsers
			$("a.jQueryBookmark").attr("href",bookmarkUrl);
			$("a.jQueryBookmark").attr("title",bookmarkTitle);
			$("a.jQueryBookmark").attr("rel","sidebar");
		} else { // for other browsers which does not support
			alert('Your browser does not support this bookmark action');
			return false;
		}
	});
});

