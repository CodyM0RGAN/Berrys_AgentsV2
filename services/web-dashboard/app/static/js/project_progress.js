document.addEventListener('DOMContentLoaded', function () {
    // Get chart data from the data attributes
    const progressDates = JSON.parse(document.getElementById('progress-chart').dataset.dates);
    const progressPlanned = JSON.parse(document.getElementById('progress-chart').dataset.planned);
    const progressActual = JSON.parse(document.getElementById('progress-chart').dataset.actual);
    const agentTimeline = JSON.parse(document.getElementById('timeline-chart').dataset.timeline);

    // Progress Chart
    const progressCtx = document.getElementById('progress-chart').getContext('2d');
    const progressData = {
        labels: progressDates,
        datasets: [
            {
                label: 'Planned Progress',
                data: progressPlanned,
                borderColor: '#6c757d',
                backgroundColor: 'rgba(108, 117, 125, 0.1)',
                borderDash: [5, 5],
                fill: false,
                tension: 0.1
            },
            {
                label: 'Actual Progress',
                data: progressActual,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                fill: true,
                tension: 0.1
            }
        ]
    };

    const progressOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day',
                    displayFormats: {
                        day: 'MMM D'
                    }
                },
                title: {
                    display: true,
                    text: 'Date'
                }
            },
            y: {
                beginAtZero: true,
                max: 100,
                title: {
                    display: true,
                    text: 'Progress (%)'
                }
            }
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false
            },
            legend: {
                position: 'top'
            }
        }
    };

    const progressChart = new Chart(progressCtx, {
        type: 'line',
        data: progressData,
        options: progressOptions
    });

    // Agent Timeline Chart
    const timelineCtx = document.getElementById('timeline-chart').getContext('2d');
    const timelineData = {
        datasets: agentTimeline
    };

    const timelineOptions = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day',
                    displayFormats: {
                        day: 'MMM D'
                    }
                },
                title: {
                    display: true,
                    text: 'Date'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Agent'
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const task = context.raw.task;
                        return `${task}: ${moment(context.raw.start).format('MMM D')} - ${moment(context.raw.end).format('MMM D')}`;
                    }
                }
            },
            legend: {
                display: false
            }
        }
    };

    const timelineChart = new Chart(timelineCtx, {
        type: 'bar',
        data: timelineData,
        options: timelineOptions
    });
});
