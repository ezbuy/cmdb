/*********************************
 * Author: HuangYao
 * Content: 定义svn管理界面的动作
 *********************************/

$(document).ready(function () {
    $('#addSvnButton').click(function () {
        let project_name = $("#project_name").val();
        let salt_id = $("#salt_minion").val();
        let repo = $("#repo").val().trim();
        let local_path = $("#local_path").val().trim();
        let username = $("#username").val().trim();
        let password = $("#password").val().trim();
        if (project_name.length == 0 || salt_id.length === 0 || repo.length === 0 || local_path.length === 0) {
            alert("请填写必填内容");
            return false;
        }
        let url = "/crontab_manage/cronSvn/add/";
        let data = {
            'salt_id': salt_id,
            'project_name': project_name,
            'repo': repo,
            'local_path': local_path,
            'username': username,
            'password': password,
        };
        $.ajax({
            url: url,
            type: "POST",
            data: data,
            contentType: 'application/x-www-form-urlencoded',
            traditional: true,
            success: function (result) {
                if (result.code === 0) {
                    window.location.reload();
                }
                else {
                    alert(result.msg)
                }
            },
            error: function () {
                alert('失败');
            }
        });
    });

    $('#deleteSvnButton').click(function () {
        let del_salt_ids = [];
        $("#editable").find(":checkbox:checked").each(function () {
            let salt_id = $(this).val();
            if (!isNaN(salt_id)){
                del_salt_ids.push(salt_id);
            }
        });

        if (del_salt_ids.length === 0) {
            alert("请选择要删除的svn");
            return false;
        }
        let url = "/crontab_manage/cronSvn/del/";
        let data = {
            'salt_ids': del_salt_ids,
        };
        $.ajax({
            url: url,
            type: "POST",
            data: data,
            contentType: 'application/x-www-form-urlencoded',
            traditional: true,
            success: function (result) {
                if (result.code === 0) {
                    window.location.reload();
                }
                else {
                    alert(result.msg)
                }
            },
            error: function () {
                alert('失败');
            }
        });
    });

});

