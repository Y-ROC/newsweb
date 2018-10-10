$(function() {
    var source = $("#pagination").attr('source')
    var cur_page = $("#pagination").attr('cur_page')
    var total_page = $("#pagination").attr('total_page')
    $("#pagination").pagination({
        currentPage: parseInt(cur_page),
        totalPage: parseInt(total_page),
        callback: function(current) {
            location.href = source + "?p=" + current
        }
    });
});