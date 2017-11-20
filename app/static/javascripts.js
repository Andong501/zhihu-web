$(function(){
	$('.vote-btn').click(function(){
		var votebtn = $(this);
		var votenum = votebtn.next();
		var data = {
			'id': votebtn.prop('id')
		};
	$.ajax({
			type: 'POST',
			url: '/vote_or_cancel',
			data: data,
			success: function(data){
				if(data=='vote'){
					votebtn.children().text('voted');
					votebtn.children().css('background-color', '#191970');
					votenum.text(Number(votenum.text()) + 1);
				}else if(data=='cancel'){
					votebtn.children().text('vote it');
					votebtn.children().css('background-color', '#428bca');
					votenum.text(Number(votenum.text()) - 1);
				}else if(data.status==302){
					location.href = data.location;
				}
			}
		});
	});


	$('.focus-btn').click(function(){
		var focusbtn = $(this);
		var focusnum = focusbtn.next();
		var data = {
			'id': focusbtn.prop('id')
		};
	$.ajax({
			type: 'POST',
			url: '/focus_or_cancel',
			data: data,
			success: function(data){
				if(data=='focus'){
					focusbtn.children().text('focused');
					focusbtn.children().css('background-color', '#191970');
					focusnum.text(Number(focusnum.text()) + 1);
				}else if(data=='cancel'){
					focusbtn.children().text('focus it');
					focusbtn.children().css('background-color', '#428bca');
					focusnum.text(Number(focusnum.text()) - 1);
				}else if(data.status==302){
					location.href = data.location
				}
			}
		});
	});


	$('.answer-btn').click(function(){
		$('.answer-form').slideToggle('slow');
	});
});