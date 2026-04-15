/*************************************************
* TITLE:        �����ґ������j���[���
* VERSION:      1.00
* DATE:         2005.2.4 wwww
*************************************************/
function jsOnload(){
	if(window.name=="frmHEAD"){
		document.thisForm.MenuOn.style.display="inline";
		document.thisForm.MenuOff.style.display="inline";
		document.getElementById("MenuOnLabel").style.display="inline";
		document.getElementById("MenuOffLabel").style.display="inline";
	}
}
function jsDisplayMenu(flag){
	var frsMAIN=parent.document.getElementById("frsMAIN");
	if(flag){
		frsMAIN.cols="164,*";
	}else{
		frsMAIN.cols="0,*";
	}
}

function jsClick(i){
	var frm=document.thisForm;
	switch(i){
		case 1:
			frm.qs.value="00C400C400C400C4018C018401B801B80184018C";
			frm.action="./do/K000ShowAction";
			break;
		case 2:
			frm.qs.value="00C800C800C800C8018C018401B801B80184018C00C8";
			frm.action="./do/K000ShowAction";
			break;
		case 3:
			frm.qs.value="3333";
			frm.action="./do/Accepter";   //KF000ShowAction";
			break;
	}
	frm.submit();
}

function jsLink1(i){
	var frm=document.thisForm;
	switch(i){
		case 1:
			frm.supplytype.value="00";
			frm.usertype.value="1";
			frm.action="../do/KK000ShowAction";
			break;
		case 2:
			frm.supplytype.value="01";
			frm.usertype.value="2";
			frm.action="../do/KK000ShowAction";
			break;
		case 3:
			frm.supplytype.value="10";
		    frm.usertype.value="3";
			frm.action="../do/KK000ShowAction";
			break;
		case 4:
			frm.supplytype.value="11";
		    frm.usertype.value="4";
			frm.action="../do/KK000ShowAction";
			break;
		case 5:
			frm.supplytype.value="00";
		    frm.usertype.value="5";
			frm.action="../do/KK000ShowAction";
			break;
		case 6:
			frm.supplytype.value="01";
		    frm.usertype.value="6";
			frm.action="../do/KK000ShowAction";
			break;
		case 7:
			frm.supplytype.value="10";
		    frm.usertype.value="7";
			frm.action="../do/KK000ShowAction";
			break;
		case 8:
			frm.supplytype.value="11";
		    frm.usertype.value="8";
			frm.action="../do/KK000ShowAction";
			break;
	}
	frm.submit();
}

function jsLink2(i){
	var frm=document.KF000DynaActionForm;
	switch(i){
		case 1:
			frm.supplytype.value="00";
			frm.action="../do/KK000ShowAction";
			break;
		case 2:
			frm.supplytype.value="01";
			frm.action="../do/KK000ShowAction";
			break;
		case 3:
			frm.supplytype.value="10";
			frm.action="../do/KK000ShowAction";
			break;
		case 4:
			frm.supplytype.value="11";
			frm.action="../do/KK000ShowAction";
			break;
	}
	frm.submit();
}

function jskakLink(i){
	var frm=document.kakForm;
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KK201ShowAction?DATATYPE=TOUROKU";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KK201ShowAction?DATATYPE=KOUKAI";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KK301ShowAction?DATATYPE=TOUROKU";
			break;
		case 4:
			frm.target="frmRIGHT";
			frm.action="../do/KK301ShowAction?DATATYPE=KOUKAI";
			break;
		case 5:
			frm.target="frmRIGHT";
			frm.action="../do/KK401ShowAction?DATATYPE=TOUROKU";
			break;
		case 6:
			frm.target="frmRIGHT";
			frm.action="../do/KK401ShowAction?DATATYPE=KOUKAI";
			break;
		case 7:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 8:
			frm.target="frmRIGHT";
			frm.action="../do/KK601ShowAction";
			break;
		case 9:
		    frm.target ="_top";
			frm.usertype.value="1";
			frm.action="../do/K000ShowAction";
			break;
		case 10:
		    frm.target ="_top";
			frm.action="../do/Accepter";  //KF000ShowAction";
			break;
		// ADD-S 2013/05/03
		// ���-���J_5-10_�������ʂ��A�b�v���[�h
    case 11:
      frm.target="frmRIGHT";
      frm.action="../do/KK201SearchAction?DATATYPE2=KBK";
      break;
		// ADD-E 2013/05/03
// ADD-S 2013/03/12
// ���-���J_5-12�����j���[�Ƀ����N�ǉ�
    case 12:
      frm.target ="_top";
      frm.action="../do/KK000ShowAction";
      break;
// ADD-E 2013/03/12
	}
	frm.submit();
}

function jskabLink(i){
	var frm=document.kabForm;
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KB301ShowAction?DATATYPE=TOUROKU";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KB301ShowAction?DATATYPE=KOUKAI";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KB401ShowAction?DATATYPE=TOUROKU";
			break;
		case 4:
			frm.target="frmRIGHT";
			frm.action="../do/KB401ShowAction?DATATYPE=KOUKAI";
			break;
		case 5:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 6:
			frm.target="frmRIGHT";
			frm.action="../do/KB601ShowAction";
			break;
		case 7:
		    frm.target ="_top";
			frm.usertype.value="1";
			frm.action="../do/K000ShowAction";
			break;
		case 8:
		    frm.target ="_top";
			frm.action="../do/Accepter";  //KF000ShowAction";
			break;
// ADD-S 2013/03/12
// ���-���J_5-12�����j���[�Ƀ����N�ǉ�
    case 9:
      frm.target ="_top";
      frm.action="../do/KK000ShowAction";
      break;
// ADD-E 2013/03/12
	}
	frm.submit();
}

function jskbkLink(i){
	var frm=document.kbkForm;
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KK201SearchAction";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KK301SearchAction";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KK401SearchAction";
			break;
		case 4:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 5:
			frm.target ="_top";
			frm.action="../do/K000ShowAction";
			break;
// ADD-S 2013/03/12
// ���-���J_5-12�����j���[�Ƀ����N�ǉ�
    case 6:
      frm.target ="_top";
      frm.action="../do/KK000ShowAction";
      break;
// ADD-E 2013/03/12
	}
	frm.submit();
}

function jskbbLink(i){
	var frm=document.kbbForm;
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KB301SearchAction";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KB401SearchAction";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 4:
			frm.target ="_top";
			frm.action="../do/K000ShowAction";
			break;
// ADD-S 2013/03/12
// ���-���J_5-12�����j���[�Ƀ����N�ǉ�
    case 5:
      frm.target ="_top";
      frm.action="../do/KK000ShowAction";
      break;
// ADD-E 2013/03/12
	}
	frm.submit();
}

function jskfkLink(i){

  var frm=document.kfkForm;
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KK201ShowAction";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KK301ShowAction";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KK311ShowAction";
			break;
		case 4:
			frm.target="frmRIGHT";
			frm.action="../do/KK401ShowAction";
			break;
		case 5:
		    frm.target="frmRIGHT";
		    frm.action="../do/KK801ShowAction";
			break;
		case 6:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 7:
		    frm.target ="_top";
			frm.action="../do/KF000ShowAction";
			break;
	}
	frm.submit();
}


function jskfbLink(i){
//DEL-S 2013/03/12
//���-���J_5-45�󒍎҃g�b�v���j���[�폜
//	var frm=document.kfbForm;
//DEL-E 2013/03/12
//ADD-S 2013/03/12
//���-���J_5-45�󒍎҃g�b�v���j���[�폜
	var frm=document.kfkForm;
//ADD-E 2013/03/12
	switch(i){
		case 1:
			frm.target="frmRIGHT";
			frm.action="../do/KB301ShowAction";
			break;
		case 2:
			frm.target="frmRIGHT";
			frm.action="../do/KB311ShowAction";
			break;
		case 3:
			frm.target="frmRIGHT";
			frm.action="../do/KB401ShowAction";
			break;
		case 4:
			frm.target="frmRIGHT";
			frm.action="../do/KB801ShowAction";
			break;
		case 5:
			frm.target="frmRIGHT";
			frm.action="../do/KK501ShowAction";
			break;
		case 6:
		    frm.target ="_top";
			frm.action="../do/KF000ShowAction";
			break;
		case 7:
			frm.target="frmRIGHT";
			frm.action="../do/KB316ShowAction";
			break;
	}
	frm.submit();
}

function jsKF(){
	var frm=document.KF000DynaActionForm;
    frm.action="../do/KF000ShowAction";
	frm.submit();
}