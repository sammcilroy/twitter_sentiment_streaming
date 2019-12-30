var ctx = document.getElementById('influencers_chart').getContext('2d');
var influencers_chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Tagged in Tweets',
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

src_data_influencers_labels = [];
src_data_influencers_counts = [];

setInterval(function(){
    $.getJSON('/refresh_influencers', {
    }, function(data) {
        src_data_influencers_labels = data.Label;
        src_data_influencers_counts = data.Count;
    });
    influencers_chart.data.labels = src_data_influencers_labels;
    influencers_chart.data.datasets[0].data = src_data_influencers_counts;
    influencers_chart.update();
},2000);
