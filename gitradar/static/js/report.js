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
        own_repo_num = 0;
    console.log("in calc_and_draw");
    console.log(repos);
    
    $.each(repos, function(i, repo){
        if (repo.fork !== false) {
            return;
        }
        own_repo_num++;

        console.log(repo.language);
        if (repo.language) {
            if (repo.language in languages) {
                languages[repo.language]++;
            } else {
                languages[repo.language] = 1;
            }
        } 
    });
    console.log(languages);

    draw_lang_pie(languages, own_repo_num);
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

function main() {
    user_repos(login, calc_and_draw);
}
