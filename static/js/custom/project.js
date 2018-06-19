/*********************************
 * Author: HuangYao
 * Content: 定义项目管理界面的动作
 *********************************/

$(document).ready(function () {
    $('#addProjectButton').click(function () {
        let svn_id = $("#svn_select").val();
        let name = $("#project_name").val().trim();
        let path = $("#project_path").val().trim();
        if (svn_id.length === 0 || name.length === 0 || path.length === 0) {
            alert("请填写必填内容");
            return false;
        }
        if (path.charAt(path.length - 1) != "/") {
            alert("本地路径必须以'/'结尾");
            return false;
        }
        let url = "/crontab_manage/cronProject/add/";
        let data = {
            'svn_id': svn_id,
            'name': name,
            'path': path,
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

    $('#deleteProjectButton').click(function () {
        let del_svn_ids = [];
        $("#editable").find(":checkbox:checked").each(function () {
            let salt_id = $(this).val();
            if (!isNaN(salt_id)){
                del_svn_ids.push(salt_id);
            }
        });

        if (del_svn_ids.length === 0) {
            alert("请选择要删除的项目");
            return false;
        }
        let url = "/crontab_manage/cronProject/del/";
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

