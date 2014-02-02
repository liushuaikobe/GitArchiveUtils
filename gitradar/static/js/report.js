var login, div_id;

function set_login(user_login) {
    login = user_login;
} 

function set_pie_div(pie_div_id) {
    div_id = pie_div_id;
    console.log("div =>" + pie_div_id);
}

function user_repos(login, callback, page_number, prev_data) {
    var page = (page_number ? page_number : 1),
        url = "https://api.github.com/users/" + login + "/repos",
        data = (prev_data ? prev_data : []);

    url += "?page=" + page;

    console.log("login =>" + login);
    console.log(url);
    
    $.getJSON(url, function(repos){
        data = data.concat(repos);

        if (repos.length > 0) {
            user_repos(login, callback, page + 1, data);
        } else {
            callback(login, data);
        }
    });
}

function calc_and_draw(login, repos) {
    var languages = {},
        sorted_repos = [],
        sort_repos_limit = 5,
        own_repo_num = 0;
    
    $.each(repos, function(i, repo){

        sorted_repos.push({
            'name': repo.full_name,
            'url': repo.html_url,
            'watchers': repo.watchers,
            'forks': repo.forks,
            'language': repo.language,
            'description': repo.description,
            'created_at': repo.created_at,
            'created_at_year': repo.created_at.slice(0, 4),
            'popularity': repo.watchers + repo.forks
        });

        if (repo.fork !== false) {
            return;
        }
        own_repo_num++;

        if (repo.language) {
            if (repo.language in languages) {
                languages[repo.language]++;
            } else {
                languages[repo.language] = 1;
            }
        } 
    });

    sorted_repos.sort(function (a, b) {
        return b.popularity - a.popularity;
    });
    sorted_repos = sorted_repos.slice(0, sort_repos_limit);
    console.log(sorted_repos);

    draw_lang_pie(languages, own_repo_num);
    write_popular_repos(sorted_repos);
}

function draw_lang_pie(languages, own_repo_num) {
    var highchart_pie_data = [];
    for (lang in languages) {
        highchart_pie_data.push([lang, languages[lang]]);
    }

    console.log(highchart_pie_data);
    if (highchart_pie_data.length == 0) {
        $("#" + div_id).html("<p>We can't figure out the programming language of his/her repos.</p>")
        return;
    }

    $("#" + div_id).highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false
        }, 
        title: {
            text: "Programming Language Statistics on " + own_repo_num + " Repos"
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %'
                }
            }
        },
        series: [{
            type: 'pie',
            name: 'percentage',
            data: highchart_pie_data
        }]
    });
}

function write_popular_repos(sorted_repos) {
    if (sorted_repos.length == 0) {
        $("#popular-repos-p").html("There isn't any repo to display.");
        return ;
    }    

    var item_template = 
        '<div class="item"> \
            <div class="right floated ui label"> \
                <i class="fork code icon"></i> {{ forks }} \
                <i class="star icon"></i> {{ watchers }} \
            </div> \
            <div class="content"> \
                <div class="header"> \
                    <a href={{ url }}>{{ name }}</a> \
                </div> \
                {{ language }} - created at {{ created_at_year }} </br> \
                {{ description }} \
            </div> \
        </div>';

    $.each(sorted_repos, function(i, repo){
        $("#popular-repos-list").append(
            item_template.replace(/{{ (\w*) }}/g, function(m, key){
                return repo.hasOwnProperty(key) ? repo[key] : ""; 
        }));
    });
}

function main() {
    user_repos(login, calc_and_draw);
}
