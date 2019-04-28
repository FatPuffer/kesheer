function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
     // ��ѯ�û�ʵ����֤��Ϣ
    $.get("/api/v1.0/users/auth", function(resp){
        // 4101��ʾ�û�δ��¼
        if ("4101" == resp.errno) {
            location.href = "/login.html";
        }else if ("0" == resp.errno) {
            // ������ص�������real_name��id_card��Ϊnull����ʾ����дʵ����Ϣ
            if (resp.data.real_name && resp.id_card){
                $("#real_name").val(resp.data.real_name);
                $("#id_card").val(resp.data.id_card);
                // ��input���disable���ԣ���ֹ�û��޸�
                $("#real_name").prop("disabled", true);
                $("#id_card").prop("disabled", true);
                // �����ύ���水ť
                $("#form-auth>input[type=submit]").hide();
            }
        }else {
            alert(resp.errmsg);
        }
    }, "json");

    // ����ʵ����Ϣ�����ύ��Ϊ
    $("#form-auth").submit(function(e){
        e.preventDefault();
        var realName = $("#real-name").val();
        var idCard = $("#id-card").val();
        if (realName == "" || idCard == ""){
            $(".error-msg").show()
        }
    })
})
