var current_last_user_val,
    current_last_user_login,
    current_last_user_index;
var each_page_num = 15;

function set_last_user_val(last_user_val) {
    current_last_user_val = last_user_val;
}

function set_last_user_login(last_user_login) {
    current_last_user_login = last_user_login;
}

function set_last_user_index(last_user_index) { 
    current_last_user_index = last_user_index;
}

function append_rank_list(html) {
    $("#rank-list").append(html);
}

function load_rank(last_val, last_login, last_index, num) {
    var item_template = 
        '<div class="item"> \
            <div class="right floated tiny teal">{{ val }}</div> \
            <div class="left floated"> \
                {{ index }} \
            </div> \
            <img class="ui avatar image" src="http://www.gravatar.com/avatar/{{ gravatar_id }}"> \
            <div class="content"> \
                <a href="/report/{{ login }}" class="header">{{ login }}</a>({{ name }}) \
                <div class="description"></div> \
            </div> \
        </div>';
    var url = window.location.pathname;
    var data = {
        "since_val": (last_val ? last_val : null),
        "since_name": (last_login ? last_login : null),
        "since_index": (last_index ? last_index : null),
        "num": num
    };
    $.getJSON(url, data,  
        function(actor_list){
            $.each(actor_list, function(i, actor){
                var item = item_template.replace(/{{ (\w*) }}/g, function(m, key){
                    return actor.hasOwnProperty(key) ? actor[key] : "N/A";
                });
                append_rank_list(item);
                if (i === actor_list.length - 1) {
                    current_last_user_login = actor.login;
                    current_last_user_val = actor.val;
                    current_last_user_index = actor.index;
                    console.log(current_last_user_index);
                }
            });
        }
    );
}

$(function() {
    $("#load-more").click(function() {
        load_rank(current_last_user_val, current_last_user_login, current_last_user_index, each_page_num);
    });
});
