function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {

    // 关注当前新闻作者
    $(".focus").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "follow",
            "user_id": user_id
        }
        $.ajax({
            url: "/news/followed_user",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 关注成功
                    var count = parseInt($(".follows b").html());
                    count++;
                    $(".follows b").html(count + "")
                    $(".focus").hide()
                    $(".focused").show()
                } else if (resp.errno == "4101") {
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                } else {
                    // 关注失败
                    alert(resp.errmsg)
                }
            }
        })
    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "unfollow",
            "user_id": user_id
        }
        $.ajax({
            url: "/news/followed_user",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 取消关注成功
                    var count = parseInt($(".follows b").html());
                    count--;
                    $(".follows b").html(count + "")
                    $(".focus").show()
                    $(".focused").hide()
                } else if (resp.errno == "4101") {
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                } else {
                    // 取消关注失败
                    alert(resp.errmsg)
                }
            }
        })
    })
})