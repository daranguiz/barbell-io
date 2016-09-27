$(document).ready(function() {

    for (var i = 0; i < chart_id.length; i++) {
        $(chart_id[i]).highcharts({
            chart: chart[i],
            title: title[i],
            xAxis: xAxis[i],
            yAxis: yAxis[i],
            series: series[i]
        });
    }

});
