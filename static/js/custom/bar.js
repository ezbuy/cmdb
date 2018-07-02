/*********************************
 * Author: HuangYao
 * Content: 定义左侧导航栏动作
 *********************************/

$('.nav-second-level').find('a').each(function () {
    if (this.href == document.location.href || document.location.href.search(this.href) >= 0) {
        $(this).parent().addClass('active'); // this.className = 'active';
        $(this).parent().parent().parent().addClass('active');
    }
});

