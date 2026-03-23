
/**
 * 
 */
var completedialog;
var validator;
var errorTemplate = '<div class="k-widget k-tooltip k-tooltip-validation"' +
'style="margin:0.5em"><span class="k-icon k-warning"> </span>' +
'#=message#<div class="k-callout k-callout-n"></div></div>';

var stompClient = null;

var rowNumber = 0;
var fileupload_dialog = null;
var fileupload_progressbar = null;

$(document).ready(function(){
	$(".print-btn").on("click", function(){ 
		print_btn();
	});
	labelingValidate();
	kendo.culture("ko-KR");
	
	init_input_restrict();
	init_screenWidth();
	
	validInputDiv();
	inputAndBtn();
	
	//a tag 클릭 이벤트 
	$(document).off().on('click','.di_click_evt',function(o){
		if($(this).data('url'))
			location.href = $(this).data('url'); 
		
		if($(this).data('func')){ 
			var fn = window[$(this).data('func')];
			if(typeof fn === 'function') {
			    fn(this);
			}
		}
	});
	
	//a tag 클릭 이벤트 
	$(document).on('change','.di_change_evt',function(o){
		
		if($(this).data('func')){
			var fn = window[$(this).data('func')];
			if(typeof fn === 'function') {
			    fn(this);
			}
		}
	})
	
	
	//a tag 클릭 이벤트 
	$(document).on('keyup','.confirm input',function(e){
//		
		if(e.keyCode == 13){
			var $target = $(this).parents('.confirm').find('.src_bnt a')

			$target.trigger('click');
		}
		
	})
	changeStatColor($('.content'));
	/*
	$('.k-datepicker').find('input').attr("disabled", true);
	$("a[href$='#'").on('click', function(){
		$('.k-datepicker').find('input').attr("disabled", false);
	});
	*/
	$("input[type=text][class=w40]").attr("maxlength","40");
	connect();
	
	 $('body').append('<div id="__fileupload_dialog__" title="File Download" style="display:none;">' +
			    '<div class="progress-label">Starting upload...</div>' +
			    '<div id="__progressbar__"></div>' +
			    '</div>');
	 fileupload_progressbar = $( "#__progressbar__" ),
	  fileupload_dialog = $( "#__fileupload_dialog__" ).dialog({
	        autoOpen: false,
	        closeOnEscape: false,
	        resizable: false,
	        open: function() {            		          
	        },
	        beforeClose: function() {
	          
	        }
	      })
	  fileupload_dialog.dialog( "close" );
	 fileupload_progressbar.progressbar({
       value: false,
       change: function() {
         $(".progress-label").text( "Current Progress: " + fileupload_progressbar.progressbar( "value" ) + "%" );
         fileupload_dialog.dialog( "open" );
       },
       complete: function() {
    	   fileupload_dialog.dialog( "close" );
     	 // $('#__fileupload_dialog__').remove();
     	  $('#__fileupload_dialog__').dialog('destroy')
       }
     });
	
	//$("form").attr("onsubmit","return false;");
});


$.fn.clearForm = function () {
	  return this.each(function () {
	    var type = this.type,
	      tag = this.tagName.toLowerCase();
	    if (tag === "form") {
	      return $(":input", this).clearForm();
	    }
	    if (
	      type === "text" ||
	      type === "password" ||
	      type === "hidden" ||
	      tag === "textarea" || 
	      tag === "file"
	    ) {
	      this.value = "";
	    } else if (tag === "select") {
	      this.selectedIndex = -1;
	    }
	  });
};



function init_enterKeyPress(inputIdName,keyPressfuncName)
{ 
	$("#"+inputIdName).on("keydown",function(key){
		if(key.keyCode==13) {
			keyPressfuncName();
			key.preventDefault();//form내 submit방지
			return;
		}
	});
}

function leftWait()
{
	Swal.fire({
		text: '서비스 준비 중입니다.',
		icon:'warning',
		confirmButtonText: '확인'
	});
}

// 글자수 체크 
function getTextLength(str){
	 var len = 0;
    for (var i = 0; i < str.length; i++) {
        if (escape(str.charAt(i)).length == 6) {
            len++;
        }
        len++;
    }
    return len;
}

// 사업자 등록 번호 정규식
function checkCorporateRegiNumber(number){
	var numberMap = number.replace(/-/gi, '').split('').map(function (d){
		return parseInt(d, 10);
	});
	
	if(numberMap.length == 10){
		var keyArr = [1, 3, 7, 1, 3, 7, 1, 3, 5];
		var chk = 0;
		
		keyArr.forEach(function(d, i){
			chk += d * numberMap[i];
		});
		
		chk += parseInt((keyArr[8] * numberMap[8])/ 10, 10);
		console.log(chk);
		return Math.floor(numberMap[9]) === ( (10 - (chk % 10) ) % 10);
	}
	
	return false;
}

function sidebar_Show()
{
	$(".row > .w200p").toggle();
	
	if( $(".row > .w200p").css("display") == "block")
	{
		$(".row > .w200p").css("height","100%");
		$(".row > .w200p").css("display","block");
		$(".row > .w200p").css("position","absolute"); 
		$(".row > .w200p").css("z-index","1000"); 
	}
	
}

function init_screenWidth()  
{
	if(screen.width > 2000 )
	{
		console.log("tv", screen.width);      
	}
	else if(screen.width < 1280 )     
	{ 
		$(".right-body").removeClass('w325p');   
		$(".right-body").addClass('w10p');   
		$(".appro-content").css("display","none");
		$(".sidebar-content").css("display","none");

		console.log("태블릿", screen.width);   
	}   
	else
	{
		$(".appro-content").css("display","block");
		$(".sidebar-content").css("display","block");
		console.log("pc", screen.width);
	}
}

// 설계 수행 tree
function unflatten(arr) {
    var tree = [],
        mappedArr = {},
        arrElem,
        mappedElem;

    var index = 0;
    
    // First map the nodes of the array to an object -> create a hash table.
    for(var i = 0, len = arr.length; i < len; i++) {
      	arrElem = arr[i];
      	var parent = {};

      	if( arrElem.parentId == null)
      	{
      		parent.expanded = true;
      		parent.id = index++;
      		parent.parentId = null;
      		parent.extraCnt = 1;
      		parent.registDt = null;
      		parent.se = arrElem.se;
      		parent.count = arrElem.count;
      		parent.seq = arrElem.seq;
      		parent.suiteSeq = arrElem.seq;
      		parent.suiteId = arrElem.id;
      		parent.nm = arrElem.nm;
      		parent.countChild = 0;
      		parent.registerNo = "";
	      	mappedArr[arrElem.seq] = parent;
	      	mappedArr[arrElem.seq]['items'] = [];	    
	      	tree.push(parent);    	
        }
      	else
      	{
      		var pElem = mappedArr[arrElem.parentId];
       		if( pElem == null )
          		continue;
      		
      		pElem.countChild += 1;
      		arrElem.expanded = true;
      		arrElem.id = index++;
      		arrElem.parentId = pElem.suiteSeq; 
      		mappedArr[arrElem.parentId]['items'].push(arrElem);
 
      	}	
      	
      	arrElem.expanded = true;
    }

    console.log("tree", tree);
    return tree;
}


var agenttop = navigator.userAgent.toLowerCase();

function appCustomAsyncAjax(url, param, success, option )
{
	Swal.fire({
		  title: '', 
		  html: option.html == null?"진행하시겠습니까?":option.html,
		  icon: option.icon == null?"warning":option.icon,
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						titleMsg = option.comMsg==null?"저장완료":option.comMsg;
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
							return;
						}
						if(e.responseJSON == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
									  
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
						else if(e.responseJSON.error == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
					}
			    });
		  }
	});
}


function appNewSaveAsyncAjax(url, param, success, error, option,text, comMsg )
{
	var textMsg= "진행하시겠습니까?";
	var titleMsg = "저장 완료";
	
	if(text){
		textMsg= text;
	}
	
	Swal.fire({
		  title: '', 
		  html: textMsg,
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(comMsg){
							titleMsg = comMsg;
						}
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
							return;
						}
						if(e.responseJSON == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
									  
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
						else if(e.responseJSON.error == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
					}
			    });
		  }
		});
}


function appSaveAsyncAjax(url, param, success, error, option,text, comMsg )
{
	
	var textMsg= "진행하시겠습니까?";
	var titleMsg = "저장 완료";
	
	if(text){
		textMsg= text;
	}
	
	Swal.fire({
		  title: '',
		  text: textMsg,
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(comMsg){
							titleMsg = comMsg;
						}
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
							return;
						}
						if(e.responseJSON == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  confirmButtonText: '확인', //스마트검사실 저장완료 확인버튼 수정
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
									  
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
						else if(e.responseJSON.error == null)
						{
							Swal.fire({
								  title:titleMsg,
								  text:'',
								  confirmButtonText: '확인',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
					}
			    });
		  }
		});
}

function appJoinAsyncAjax(url, param, success, error, option,text)
{
	var textMsg= "진행하시겠습니까?";
	
	if(text){
		textMsg= text;
	}
	Swal.fire({
		  title: '',
		  text: textMsg,
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
							return;
						}
						if(e.responseJSON == null)
						{
							Swal.fire({
								  title:'가입 완료',
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
									  
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
						else if(e.responseJSON.error == null)
						{
							Swal.fire({
								  title:'가입 완료',
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
					}
			    });
		  }
		});
}

function appSaveFileAsyncAjax(url, param, success, error, option,text)
{
	
	var textMsg= "진행하시겠습니까?";
	
	
	if(text){
		textMsg= text;
	}
	Swal.fire({
		  title: '',
		  text: textMsg,
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
							return;
						}
						if(e.responseJSON == null)
						{
							Swal.fire({
								  title:'저장 완료',
								  text:'',
								  icon:'success',
								  onClose:function(){
									  if($(".swal2-backdrop-hide")!=null)
										  $(".swal2-backdrop-hide").remove();
									  //if(param.get("tgturl") != null)
									  console.log(agenttop);
									  if(option != null)
									  {
										  if(option.tgturl != null)
										  {
											  if(option.param != null)
											  {
												  $.redirect(option.tgturl,
														  option.param);
											  }
											  else
												  location.href = option.tgturl;  
										  }  
									  }
									  
								  }
							});
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
						else if(e.responseJSON.error == null)
						{
							if(e.responseJSON.result == 'fail')
							{
								Swal.fire({
									title:'',
									html:'파일에서 정보를 읽을 수 없습니다. <br>첨부파일을 다시 확인해주세요.',
									icon:'warning',
									onClose:function(){
										if($(".swal2-backdrop-hide")!=null)
											$(".swal2-backdrop-hide").remove();
										//if(param.get("tgturl") != null)
										console.log(agenttop);
									}
								});
							}
							else
							{
								Swal.fire({
									title:'저장 완료',
									text:'',
									icon:'success',
									onClose:function(){
										if($(".swal2-backdrop-hide")!=null)
											$(".swal2-backdrop-hide").remove();
										//if(param.get("tgturl") != null)
										console.log(agenttop);
										if(option != null)
										{
											if(option.tgturl != null)
											{
												if(option.param != null)
												{
													$.redirect(option.tgturl,
															option.param);
												}
												else
													location.href = option.tgturl;  
											}  
										}
									}
								});
							}
							
							$("body").removeClass("swal2-height-auto");
							$("body").css("overflow", "auto");
						}
					}
			    });
		  }
		});
}

function appApproveAsyncAjax(url, param, success, option)
{
	Swal.fire({
		  title: '',
		  text: "진행하시겠습니까?",
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);     
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							return;
						}
						
						Swal.fire(
								{
									  title:'승인 완료',
									  text:'',
									  icon:'success',
									  onClose: function() {
										  if($(".swal2-backdrop-hide")!=null)
											  $(".swal2-backdrop-hide").remove();
										  //if(param.get("tgturl") != null)
										  if (true) {
											  if(option!=null&&option.tgturl != null)
											  {
												  location.href = option.tgturl;
											  }
										  }		
									  }
								}
						);
						$("body").removeClass("swal2-height-auto");
					}
			    });
		  }
		});  
	
}


function appRejectAsyncAjax(url, param, success, option)
{
	Swal.fire({
		  title: '',
		  text: "진행하시겠습니까?",
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
		  if (result.value) {
			  if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);     
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							return;
						}
						
						Swal.fire(
								{
									  title:'반려 완료',
									  text:'',
									  icon:'success',
									  onClose: function() {
										  if($(".swal2-backdrop-hide")!=null)
											  $(".swal2-backdrop-hide").remove();
										  //if(param.get("tgturl") != null)
										  if (true) {
											  if(option!=null&&option.tgturl != null)
											  {
												  location.href = option.tgturl;
											  }
										  }		
									  }
								}
						);
						$("body").removeClass("swal2-height-auto");
					}
			    });  
		  }
	});
	
}

function appUpdateAsyncAjax(url, param, success, option)
{
	if(option!=null&&option.tgtdoc != null)
		kendo.ui.progress(option.tgtdoc, true);
	$.ajax({
        type: "POST",
        beforeSend:function(xhr) {
        	xhr.setRequestHeader("AJAX", true);
        },
        //enctype: 'multipart/form-data',
        url: url,
        data: param,
        processData: false,
        contentType: false,
        cache: false,
        timeout: 600000,
        success: success,
        crossOrigin: true, 
        error: function (e) {
            console.log("ERROR : ", e);     
            Swal.fire(
            	{
            	title:'Error',
            	icon:'error',
            	html:e.responseText,
            	width: '800px'
            	}
			);
        },
		complete: function(e){
			if(option!=null&&option.tgtdoc != null)
				kendo.ui.progress(option.tgtdoc, false);
			if(e.status == 500)
			{
				$("body").removeClass("swal2-height-auto");
				return;
			}
			
			Swal.fire({
				  title:'수정 완료',
				  text:'',
				  icon:'success',
				  onClose: function() {
					  if($(".swal2-backdrop-hide")!=null)
						  $(".swal2-backdrop-hide").remove();
					  //if(param.get("tgturl") != null)
						  if(option!=null&&option.tgturl != null)
						  {
							  location.href = option.tgturl
						  }
				  }
			});
		}
    });
}

function appConfirmAsyncAjax(url, param, success, option)
{
	if(option!=null&&option.tgtdoc != null)
		kendo.ui.progress(option.tgtdoc, true);
	$.ajax({
        type: "POST",
        //enctype: 'multipart/form-data',
        beforeSend:function(xhr) {
        	xhr.setRequestHeader("AJAX", true);
        },
        url: url,
        data: param,
        processData: false,
        contentType: false,
        cache: false,
        timeout: 600000,
        success: success,
        crossOrigin: true, 
        error: function (e) {
            console.log("ERROR : ", e);     
            Swal.fire(
            	{
            	title:'Error',
            	icon:'error',
            	html:e.responseText,
            	width: '800px'
            	}
			);
        },
		complete: function(e){
			if(option!=null&&option.tgtdoc != null)
				kendo.ui.progress(option.tgtdoc, false);
			
			if(e.status == 500)
			{
				$("body").removeClass("swal2-height-auto");
				return;
			}
			
			if($(".swal2-backdrop-hide")!=null)
				  $(".swal2-backdrop-hide").remove();
			
			Swal.fire(
					  '확정 완료',
					  '',
					  'success'
			);
		}
    });
}

function appDeleteAsyncAjax(url, param, success, error, option,text)
{
	Swal.fire({
		  title: '',
		  html: option!=null&&option.userMsg!=null?option.userMsg:"삭제하시겠습니까?",
		  icon: 'warning',
		  showCancelButton: true,
		  confirmButtonColor: '#3085d6',
		  cancelButtonColor: '#d33',
		  confirmButtonText: '네',
		  cancelButtonText: '아니오'
		}).then( function (result) {
			if (result.value) {
				if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);
				
				$.ajax({
			        type: "POST",
			        //enctype: 'multipart/form-data',
			        beforeSend:function(xhr) {
			        	xhr.setRequestHeader("AJAX", true);
			        },
			        url: url,
			        data: param,
			        processData: false,
			        contentType: false,
			        cache: false,
			        timeout: 600000,
			        success: success,
			        crossOrigin: true, 
			        error: function (e) {
			            console.log("ERROR : ", e);    
			            Swal.fire(
			            	{
			            	title:'Error',
			            	icon:'error',
			            	html:e.responseText,
			            	width: '800px'
			            	}
						);  
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							return;
						}
						
						Swal.fire({
							  title : option!=null&&option.userCmpltMsg!=null?option.userCmpltMsg:'삭제 완료',
							  text :'',
							  icon :'success',
							  onClose: function() {
								  if($(".swal2-backdrop-hide")!=null)
									  $(".swal2-backdrop-hide").remove();
								  //if(param.get("tgturl") != null)
								  if (true) {
									  if(option!=null&&option.tgturl != null)
									  {
										  location.href = option.tgturl;
									  }
								  }		
							  }
						});
						$("body").removeClass("swal2-height-auto");
					}
			    });
			}
		});
}

function appWithdrawAsyncAjax(url, param, success, error, option)
{
	Swal.fire({
		title: '',
		html: option!=null&&option.userMsg!=null?option.userMsg:"탈퇴하시겠습니까?",
		icon: 'warning',
		showCancelButton: true,
		confirmButtonColor: '#3085d6',
		cancelButtonColor: '#d33',
		confirmButtonText: '네',
		cancelButtonText: '아니오'
	}).then( function (result) {
			if (result.value) {
				if(option!=null&&option.tgtdoc != null)
					kendo.ui.progress(option.tgtdoc, true);

				$.ajax({
					type: "POST",
					//enctype: 'multipart/form-data',
					beforeSend:function(xhr) {
						xhr.setRequestHeader("AJAX", true);
					},
					url: url,
					data: param,
					processData: false,
					contentType: false,
					cache: false,
					timeout: 600000,
					success: success,
					crossOrigin: true, 
					error: function (e) {
						console.log("ERROR : ", e);    
						Swal.fire(
							{
							title:'Error',
							icon:'error',
							html:e.responseText,
							width: '800px'
							}
						);  
			        },
					complete: function(e){
						if(option!=null&&option.tgtdoc != null)
							kendo.ui.progress(option.tgtdoc, false);
						if(e.status == 500)
						{
							$("body").removeClass("swal2-height-auto");
							return;
						}
						
						Swal.fire({
							title : option!=null&&option.userCmpltMsg!=null?option.userCmpltMsg:'탈퇴 완료',
							text :'',
							icon :'success',
							onClose: function() {
								if($(".swal2-backdrop-hide")!=null)
									$(".swal2-backdrop-hide").remove();
								//if(param.get("tgturl") != null)
								if (true) {
									if(option!=null&&option.tgturl != null)
									{
										location.href = option.tgturl;
									}
								}		
							}
						});
						$("body").removeClass("swal2-height-auto");
					}
				});
			}
		});
}

//퍼센티지를 업데이트하는 함수 예제
function showProgress() {
  var progress = 0;
  var progressBar = document.querySelector('.progress-bar');
  var interval = setInterval(() => {
    progress++;
    progressBar.style.width = progress + '%';
    if (progress === 100) {
      clearInterval(interval);
    }
  }, 30);
}

function appLoadAsyncAjax(url, param, success, option, filetarget)
{
	var asyncOpt = true;
	
	if(option!=null&&option.tgtdoc != null)
		kendo.ui.progress(option.tgtdoc, true);
	if(option!=null&&option.async != null)
		asyncOpt = option.async;
	
	
	
	$.ajax({
        type: "POST",
        //enctype: 'multipart/form-data',
        beforeSend:function(xhr) {
        	xhr.setRequestHeader("AJAX", true);
        },
        url: url,
        data: param,
        filetarget: filetarget,
        processData: false,
        contentType: false,
 		async: asyncOpt,
        cache: false,
        timeout: 600000,
        success: success,
        crossOrigin: true, 
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            
            // 업로드 진행 상황을 추적하는 이벤트 핸들러
            xhr.upload.addEventListener('progress', function(event) {
              if (event.lengthComputable) {
            	  
            	    
                var percentComplete = (event.loaded / event.total) * 100;
                
                if( event.total > 1000000 )
                {
                	if (!Swal.isVisible()) {
	                	Swal.fire({
	                		  title: '파일 업로드...',
	                		  html: '<div class="progress-area"><div class="progress-bar"></div><div class="progress-val"></div></div>',
	                		  allowOutsideClick: false,
	                		  allowEscapeKey: true,
	                		  showCancelButton: false, // 취소 버튼 숨김
	                		  showConfirmButton: false, // 확인 버튼 숨김
	                		  onBeforeOpen: () => {
	                		    //Swal.showLoading();
	                		    //showProgress();
	                		  }
	                		});
                	}
                	
                	$('.progress-bar').css('width', percentComplete + '%');
                    $('.progress-val').text(percentComplete.toFixed(1) + '%'); // + "(" + event.loaded/1000000 + "mb/" + event.total/1000000 + "mb)")
                    
                    //if(fileupload_progressbar != null)
                    //	fileupload_progressbar.progressbar( "value",  percentComplete.toFixed(0));
                }
                /*
                else
                {
                	if (!Swal.isVisible()) {
	                	Swal.fire({
	                		  title: '로딩 중',
	                		  allowOutsideClick: false,
	                		  allowEscapeKey: false,
	                		  onBeforeOpen: () => {
	                		    Swal.showLoading();
	                		    //showProgress();
	                		  }
	                		});
                	}
                }
                */
                
              }
            }, false);
            
            return xhr;
        },
        error: function (e) {
        	Swal.fire(
            	{
            	title:'Error',
            	icon:'error',
            	html:e.responseText,
            	width: '800px'
            	}
			);    
        	//debugger;
        	if($("#__fileupload_dialog__").length > 0)
            {
				//$("#__fileupload_dialog__").remove();
				 //$('#__fileupload_dialog__').dialog('destroy').remove()
            }
        },
		complete: function(e){
			//debugger;
			if (Swal.isVisible()) {
				if( Swal.getTitle().innerHTML.indexOf("파일 업로드...") > -1 )
					Swal.close();
			}
			if($("#__fileupload_dialog__").length > 0)
            {
				//$("#__fileupload_dialog__").remove();
				 //$('#__fileupload_dialog__').dialog('destroy').remove()
            }
			if(option!=null&&option.tgtdoc != null)
				kendo.ui.progress(option.tgtdoc, false);
			
			
			if(e.status == 500)
			{
				$("body").removeClass("swal2-height-auto");
				return;
			}
			
			if(e.responseText.indexOf("시스템 에러") > -1 && e.responseText != null)
			{
				Swal.fire(
		            	{
		            	title:'Error',
		            	icon:'error',
		            	html:e.responseText,
		            	width: '800px'
		            	}
					);
			}
			
			if(e.responseJSON != null && e.responseJSON.error != null && e.responseJSON.error != "")
			{
				Swal.fire(
		            	{
		            	title:'Error',
		            	icon:'error',
		            	html:e.responseJSON.error,
		            	width: '800px',
		            	confirmButtonText : '확인'
		            	}
					);
			}
			if($(".swal2-backdrop-hide")!=null)
				  $(".swal2-backdrop-hide").remove();
		}
    });
}


function onOK()
{
	console.log("onOk");
}

function appSyncAjax(url, param, success)
{
	var promise = $.ajax({
        type: "POST",
        //enctype: 'multipart/form-data',
        url: url,
        data: param,
        processData: false,
        contentType: false,
        cache: false,
        //async: false,
        timeout: 600000,
        //success: success,
        error: function (e) {
            console.log("ERROR : ", e);            
        }
    });
	
	promise.done(success);
}

/*
function appAsyncJsonAjax(url, param, success)
{

	$.ajax({
        type: "POST",
        //enctype: 'multipart/form-data',
        dataType:"json",
        //jsonp:"callback",
        url: url,
        //data: param,
        //processData: false,
        //contentType: false,
        //cache: false,
        timeout: 600000,
        success: success,
        error: function (e) {
            console.log("ERROR : ", e);            
        }
    });
}
*/

function appAsyncJsonAjax(url, param, success)
{
	$.ajax({
		type: "POST",
		url : url,
		data : param,
		//enctype: 'multipart/form-data',
		contentType : "application/json",
		cache: false,
		dataType : 'json',
		processData:false,
		timeout : 100000,
		success : success,
		error : function(e) {
			Swal.fire(
            	{
            	title:'Error',
            	icon:'error',
            	html:e.responseText,
            	width: '800px'
            	}
			);
		}
	});
}

function print_btn(){
	console.log("출력");
	 var initBody = document.body.innerHTML;
     window.onbeforeprint = function(){
    	 if(document.getElementById('printwrap') == undefined)
    		 return false;
         document.body.innerHTML = document.getElementById('printwrap').innerHTML;
     }
     window.onafterprint = function(){
    	 if(document.getElementById('printwrap') == undefined)
    		 return false;
         document.body.innerHTML = initBody;
     }
     if(document.getElementById('printwrap') == undefined)
		 return false;
     window.print();    
}

function loadValueByCase(object)
{
	for (var key in object) {			    
	    
	    if(key.substr(0,3) == "str" && key.substr(key.length-2,2) == "Dt")
	    {
	    	var datepickerId = key.split("str")[1];
	    	datepickerId = datepickerId.charAt(0).toLowerCase() + datepickerId.slice(1);
	    	var datepicker = $("#"+datepickerId).data("kendoDatePicker")==null?$("#"+datepickerId).data("kendoDateTimePicker"):null;
	    	
	    	if(datepicker != null)
	    		datepicker.value(object[key]);
	    
	    }
	    else if(key.substr(key.length-2,2) == "Dt")
	    {
	    	continue;
	    }
	    else	
	    	$("#"+key).val(object[key]);
	}
}

function loadValueToDiv(object)
{
	for (var key in object) {
		if(key.substr(0,3) == "str" && key.substr(key.length-2,2) == "Dt")
	    {
	    	var datepickerId = key.split("str")[1];
	    	datepickerId = datepickerId.charAt(0).toLowerCase() + datepickerId.slice(1);
	    	
	    	$("#"+datepickerId).text(object[key]);
	    }
	    else if(key.substr(key.length-2,2) == "Dt")
	    {
	    	continue;
	    }
	    else	
	    	$("#"+key).text(object[key]);
	}
}

function fileDownloadAjax(fileId, url)
{
	var formData = new FormData($('#add_chckstdr_form')[0]);
	
	formData.append("param_atchFileId", fileId);    
	appLoadAsyncAjax(filedownurl, formData, fileDownloadSuccess);
} 

function comma(num){
	var len, point, str;  
	  
	num = num + "";  
	point = num.length % 3 ;
	len = num.length;  
  
	str = num.substring(0, point);  
	while (point < len) {  
	    if (str != "") str += ",";  
	    str += num.substring(point, point + 3);  
	    point += 3;  
	}  
	
	return str;

}

function unicodeToKor(str){
	//유니코드 -> 한글
	var retStr = unescape(replaceAll(str, "\\", "%"));
	return replaceAll(retStr, "%\"", "\"");
	
	return ;
}

function replaceAll(strTemp, strValue1, strValue2){ 

    while(1){
        if( strTemp.indexOf(strValue1) != -1 )
            strTemp = strTemp.replace(strValue1, strValue2);
        else
            break;
    }
    return strTemp;

}

Date.prototype.format = function(f) {
    if (!this.valueOf()) return " ";
 
    var weekName = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
    var d = this;
     
    return f.replace(/(yyyy|yy|MM|dd|E|hh|mm|ss|a\/p)/gi, function($1) {
        switch ($1) {
            case "yyyy": return d.getFullYear();
            case "yy": return (d.getFullYear() % 1000).zf(2);
            case "MM": return (d.getMonth() + 1).zf(2);
            case "dd": return d.getDate().zf(2);
            case "E": return weekName[d.getDay()];
            case "HH": return d.getHours().zf(2);
            case "hh": return ((h = d.getHours() % 12) ? h : 12).zf(2);
            case "mm": return d.getMinutes().zf(2);
            case "ss": return d.getSeconds().zf(2);
            case "a/p": return d.getHours() < 12 ? "오전" : "오후";
            default: return $1;
        }
    });
};
 
function getShipTyByCode(code)
{
	return code=="0001"?"화물선":
		code=="0001"?"여객선":
		code=="0001"?"캐미컬운반선":
		code=="0001"?"유조선":
		code=="0001"?"예/분석":
		code=="0001"?"석유제품운반선":
		code=="0001"?"LNG":
		code=="0001"?"자동차운반선":
		code=="0001"?"컨테이너선":
		code=="0001"?"벌크선":
		code=="0001"?"모래운반선":
		code=="0001"?"어선":"기타";
}
String.prototype.string = function(len){var s = '', i = 0; while (i++ < len) { s += this; } return s;};
String.prototype.zf = function(len){return "0".string(len - this.length) + this;};
Number.prototype.zf = function(len){return this.toString().zf(len);};

var RgbaColorCollect = ["rgba(99,137,223,0.7)","rgba(210,215,219,0.7)","rgba(255,159,175,0.7)","rgba(164,213,166,0.7)",
		"rgba(109,163,190,0.7)","rgba(252,214,164,0.7)","rgba(230,174,133,0.7)",
		"rgba(167,191,208,0.7)","rgba(0,107,235,0.7)","rgba(157,205,191,0.7)",
		"rgba(192,154,153,0.7)","rgba(241,207,201,0.7)","rgba(196,205,133,0.7)"];

var CHCKTYPE = {CHCKDAY:0x1, CHCKMON:0x2, CHCKRAW:0x04, CHCKFULL:0x08, CHCKEMER:0x16, CHCKETC:0x32};

Date.prototype.toLocalISOString = function(){
	// ISO 8601
	var d = this
		, pad = function (n){return n<10 ? '0'+n : n}
		, tz = d.getTimezoneOffset() //mins
		, tzs = (tz>0?"-":"+") + pad(parseInt(tz/60))
	
	if (tz%60 != 0)
		tzs += pad(tz%60)
	
	if (tz === 0) // Zulu time == UTC
		tzs = 'Z'
		
	 return d.getFullYear()+'-'
	      + pad(d.getMonth()+1)+'-'
	      + pad(d.getDate())+'T'
	      + pad(d.getHours())+':'
	      + pad(d.getMinutes())+':'
	      + pad(d.getSeconds())
}

Date.prototype.subtractDays = function(d) {  
    this.setTime(this.getTime() - (d*24*60*60*1000));  
    return this;  
}

Date.prototype.getDateTime = function() {
	return this.toLocalISOString().split("T")[0] + " " +this.toLocalISOString().split("T")[1]; 
}

Date.prototype.getYMDHM = function(suggestHM) {
	// 날짜 및 시간을 원하는 형식으로 포맷팅
	// 10 미만의 숫자를 두 자리로 만들기 위한 보조 함수
	function padZero(number) {
	  return (number < 10 ? '0' : '') + number;
	}
	
	var formattedDate = "";
	if( suggestHM == null)
	{
		formattedDate = this.getFullYear() + '-' +
                      padZero(this.getMonth() + 1) + '-' +
                      padZero(this.getDate()) + ' ' +
                      padZero(this.getHours()) + ':' +
                      padZero(this.getMinutes());
	}
	else
	{
		formattedDate = this.getFullYear() + '-' +
			        padZero(this.getMonth() + 1) + '-' +
			        padZero(this.getDate()) + ' ' + suggestHM;
	}
	return formattedDate; 
}

Date.prototype.getDateTime2 = function() {
	return this.toLocalISOString().split("T")[0]; 
}

Date.prototype.getTimeOnly = function() {
	return this.toLocalISOString().split("T")[1]; 
}

Date.prototype.getTimeFormat = function(){
	return this.toTimeString().split(":")[0] + ":" + this.toTimeString().split(":")[1];
}


function getDateFormat(beginDt, endDt)
{
	var date = null;
	var beginDe = new Date(beginDt).getDateTime2();
	var beginTime = new Date(beginDt).toTimeString().split(":")[0] + ":" + new Date(beginDt).toTimeString().split(":")[1];
	
	if(endDt != null)	
	{
		var endDe = new Date(endDt).getDateTime2();
		var endTime = new Date(endDt).toTimeString().split(":")[0] + ":" + new Date(endDt).toTimeString().split(":")[1];
		
		date = beginDe + " " + beginTime + " ~ " + endDe + " " + endTime;
	}
	else
		date = beginDe + " " + beginTime;
	
	return date;
}

function tempLink(url)
{
	location.href = url;
}


var drawing = kendo.drawing;
var geometry = kendo.geometry;


function createColumn(rect, color) {
    var origin = rect.origin;
    var center = rect.center();
    var bottomRight = rect.bottomRight();
    var radiusX = rect.width() / 2;
    var radiusY = radiusX / 3;
    var gradient = new drawing.LinearGradient({
        stops: [{
            offset: 0,
            color: color
        }, {
            offset: 0.5,
            color: color,
            opacity: 0.9
        }, {
            offset: 0.5,
            color: color,
            opacity: 0.9
        }, {
            offset: 1,
            color: color
        }]
    });

    var path = new drawing.Path({
            fill: gradient,
            stroke: {
                color: "none"
            }
        }).moveTo(origin.x, origin.y)
        .lineTo(origin.x, bottomRight.y)
        .arc(180, 0, radiusX, radiusY, true)
        .lineTo(bottomRight.x, origin.y)
        .arc(0, 180, radiusX, radiusY);

    var topArcGeometry = new geometry.Arc([center.x, origin.y], {
        startAngle: 0,
        endAngle: 360,
        radiusX: radiusX,
        radiusY: radiusY                
    });

    var topArc = new drawing.Arc(topArcGeometry, {
        fill: {
            color: color
        },
        stroke: {
            color: "#ebebeb"
        }
    });
    var group = new drawing.Group();
    group.append(path, topArc);
    return group;
}

function createLegendItem(e) {
    var color = e.options.markers.background;
    var labelColor = e.options.labels.color;
    var rect = new geometry.Rect([0, 0], [120, 50]);
    var layout = new drawing.Layout(rect, {
        spacing: 5,
        alignItems: "center"
    });

    var overlay = drawing.Path.fromRect(rect, {
        fill: {
            color: "#fff",
            opacity: 0
        },
        stroke: {
            color: "none"
        },
        cursor: "pointer"
    });

    var column = createColumn(new geometry.Rect([0, 0], [15, 10]), color);
    var label = new drawing.Text(e.series.name, [0, 0], {
        fill: {
            color: labelColor
        }
    })

    layout.append(column, label);
    layout.reflow();

    var group = new drawing.Group().append(layout, overlay);

    return group;
}
function fnMaxlength(obj){
	  var maxLength = parseInt(obj.getAttribute("maxlength"));
	  //console.log(maxLength);
	  //console.log(obj.value.length);
	  if ( obj.value.length >= maxLength ) {
		  Swal.fire(
	            	{
	            	title:'Error',
	            	icon:'error',
	            	html: "입력 범위를 초과했습니다.",
	            	width: '800px'
	            	}
				);
	  }
}
function labelingValidate(){
	 var mask = '<em class="red requiredCheck">*</em>'; 
	 
	 $('input[type="text"],input[type="radio"],checkbox, select,textarea').each(function(i,o){
		if($(o).attr('required')){
			var id = $(o).attr("id");
			if(!id){
				id = $(o).attr("name");
			}
			if(id){
				if($('label[for="'+id+'"]') && $('label[for="'+id+'"]').find('em.requiredCheck').length <1){
					$('label[for="'+id+'"]').append(mask);	
				}
				
			}
		}  
	 }) 
}
var gridRownum = function(dataItem) {
	var index = 0;
	try {
		if(dataItem)
			index = dataItem.parent().indexOf(dataItem);
	}catch(e){
		alert('데이터 로드에 실패 했습니다. ')
	}
	return index + 1; 
} ;

//getFormData($('#searchForm'),formData);
function getFormData($target, formData){
	$.each($target.serializeObject(),function(key,val){
		
		if(key == 'searchEndDt'){
			val = endDateParse(val);
		} 
		formData.append(key,val);
	})
}
function endDateParse(obj){
	
	var date = new Date(obj);
	date.setDate(date.getDate() + 1);
	
	return date.format('yyyy-MM-dd')
}



function createDatePickerYMD(tgt, endTgt, isAssign)
{
	$(tgt).kendoDatePicker({
        format: "yyyy-MM-dd",
        value:isAssign==null?new Date():new Date(isAssign),
        dateInput:false,
        culture:"ko-KR",
        change:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        }
    });
	
	
}


function createTimePickerHM(tgt, endTgt)
{
	$(tgt).kendoTimePicker({
		format: "HH:mm", 
        value:new Date(),
        dateInput:false,     
        change:function(e){

        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoTimePicker").value();
        		 
        		
        		$(endTgt).data("kendoTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoTimePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoTimePicker").value();
        		
        		$(endTgt).data("kendoTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoTimePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoTimePicker").value();
        		$(endTgt).data("kendoTimePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoTimePicker").value(startDt);
        		
        	}
        }
	});
}

var _previousDateValue = null;
function createDatePickerYMDHM(tgt, endTgt, isAllowedAgo)
{
	$(tgt).kendoDateTimePicker({
        format: "yyyy-MM-dd HH:mm", 
        value:new Date(),
        dateInput:false,
        open:function(e) {
        	console.log(e)
        	_previousDateValue = e.sender._old
        },
        change:function(e){
        	

        	if( isAllowedAgo != null && isAllowedAgo == false)
        	{
        		if( new Date().getDateTime2() > e.sender._old.getDateTime2())
        		{
        			e.preventDefault();
        			e.sender.value(_previousDateValue);
        			console.log(e.sender.value);
            		
            		return;
        		}
        		
        		
        	}
        	
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		 
        		
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        }
    });	
}

function createEndDatePickerYMDHM(startTgt, endTgt, isAllowedAgo)
{
	$(endTgt).kendoDateTimePicker({
        format: "yyyy-MM-dd HH:mm", 
        value:new Date(),
        dateInput:false,     
        open:function(e) {
        	console.log(e)
        	_previousDateValue = e.sender._old
        },
        change:function(e){
        	if( isAllowedAgo != null && isAllowedAgo == false)
        	{
        		if( new Date().getDateTime2() > e.sender._old.getDateTime2())
        		{
        			e.preventDefault();
        			e.sender.value(_previousDateValue);
        			console.log(e.sender.value);
        			return;
        		}
        		
        		
        		
        		
        	}
        	
        	if(startTgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(startTgt).data("kendoDateTimePicker").value();
        		 
        		
        		$(startTgt).data("kendoDateTimePicker").max(endDt);
        		
        		if(endDt < startDt)
        			$(startTgt).data("kendoDateTimePicker").value(endTgt);
        		
        	}
        },
        databinding:function(e){
        	if(startTgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(startTgt).data("kendoDateTimePicker").value();
        		 
        		
        		$(startTgt).data("kendoDateTimePicker").max(endDt);
        		
        		if(endDt < startDt)
        			$(startTgt).data("kendoDateTimePicker").value(endTgt);
        		
        	}
        },
        databound:function(e){
        	if(startTgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(startTgt).data("kendoDateTimePicker").value();
        		 
        		
        		$(startTgt).data("kendoDateTimePicker").max(endDt);
        		
        		if(endDt < startDt)
        			$(startTgt).data("kendoDateTimePicker").value(endTgt);
        		
        	}
        }
    });	
}


function createDatePickerYMDHMS(tgt, endTgt)
{
	$(tgt).kendoDateTimePicker({
        format: "yyyy-MM-dd HH:mm:ss", 
        value:new Date(),
        dateInput:false,     
        change:function(e){
        	
        	
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		 
        		
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDateTimePicker").value();
        		$(endTgt).data("kendoDateTimePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoDateTimePicker").value(startDt);
        		
        	}
        }
    });	
}


function init_input_restrict()
{
	if($(".numeric").length > 0)
		$(".numeric").numeric();
	if($(".alphanum").length > 0)
		$(".alphanum").alphanum();
	if($(".alpha").length > 0)
		$(".alpha").alpha();
	if($(".korean").length > 0)
	{
		$(".korean").on('keypress', function (event) {
			var pattern = /[a-z0-9]|[ \[\]{}()<>?|`~!@#$%^&*-_+=,.;:\"'\\]/g;
			  this.value = this.value.replace(pattern, '');
		});
	}
	if($(".nokorean").length > 0)
	{
		 $(".nokorean").keyup(function(event){
             if (!(event.keyCode >=37 && event.keyCode<=40)) {
                 var inputVal = $(this).val();
                 //$(this).val(inputVal.replace(/[^a-z0-9~!@#$%^&*()._+|<>?:{}]/gi,''));
				$(this).val(inputVal.replace(/[^a-z0-9~!@#$%^&*()._\-+|<>?:{}]/gi,''));
             }
         });
	}
	if($(".float").length > 0)
	{
		 $(".float").keyup(function(event){
			 var pattern = /[^0-9.]/g;
			  this.value = this.value.replace(pattern, '');
         });
	}
	
	$('.nospecial').on('keyup', function (event) {
	    var regex = new RegExp("^[a-zA-Z0-9]+$");
	    var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);
	    if (!regex.test(key)) {
	       event.preventDefault();
	       return false;
	    }
	});
	$('.nospecial').on('keyup', function(e){
		var inputValue = $(this).val();
		//console.log(inputValue);
		$(this).val(inputValue.replace(/[^(가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s)]/gi,''));
	});
	
	$('textarea[maxlength]').keyup(function(){
		var max = parseInt($(this).attr('maxlength'));
		if($(this).val().length > max){
			$(this).val($(this).val().substr(0, $(this).attr('maxlength')));
		}
	
		$(this).parent().find('.charsRemaining').html((max - $(this).val().length)+'/'+max);
	 });
	
	$('.diphone').on('keyup', function(e){
		$(this).val( $(this).val().replace(/[^0-9]/g, "").replace(/(^02|^0505|^1[0-9]{3}|^0[0-9]{2})([0-9]+)?([0-9]{4})$/,"$1-$2-$3").replace("--", "-") );
	});
	
	$('.dipassword').on('blur', function(e){
		if($(this).val()==""){
			return;
		}
		if(!passRegCheck($(this).val())){
			Swal.fire(
					'',
					'비밀번호는 영문자,숫자,특수문자를 조합하여 최소 8자리 이상을 사용하세요',
					'warning'
				);
			$(this).val("");
		}
	});
	
	$(".email").on('blur', function(e){
		if($(this).val()==""){
			return;
		}
		var regEmail = /^[0-9a-zA-Z]([-_\.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_\.]?[0-9a-zA-Z])*\.[a-zA-Z]{2,3}$/;
		if(!regEmail.test($(this).val())){
			Swal.fire(
				/*'',
				'이메일 형식이 맞지 않습니다.',
				'warning'*/
				{
					title:'',
					html : '이메일 형식이 맞지 않습니다.',
					icon : 'warning',
					confirmButtonText : '확인'
				}
				
			)
			$(this).val("");
			return;
		}
	});
	
	if($(".noLowercase").length > 0)
	{
		 $(".noLowercase").keyup(function(event){
             if (!(event.keyCode >=37 && event.keyCode<=40)) {
                 var inputVal = $(this).val();
                 $(this).val(inputVal.toUpperCase());
             }
         });
	}

}

(function ($, kendo) {
	var _init = kendo.ui.Grid.fn.init;
	var extendedGrid = kendo.ui.Grid.extend({

	    init: function (element, options) {   
	    	/*
	    	$.each(options.columns,function(i,o){
	    		if(o.field=='rowNumber' || o.title == "No"){
	    			o.template=gridRownum
	    		}
			})
			*/
			
			var bool = true;
			if (typeof options.pageable  === 'boolean' ){
				if(!options.pageable){
					bool = false;
				}
			}
			
			if(bool){
				options.pageable = {
					pageSizes: [10, 20, 50, 100],
					responsive: false
				} 
			}
			/*
			var func = options.dataBound;
			
			options.dataBound = function(a,b,c){
				
				changeStatColor($(element))
				eval(func)
			}
			*/
			
			var func = options.dataBinding;
			options.dataBinding = function(a,b,c) {
				rowNumber = (this.dataSource.page() -1) * this.dataSource.pageSize();
		        eval(func);
			}
	        //call base constructor
	        _init.call(this, element, options);
	                        
	    }               
	});
	kendo.ui.plugin(extendedGrid);
}(window.kendo.jQuery, window.kendo));

var changeStatColor= function($target){
	$target.find('td:contains("승인대기")').addClass('t-color').addClass('c-yellow')
	$target.find('td:contains("심사 대기")').addClass('t-color').addClass('c-yellow')
	$target.find('td:contains("승인완료")').addClass('t-color').addClass('c-green')
	$target.find('td:contains("심사 완료")').addClass('t-color').addClass('c-green')
	$target.find('td:contains("반려")'	).addClass('t-color').addClass('c-red')

}


$.fn.serializeObject = function() {
  var result = {}
  $.each(this.serializeArray(), function(i, element) {
	    var node = result[element.name]
	    if ("undefined" !== typeof node && node !== null) {
	      if ($.isArray(node)) {
	        node.push(element.value)
	      } else {
	        result[element.name] = [node, element.value]
	      }
	    } else {
	      result[element.name] = element.value
	    }
  })
  return result
}

function passRegCheck(val){
	var pattern_pw = /^.*(?=^.{9,16}$)(?=.*\d)(?=.*[a-zA-Z])(?=.*[\{\}\[\]\/?.,;:|\)*~`!^\-+<>@\#$%&\\\=\(\'\"]).*$/;
	if(pattern_pw.test(val)){
		return true;
	}else{
		return false;
	}
}


function setFromToDate($starget, $etarget, startDate, endDate){
	
	var todayDate = new Date();
	 
	if(!startDate)
		startDate = kendo.date.addDays(todayDate, -7); 
	if(!endDate)
		endDate = todayDate;
	
	$starget.kendoDatePicker({
        format: "yyyy-MM-dd",
        value:startDate,
        dateInput:true,
        change: function(e){
        	var startDateObj = e.sender
        	var endDateObj = $etarget.data('kendoDatePicker');
        	var startDt = e.sender.value();
        	var beforeStartDt =  new Date(e.sender.value()); beforeStartDt.setDate(beforeStartDt.getDate()-1);
//			endDateObj.setOptions({ 
//				disableDates:function (date) {
//					if (date <beforeStartDt){
//						return true;
//					}else	
//			            return false;
//			    } 
//			});
        	if(startDt > endDateObj.value()){
				endDateObj.value(startDt);
        	}
        }
    });	
	
	$etarget.kendoDatePicker({
        format: "yyyy-MM-dd",
        value:new Date(),
        dateInput:true,
        change: function(e){
        	var startDateObj =$starget.data('kendoDatePicker')
        	var endDateObj =  e.sender;
        	var endDt = e.sender.value()
        	
        	if(startDateObj.value() > endDt){
        		startDateObj.value(endDt);
        	}
        }
    });	
	
	
}

function createDateLimitPickerYMD(tgt, endTgt, can, max)
{
	var disableDatesList = ["sa", "su"];
	
	$(tgt).kendoDatePicker({
        format: "yyyy-MM-dd",
        value: can,
        min: can,
		max: max,
		disableDates: disableDatesList,
        dateInput:false,
        change:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        }
    });
}

function makeSelectBox(list, tgt)
{
	$.each(list, function (i, item) {
	    $(tgt).append($('<option>', { 
	        value: item.code,
	        text : item.codeNm 
	    }));
	});
}


function makeDropDownList(list, tgt)
{
	$(tgt).kendoDropDownList({
		dataTextField: "codeNm",
        dataValueField: "code",
		dataSource: list,
	});
}

function initValidator(tgt){
	validator = $(tgt).kendoValidator().data("kendoValidator");
}

function getCodeNm(list, code)
{
	for(var i =0 ; i < list.length ; i++)
	{
		if(list[i].code == code)
		{
			return list[i].codeNm;
		}
	}
	return "";	
}

function getCodeDc(list, code)
{
	for(var i =0 ; i < list.length ; i++)
	{
		if(list[i].code == code)
		{
			return list[i].codeDc;
		}
	}
	return "";	
}

function compareTime(startTime, endTime) //시작시간 종료시간 비교
{
	if((startTime.split(":")[0] + startTime.split(":")[1]) * 1 > (endTime.split(":")[0] + endTime.split(":")[1]) * 1){
		Swal.fire({
			title: '',
			text: "일정 입력 시간을 확인해주세요.",
			confirmButtonText: '확인',
			icon:'warning'
		});
		return;
	}
}


function resetRowNumber(e) {
    rowNumber = 0;
}
 
function renderNumber(data) {
    return ++rowNumber;
}

var CommonDataObj = {};
var iemReportData = {};

function loadUI(view,target,obj){
	var $target= $(target);
	var url = '' ;
	var param = {};
	
	if(obj){
		CommonDataObj[view] = obj;
		if(view=="reportPerIem")
		{
			iemReportData[obj.excExprIemSeq] = obj;
			param.view = view;
			param.seq = obj.excExprIemSeq;
		}
	}
	$.ajax({
		url: CTX + '/common/view/getView' ,
		data:param,
		async:false,
		cache:false, 
		success: function(data, textStatus, jqXHR) { 
			if(!data){
				alert();
			}
			
			if($target.length>0){
				if(data){
					$target.append(data);
				}
			}else{
				return data;
			}
		},complete: function(){
		}
	});
}

window.onload  = function() {
	drawCaption();
}

function drawCaption()
{
	//$("table[role='grid']");//.insertBefore("<caption></caption>");
	//$('#dataTable')[0].first().prepend('<caption><span>Weekly Results</span></caption>');
	console.log($("table[role='grid']").find('th'));
	if($("table[role='grid']") != null)
	{
		var captionText = "";
		for(var i = 0 ; i < $("table[role='grid']").find('th').length ; i++)
		{
			captionText += $("table[role='grid']").find('th')[i].innerText + ",";
		}
		
		captionText += " 로 구성";
		$("table[role='grid']").prepend("<caption style='display:none;'>"+captionText+"</caption>");
		//$("#dataTable > colgroup").insertBefore("<caption></caption>");
	}
	
}



function changeDayDt(obj, day) // day기준 1
{
	var btnObj = $(obj).data("id");
	var tmpDt = $("#searchBgnDe").data("kendoDatePicker").value();
	var year = new Date(tmpDt).getYear();
	var month = new Date(tmpDt).getMonth();
	year += (year < 2000) ? 1900 : 0; 
	month = month >= 10 ? month : '0' + month;
	
	
	var firstDate, lastDate;
	
	if( btnObj == "before")
	{
		var nowDay = new Date(tmpDt).getDate() - day;	
		firstDate = new Date(year, month , nowDay); 
		
		var year = new Date(firstDate).getYear();
		var month = new Date(firstDate).getMonth();
		year += (year < 2000) ? 1900 : 0; 
		month = month >= 10 ? month : '0' + month;
		
		var endDay =  new Date(firstDate).getDate() + (day - 1);
		lastDate = new Date(year, month , endDay); 
	}
	else
	{  
		var nowDay = new Date(tmpDt).getDate() + day;
		firstDate = new Date(year, month , nowDay); 
		
		var year = new Date(firstDate).getYear();
		var month = new Date(firstDate).getMonth();
		year += (year < 2000) ? 1900 : 0; 
		month = month >= 10 ? month : '0' + month;
		
		var endDay =  new Date(firstDate).getDate() +  (day - 1);
		lastDate = new Date(year, month , endDay);
	}

	$("#searchBgnDe").data("kendoDatePicker").value(firstDate);
	$("#searchEndDe").data("kendoDatePicker").min(firstDate);
	$("#searchEndDe").data("kendoDatePicker").value(lastDate);
	
	searchProcess();
}

function changeDateL(obj)
{
	var start = $("#searchBgnDe").data("kendoDatePicker").value();
	var end = $("#searchEndDe").data("kendoDatePicker").value();
	
	var hours = Math.abs(end - start) / 36e5;
	
	console.log("hours", hours);
	start.setHours(start.getHours() - hours);
	end.setHours(end.getHours() - hours);
	
	console.log("start:", start);
	console.log("end:", end);
	
	$("#searchBgnDe").data("kendoDatePicker").value(start);
	$("#searchEndDe").data("kendoDatePicker").value(end);	
	
	searchProcess();
}

function changeDateR(obj)
{
	var start = $("#searchBgnDe").data("kendoDatePicker").value();
	var end = $("#searchEndDe").data("kendoDatePicker").value();
	
	var hours = Math.abs(end - start) / 36e5;
	
	start.setHours(start.getHours() + hours);
	end.setHours(end.getHours() + hours);
	
	$("#searchBgnDe").data("kendoDatePicker").value(start);
	$("#searchEndDe").data("kendoDatePicker").value(end);	
	
	searchProcess();
}


function changeLaboDayDt(obj) // day기준 (시험실 온습도)
{
	var id = $(obj).data("objid");
	var objStr = id.split( '_');

	var btnObj = objStr[0];
	var code = objStr[1];
	
	searchProcess(code);
}

function changeWeekDt(obj) // 일주일 기준
{
	
	var tmpDt = $("#searchBgnDe").data("kendoDatePicker").value();
	
	var year = new Date(tmpDt).getYear();
	year += (year < 2000) ? 1900 : 0; 
	
	var btnObj = $(obj).data("id");
	if( btnObj == "before")
		var nowYear = new Date(tmpDt).getYear() - 1;	
	else
		var nowYear = new Date(tmpDt).getYear() + 1;
		
	nowYear += (nowYear < 2000) ? 1900 : 0; 
	
	var firstDate, lastDate;
	firstDate = new Date(nowYear, 0,1); 
	lastDate = new Date(nowYear, 11,31); 
	
	$("#searchBgnDe").data("kendoDatePicker").value(firstDate);
	$("#searchEndDe").data("kendoDatePicker").min(firstDate);
	$("#searchEndDe").data("kendoDatePicker").value(lastDate);
	
	//searchProcess();
}

function changeMonthDt(obj, month) // 월 기준
{
	var tmpDt = $("#monthpicker").data("kendoDatePicker").value();  
	
	var year = new Date(tmpDt).getYear();
	year += (year < 2000) ? 1900 : 0; 
	
	var btnObj = $(obj).data("id");
	if( btnObj == "before")
		var nowMonth = new Date(tmpDt).getMonth() - 1;	
	else
		var nowMonth = new Date(tmpDt).getMonth() + 1;
	
	nowMonth = nowMonth >= 10 ? nowMonth : '0' + nowMonth;
	var firstDate;
	firstDate = new Date(year, nowMonth); 
	
	$("#monthpicker").data("kendoDatePicker").value(firstDate);
	searchProcess();
}

function changeQuarDt(obj, year, quarter) // 분기 기준
{
	var startmonth = $("#quarterpicker").val();
	var nowmonth = startmonth;
	
	var btnObj = $(obj).data("id");
	if( btnObj == "before")
	{
		if(startmonth != 1)
			nowmonth = parseInt(startmonth) - 1;	
	}
	else
		nowmonth = parseInt(startmonth) + 1;
	
	if(nowmonth == 4) // 4분기 이상일 경우 화살표 제거
		$(obj).css("display", "none");
	else if(nowmonth == 1) // 1분기 이하일 경우 화살표 제거
		;//$(obj).css("display", "none");
	else 
		$(".changeDtArrow").css("display", "block");
	
	$("#quarterpicker").val(nowmonth);
	searchProcess();
}

function changeYearDt(obj, year) // 연 기준
{
	if(year == "undefined" || year == null || year == "")
		var tmpDt = $("#searchBgnDe").data("kendoDatePicker").value();
	else
		var tmpDt = $("#yearpicker").data("kendoDatePicker").value();
	
	var btnObj = $(obj).data("id");
	if( btnObj == "before")
		var nowYear = new Date(tmpDt).getYear() - 1;	
	else
		var nowYear = new Date(tmpDt).getYear() + 1;
		
	nowYear += (nowYear < 2000) ? 1900 : 0; 
	
	if(year == "undefined" || year == null || year == "")
	{
		// 시험관리 연 기준 검색
		var firstDate, lastDate;
		firstDate = new Date(nowYear, 0,1); 
		lastDate = new Date(nowYear, 11,31); 
		
		$("#searchBgnDe").data("kendoDatePicker").value(firstDate);
		$("#searchEndDe").data("kendoDatePicker").min(firstDate);
		$("#searchEndDe").data("kendoDatePicker").value(lastDate);
	}	
	else
	{
		// 시험계획관리 연 기준 검색
		var firstDate;
		firstDate = new Date(nowYear, 0,1); 
		
		$("#yearpicker").data("kendoDatePicker").value(firstDate);
	}
	
	searchProcess();
}

function dataTableSelectedRow(data, obj) // 장비사용 이력&시험데이터관리 : 그래프 클릭하면 해당 row selected 
{
	var objDt = data.name;
	if( obj == "chart2")
	{
		var grid = $("#dataTable2").data("kendoGrid");
		var list = dataTable2.dataSource.data(); 
	}
	else if( obj == "chart3")
	{
		var grid = $("#dataTable3").data("kendoGrid");
		var list = dataTable3.dataSource.data(); 
	}
	else
	{
		var grid = $("#dataTable").data("kendoGrid");
		var list = dataTable.dataSource.data(); 
	}
	
	var rowNum = 0;
	var modelToSelect = null;
	 
	var listCnt = list.length;
	for(var i = 0; i < list.length ; i++)
	{
		if( objDt == new Date(list[i].registDt).getDateTime())
		{   
			modelToSelect = list[i];
            rowNum = i; 
            break;
		}
	}	
	rowNum = parseInt((listCnt - rowNum)); // 정렬이 desc이므로 rowNum 변경   
	
	var currentPageSize = grid.dataSource.pageSize();
    var pageWithRow = parseInt((rowNum / currentPageSize)) + 1; 
    
    grid.dataSource.page(pageWithRow);
    var row = grid.element.find("tr[data-uid='" + modelToSelect.uid + "']");
	if (row.length > 0) {
         grid.select(row);
         grid.content.scrollTop(grid.select().position().top);
    }
}

function getTableCurrentPage(grid) //직전 페이지 위치 유지 
{
	if(  gridPage == null || gridPage == "" )
		;
	else
	{
		grid.dataSource.page(gridPage);
		gridPage = null;
	} 
}


//init stomp
function connect() {
    var socket = new SockJS('/gs-guide-websocket'); 
    //var socket = new SockJS('http://192.168.0.43:8080/gs-guide-websocket'); 
    
    stompClient = Stomp.over(socket);
    stompClient.connect({}, function (frame) {
        //setConnected(true);
        //alert(1);
        console.log('Connected: ' + frame);
        stompClient.subscribe('/topic/greetings', function (greeting) {
        	
        	if( typeof(process_webskmsg) == 'function' )
        	{
        		process_webskmsg(greeting);
        	}
        	else if( typeof(process_webskmsg_inheader) == 'function' )
        	{
        		process_webskmsg_inheader(greeting);
        	}
        	
        	
        	
            //showGreeting(JSON.parse(greeting.body).content);
        });
    });
}


function loadSaleAmount(val) //할인가 적용
{
	var lastSum = 0;
    var val = 0;
	if( $("input[name=dscntSe]:checked").val()  == "P01" || $("#dscntSe").text() == "퍼센트" )  // 퍼센트 할인
    {
    	var salePay;
    	val = $("#dscntAmount").val();
    	console.log("rntFeeTxt", $("#sumAmount").val() ); 
    	salePay = $("#sumAmount").val() * val / 100;
    	lastSum =  parseInt($("#sumAmount").val() ) - parseInt(salePay);
    	
    	$("#lastSumTxt").text(kendo.toString(parseInt(lastSum), "c0"));
    	$("#lastSumAmount").val(lastSum);
    	console.log("lastSum", lastSum);
    }
    else
    {
    	console.log("rntFeeTxt", $("#sumAmount").val() );
    	val = $("#dscntAmount").val();
    	lastSum = parseInt($("#sumAmount").val() ) - parseInt(val);
    	$("#lastSumTxt").text(kendo.toString(parseInt(lastSum), "c0"));
    	$("#lastSumAmount").val(lastSum);
    	console.log("lastSum", lastSum);
    }
}


function changeDatePicker(value) // 유효기간 = 견적일+ 30일
{
	var date = new Date(value);
	
    date.setDate(date.getDate() + 30);
    var dateString = date.toISOString().split('T')[0];
    var _validpd = $("#validpd").data("kendoDatePicker");
    _validpd.value(dateString);

    console.log("dateString", dateString); 
}


function disconnect() {
    if (stompClient !== null) {
        stompClient.disconnect();
    }
    setConnected(false);
    console.log("Disconnected");
}

//textarea 자동 높이
function txtareaAutoHeight()
{
	$("textarea.txtareaAutoH").on('keydown keyup', function () {
		$(this).css('height', 'auto');
		$(this).height(this.scrollHeight - 10);	
	});		
}



function getDocSttus(data)
{
	if (data == "A01") {
		sttus = "임시 저장";
	} else if (data == "A02") {
		sttus = "제출";
	} else {
		sttus = "재요청";
	}
	
	return sttus;
}


/**********************
 * 스마트 검사실 전용 기준 구분 체크 박스 만들기
 * ADD SJ 20220711
 ***********************/
function makeStdrBox(confm, stdr, tgt)
{	
	//** 검사 구분**//
	if (confm == "T01") {
		code = commCode.ST01;
	} else if (confm == "T02") {
		code = commCode.ST02;
	} else {
		code = commCode.ST03;
	}
	
	//** 기준 구분**//
	stdr = stdr.split(',');
	
	var stdrSeArr = [];
	for ( var i in stdr ) {
       for(var j=0; j < code.length; j++){
	   		var arrObj = code[j];
	   		if(stdr[i] == arrObj.code)
	   		{
	   			stdrSeArr.push(arrObj);
	   		}
	   	}
    }
	
	makeWriteCheckBox(stdrSeArr, "stdrSe", "#stdrBox");//기준 구분
}

function getSeType(data)
{
	var type;
	if(data ==  "A01")
		type = "dv";
	else if(data ==  "A02")
		type = "cs";
	else if(data ==  "A03")
		type = "ta";
	
	return type;
}

function setTitleTemplt(se)
{
	var seArr = [];
	
	seArr.textSe = getCodeNm(commCode.S0404, se);
	seArr.codeSe = getCodeDc(commCode.S0404, se);
	return seArr;
}

function getCnfrmnKndCode(cnfrmnKndStr){
	var cnfrmnKndCode = "";
	
	if(cnfrmnKndStr.indexOf("부품")>-1){
		cnfrmnKndCode="A";
	}else if(cnfrmnKndStr.indexOf("구성품")>-1){
		cnfrmnKndCode="B";
	}else if(cnfrmnKndStr.indexOf("완성차")>-1){
		cnfrmnKndCode="C";
	}else if(cnfrmnKndStr.indexOf("시운전")>-1){
		cnfrmnKndCode="E";
	}
	
	return cnfrmnKndCode;	
}

function getCnfrmnKndStdr(cnfrmnKndCode){
	var cnfrmnKndStr = "";
	
	if(cnfrmnKndCode.indexOf("A")>-1){
		cnfrmnKndStr="부품시험";
	}else if(cnfrmnKndCode.indexOf("B")>-1){
		cnfrmnKndStr="구성품시험";
	}else if(cnfrmnKndCode.indexOf("C")>-1){
		cnfrmnKndStr="완성차시험";
	}else if(cnfrmnKndCode.indexOf("E")>-1){
		cnfrmnKndStr="시운전시험";
	}
	
	return cnfrmnKndStr;	
}

function checkAttendUsers(val, tgt) 
{
	//필수참석자와 참석자 중복 체크 
	imUsrArr =  importantUser.value();
	atUsrArr =  attendingUser.value();
	
	var check = imUsrArr.filter(it => atUsrArr.includes(it)); //중복된 사용자를 리턴함. 
	if( check.length >= 1)
	{
		Swal.fire({
			title: '',
			text: '중복된 사용자가 지정 되었습니다. ',
			icon:'warning',
			confirmButtonText : '확인'
		});
		
		//방금 선택한 중복 사용자 삭제 하기 
		//$("#" +tgt).data("kendoDropDownTree").dataSource.remove();
		
		return;
	}	
}

function init_customBtnStting() //버튼 월요일-화요일18시까지 
{
	// 제출 
	if((new Date).getDay() == 1 || (((new Date).getDay() == 2) && ((new Date).getHours() < 18)))
	{
		$("div[data-func='submit']").show();
	} 
}


function getDocType(relateDocSeq)
{
	if(relateDocSeq.indexOf("REQST") > -1)
		return "요청서";
	else if(relateDocSeq.indexOf("CMRCNFRMN") > -1)
		return "고객 확인서";
	else if(relateDocSeq.indexOf("EXMNT") > -1)
		return "검토서";
	else if(relateDocSeq.indexOf("CNFRMN") > -1){		
		if(relateDocSeq.indexOf("TOTALCNFRMN") > -1)
			return "통합확인서";
		else
			return "확인서";		
	}
}


/**********************
 * FILE Function
 * KIMDK 20211018
 ***********************/
var maxlen;
function getFileModifyForTable(data, dropZone, extension, maxNum, isSingle)
{
	maxlen = maxNum==null?null:maxNum; // 파일 갯수
	var columnKeys = Object.keys(data);
	for(i = 0 ; i < columnKeys.length ; i++)
    {
		if(columnKeys[i].indexOf("fileList") > -1)
		{
			console.log(data[columnKeys[i]]);
			var fList = data[columnKeys[i]].map(function(element){
			        return { 
			        	name: element.orignlFileNm, 
			        	size: element.fileMg, 
			        	extension: "." + element.fileExtsn,
			        	value : element
			        }});
			
			if(isSingle!=null)
				init_fileupload("#"+columnKeys[i], fList, dropZone, extension, maxlen, true);
			else
				init_fileupload("#"+columnKeys[i], fList, dropZone, extension, maxlen);
		}
		
    }
}

function init_fileupload(target, files, dropZone, extension, maxlen, isSingle)
{
	console.log("maxlen", maxlen);
	console.log("extension", extension);
	var fileFlag =true;
	if(extension == null){
		extension = g_Kendo_allowedDocExt;
		//extension = $("#Extension")[0].value.replace(".", "").split(".");
	}
	if (isSingle!=null){
		fileFlag=false;
	}
	
	$(target).kendoUpload({
		multiple:fileFlag,
        async: {
            chunkSize: 1100000,// bytes 
            saveUrl: "chunksave",
            removeUrl: "remove",
            autoUpload: false,
        },
        error: function (e) {
            var files = e.files;
            if (e.operation == "upload") {
                console.log (e);
                alert("Failed to upload " + files.length + " files");
            }
        },
        validation:{
        	allowedExtensions: extension,
        	maxFileSize: g_Kendo_maxFileSize,
        	minFileSize: g_Kendo_minFileSize
        }, 
        select: onFileUploaderSelect,
        dropZone: dropZone,
        files:files,
        showFileList: true,
        remove: onFileRemove
    }).data("kendoUpload");
	
	//$(".textWrapper").append("<div class='dropImageHereText'>가능 확장자: " +  extension + "</div>");
	
	// 용량 bytesToSize
	var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	var i = parseInt(Math.floor(Math.log(g_Kendo_maxFileSize) / Math.log(1024)));
	var maxSize = Math.round(g_Kendo_maxFileSize / Math.pow(1024, i), 2) + ' ' + sizes[i];
	
	
	
	if($(".k-dropzone").length > 1){
		$(".k-dropzone>.maxSize").remove();
	}
	$(".k-dropzone").append("<div class='maxSize'>(최대 크기 : " + maxSize + " )</div>");
	$(target).attr("accept", extension);
	
}

function onFileUploaderSelect(e)
{
	var UPLOAD_FILE_NUM_MAX = maxlen;
	if( UPLOAD_FILE_NUM_MAX != null )
	{
		if (e.files.length > UPLOAD_FILE_NUM_MAX || $(this.element[0].closest(".k-dropzone")).next().children().length + e.files.length > UPLOAD_FILE_NUM_MAX) {
			Swal.fire({
				text: '업로드 가능한 파일 수는 최대 ' + UPLOAD_FILE_NUM_MAX + '개 입니다.',
				confirmButtonText: '확인',
				icon:'warning'
			});
			//e.preventDefault();
			/*var child = $(this.element[0].closest(".k-dropzone")).next().children();
			
			while(true){
				if($(this.element[0].closest(".k-dropzone")).next().children().length + e.files.length > UPLOAD_FILE_NUM_MAX){
					var files=this.getFiles();
					this.removeFile(files[0]);
					$(this.element[0].closest(".k-dropzone")).next().children()[0].remove();
					var tmp  = $(this.element[0].closest(".k-dropzone")).next().children("li:eq(0)");
					tmp.find(".k-i-x").click();
					continue;
					for(var fileCnt =files.length; fileCnt=1; fileCnt--){
						var rawFile = files[fileCnt-1];
						for(var eCnt =0; eCnt<e.files.length; eCnt ++){
							var eFile = e.files[eCnt];
							if(rawFile.rawFile.name == eFile.rawFile.name){
								files.splice(fileCnt-1,1);
								break;
							}
						}
					}
				}
				break;
			}*/
		}
	}
}

function init_fileList(formData, target, fileList){
	var file = $(target).data("kendoUpload").getFiles();
	var fList = [];
	for( var i = 0; i < file.length; i++) 
	{
		if(file[i].rawFile != null )
			formData.append(fileList, file[i].rawFile); 
	} 
}

function onFileRemove(e) {
    // An array with information about the removed files
    var files = e.files;
    
    if(files.length == 0)
    {
		return;
    }
    
    var file = files[0];
    if(file.rawFile == null)
    {
    	$("#reqForm").append($('<input/>', {type: 'hidden', name: 'delfile', value:file.value.atchFileId + "," + file.value.fileSn }));
    	
    	e.sender.clearFileByUid(file.uid);
    }

    // Processes the remove event
    // Optionally cancels the remove operation by calling
    // e.preventDefault()
}

function getFileViewForTable(data)
{
	var columnKeys = Object.keys(data);
	for(i = 0 ; i < columnKeys.length ; i++)
    {
		if(columnKeys[i].indexOf("fileList") > -1)
		{
			var ulHtml = '<ul class="k-upload-files k-reset">';
			console.log(data[columnKeys[i]]);
			
			
			var tid = columnKeys[i].split("_fileList")[0];
			
			
			data[columnKeys[i]].forEach(element => 
				//console.log(element)
				
				$("#"+tid).append(getFileViewHtmlForTable(element))
			);
			
			$("#"+tid).prepend('<ul class="k-upload-files k-reset">');
			$("#"+tid).append('</ul>'); 
			
		}
		
    }
}


function getFileOnlyViewForTable(data)
{
	var columnKeys = Object.keys(data);
	for(i = 0 ; i < columnKeys.length ; i++)
    {
		if(columnKeys[i].indexOf("fileList") > -1)
		{
			var ulHtml = '<ul class="k-upload-files k-reset">';
			console.log(data[columnKeys[i]]);
			
			
			var tid = columnKeys[i].split("_fileList")[0];
			
			
			data[columnKeys[i]].forEach(element => 
				//console.log(element)
				
				$("#"+tid).append(getFileOnlyViewHtmlForTable(element))
			);
			
			$("#"+tid).prepend('<ul class="k-upload-files k-reset">');
			$("#"+tid).append('</ul>'); 
			
		}
		
    }
}

function getFileOnlyViewHtmlForTable(file)
{ 
	var _tmpString = file.fileExtsn;
	var lowerExtsn = _tmpString.toLowerCase(); //파일 확장자 소문자로 변경
	
	var ulHtml = '<li class="k-file k-file-success k-i-file-' + lowerExtsn + '">';
	ulHtml += '<span class="k-file-name-size-wrapper"><span class="k-file-name" title="'+file.orignlFileNm+'">'+file.orignlFileNm+'</span></span>';
	/*ulHtml += '<button type="button" class="k-button k-upload-action" aria-label="Download"><span class="k-icon k-i-close k-i-x" title="Download"></span></button>';*/
	ulHtml += '</li>';
	
	return ulHtml;
}


function getFileViewHtmlForTable(file)
{ 
	var _tmpString = file.fileExtsn;
	var lowerExtsn = _tmpString.toLowerCase(); //파일 확장자 소문자로 변경
	
	var ulHtml = '<li class="k-file k-file-success k-i-file-' + lowerExtsn + '">';
	ulHtml += '<a href="javascript:fn_delta_downFile(\''+file.atchFileId+'\','+file.fileSn+')">';
	ulHtml += '<span class="k-file-name-size-wrapper"><span class="k-file-name" title="'+file.orignlFileNm+'">'+file.orignlFileNm+'</span></span>';
	ulHtml += '</a>';
	/*ulHtml += '<button type="button" class="k-button k-upload-action" aria-label="Download"><span class="k-icon k-i-close k-i-x" title="Download"></span></button>';*/
	ulHtml += '</li>';
	
	return ulHtml;
}

function fn_delta_downFile(atchFileId, fileSn){
	window.open(CTX + "/cmm/fms/FileDown.do?atchFileId="+atchFileId+"&fileSn="+fileSn);
}

function formSubmitByEnter(val)
{
	if(window.event.keyCode == 13){
		$(val).next().click()
	}
}

function approvalPopup(){
	$('.btn-approval').click(function(){
		$('.right-menu').addClass('active');
	});
	$('.close-btn').click(function(){
		$('.right-menu').removeClass('active');
	});
}

function load_approve_in_frame(seq) 
{
	$('.approve-module').attr('src', CTX + "/approve/ui/page.do" +"?relateDocSeq="+seq );
}

function goHome()
{
	$.redirect(CTX + "/");
}

function goPrjct(obj)
{
	//addpanel(null, obj);
	//window ui 변경시 아래 함수 사용
	if(typeof(addpanel_v2) == 'function'){
		addpanel_v2(null, obj);
	}
	else{
		$.redirect(CTX + "/main/view/",
		{
			prjctSeq : obj.id,
			prjctWindow : obj.id
		});
	}
}

function leftMenuOpen()
{
	$('.hamburger-icon').click(function(){
		
		//메뉴 이벤트
		$('.hamburger-icon>span').toggleClass('open');
		$('.profil-group').toggleClass('open');
		
		//좌측 메뉴 
		$('#leftMenu').toggleClass('show');
		$('.left-overay').toggleClass('show');
	})
}

//필수입력 표시 input 태그 안으로 배치
function validInputDiv(){
	var validInput = $('input[validationmessage="필수입력"]');
	
	validInput.wrap('<div class="valid_div position-relative"></div>');
	validInput.addClass('input-w100');
	
}

//중복체크 등 인풋+버튼 붙어있는 경우 valid_div 크기 조정
function inputAndBtn(){
	var btnSibling = $('.btn').prev('.valid_div');
	
	btnSibling.css({"width":"70%", "display":"inline-block"});
}

var UPLOAD_FILE_NUM_MAX = null;
//var g_Kendo_maxFileSize = 52428800;
var g_Kendo_maxFileSize = 1073741824;
var g_Kendo_minFileSize = 0;
var g_Kendo_allowedDocExt = [".doc",".docx",".hwt",".hwp",".pdf",".txt",".zip",".ppt",".img",".tar",".tgz",".zool",".xlv",".xlw",".xll",".xld",".xlc",".xlb",".xla",".xlt",".pptx",".pps",".ppsx",".gif",".jpg",".jpeg",".png",".xls",".xlsx",".xlsm",".txt", ".csv"];
var g_Kendo_allowedImgExt = [".gif",".jpg",".jpeg",".png"];


//Create DatePicker start, End
function createDatePickerApplyYMD(tgt, endTgt)
{
	console.log("aaa");
	var nowDate = new Date();
	var canDate = new Date();
	canDate.setDate(nowDate.getDate() + 7 - nowDate.getDay() + 1);
	var maxDate = new Date();
	maxDate.setDate(nowDate.getDate() + 14 - nowDate.getDay());
	$(endTgt).kendoDatePicker({
		format: "yyyy-MM-dd",
        value: maxDate,
        min: canDate,
		max: maxDate,
        dateInput:false,
        culture:"ko-KR",
        change:function(e){
        	if(tgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(tgt).data("kendoDatePicker").value();
        		
        		
        		//$(tgt).data("kendoDatePicker").max(endDt);
        		
        		if(startDt > endDt)
        			$(tgt).data("kendoDatePicker").value(endDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(tgt).data("kendoDatePicker").value();
        		
        		
        		$(tgt).data("kendoDatePicker").max(endDt);
        		
        		if(startDt > endDt)
        			$(tgt).data("kendoDatePicker").value(endDt);
        		
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var endDt = e.sender.value();
        		var startDt = $(tgt).data("kendoDatePicker").value();
        		
        		
        		$(tgt).data("kendoDatePicker").max(endDt);
        		
        		if(startDt > endDt)
        			$(tgt).data("kendoDatePicker").value(endDt);
        		
        		
        	}
        }
	})
	$(tgt).kendoDatePicker({
        format: "yyyy-MM-dd",
        value: kendo.date.addDays(nowDate, +7),
        min: canDate,
        max: maxDate,
        dateInput:false,
        change:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databinding:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        },
        databound:function(e){
        	if(endTgt != null)
        	{
        		var startDt = e.sender.value();
        		var endDt = $(endTgt).data("kendoDatePicker").value();
        		$(endTgt).data("kendoDatePicker").min(startDt);
        		if(endDt < startDt)
        			$(endTgt).data("kendoDatePicker").value(startDt);
        		
        	}
        }
    });
	
	
}
