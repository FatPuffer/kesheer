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
     // 查询用户实名认证信息
    $.get("/api/v1.0/users/auth", function(resp){
        // 4101表示用户未登录
        if ("4101" == resp.errno) {
            location.href = "/login.html";
        }else if ("0" == resp.errno) {
            // 如果返回的数据中real_name与id_card不为null，表示有填写实名信息
            if (resp.data.real_name && resp.id_card){
                $("#real_name").val(resp.data.real_name);
                $("#id_card").val(resp.data.id_card);
                // 给input添加disable属性，禁止用户修改
                $("#real_name").prop("disabled", true);
                $("#id_card").prop("disabled", true);
                // 隐藏提交保存按钮
                $("#form-auth>input[type=submit]").hide();
            }
        }else {
            alert(resp.errmsg);
        }
    }, "json");

    // 管理实名信息表单的提交行为
    $("#form-auth").submit(function(e){
        e.preventDefault();
        var realName = $("#real-name").val();
        var idCard = $("#id-card").val();
        if (realName == "" || idCard == ""){
            $(".error-msg").show()
        }
    })
})
