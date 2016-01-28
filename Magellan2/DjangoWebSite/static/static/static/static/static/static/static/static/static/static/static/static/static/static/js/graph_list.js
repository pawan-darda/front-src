$(document).ready(function() {
	$(".tabs_versions").tabs();
	$("span.ver_header").mbFlipText(false);
	$(".shortcut").mouseenter(function() { $(this).addClass('ui-state-hover');})
	$(".shortcut").mouseleave(function() { $(this).removeClass("ui-state-hover");})
});