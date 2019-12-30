var ctx = document.getElementById('trending_chart').getContext('2d');
var trending_chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Hashtags',
            data: [],
            backgroundColor:' #af90ca',
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                    callback: function(value) {if (value % 1 === 0) {return value;}}
                }
            }]
        }
    }
});

var src_data_trending= {
    labels: [],
    counts: []
}

setInterval(function(){
    $.getJSON('/refresh_trending', {
    }, function(data) {
        src_data_trending.labels = data.Label;
        src_data_trending.counts = data.Count;
    });
    trending_chart.data.labels = src_data_trending.labels;
    trending_chart.data.datasets[0].data = src_data_trending.counts;
    trending_chart.update();
},2000);