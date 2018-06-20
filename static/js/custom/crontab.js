/*********************************
 * Author: HuangYao
 * Content: 定义crontab管理界面的动作
 *********************************/

$(document).ready(function () {
    $('#addCrontabButton').click(function () {
        let project_id = $("#project_select").val();
        let cmd = $("#cmd").val().trim();
        let frequency = $("#frequency").val().trim();
        if (project_id.length === 0 || cmd.length === 0 || frequency.length === 0) {
            alert("请填写必填内容");
            return false;
        }
        let url = "/crontab_manage/cronList/add/";
        let data = {
            'project_id': project_id,
            'cmd': cmd,
            'frequency': frequency,
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

    $('#deleteCrontabButton').click(function () {
        let del_svn_ids = [];
        $("#editable").find(":checkbox:checked").each(function () {
            let salt_id = $(this).val();
            if (!isNaN(salt_id)){
                del_svn_ids.push(salt_id);
            }
        });

        if (del_svn_ids.length === 0) {
            alert("请选择要删除的crontab");
            return false;
        }
        let url = "/crontab_manage/cronList/del/";
        let data = {
            'svn_ids': del_svn_ids,
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

function pauseCrontab(crontab_id) {
    alert('pause '+crontab_id);
}

function startCrontab(crontab_id) {
    alert('start '+crontab_id);
}