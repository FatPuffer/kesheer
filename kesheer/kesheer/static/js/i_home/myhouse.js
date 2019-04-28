$(document).ready(function(){
    // ���ڷ�����Դ��ֻ����֤����û��ſ��ԣ��������ж��û���ʵ����֤״̬
    $.get("/api/v1.0/users/auth", function (resp) {
        if ("4001" == resp.errno){
            // �û�δ��¼
            location.href = "/login.html";
        } else if ("0" == resp.errno) {
            // δ��֤���û�����ҳ����չʾ��ȥ��֤����ť
            if (!(resp.data.real_name && resp.data.id_card)) {
                $(".auth-warn").show();
                return
            }
            // ����֤���û���������֮ǰ�����ķ�Դ��Ϣ
            $.get("/api/v1.0/user/houses", function (resp) {
                if ("0" == resp.errno) {
                    $("#houses-list").html(template("houses-list-tmpl", {house:resp.data.houses}))
                } else {
                    $("#houses-list").html(template("houses-list-tmpl", {house:[]}))
                }
            });
        }
    });

})