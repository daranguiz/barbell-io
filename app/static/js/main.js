$(document).ready(function() {

    if (typeof chart_id != "undefined") {
        for (var i = 0; i < chart_id.length; i++) {
            var curChart = $(chart_id[i]).highcharts({
                chart: chart[i],
                title: title[i],
                xAxis: xAxis[i],
                yAxis: yAxis[i],
                plotOptions: plotOptions[i],
                series: series[i]
            });
        }
    }

});
