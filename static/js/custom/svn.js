/*********************************
 * Author: HuangYao
 * Content: 定义svn管理界面的动作
 *********************************/

$(document).ready(function () {
    $('#addSvnButton').click(function () {
        let url = "/project_contab/cronSvn/";
        let data = "";
        $.ajax({
            url: url,
            type: "POST",
            data: data,
            enctype: "multipart/form-data",
            processData: false,
            contentType: false,
        }).done(function (result) {
            if (result.status === 'ok') {
                window.location.reload();
            }
            else {
                alert(result.msg)
            }
        });
    });
});

