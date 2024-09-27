// chartGenerator.js

function generateChart(datasets, labels, chartTitle, chartType) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  const chart = new Chart(ctx, {
    type: chartType,
    data: {
      labels: labels, // X-axis labels
      datasets: datasets, // Now accepting multiple datasets
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      animation: {
        duration: 0, // Disable animations
      },
      // plugins: {
      //   title: {
      //     display: true,
      //     text: chartTitle,
      //   },
      // },
    },
  });

  return canvas;
}
