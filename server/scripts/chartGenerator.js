// chartGenerator.js

function generateChart(datasets, labels, chartTitle, chartType, minY, maxY) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  const settings = {
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
  };
  if (minY !== null) settings.options.scales.y.suggestedMin = minY;
  if (maxY !== null) settings.options.scales.y.suggestedMax = maxY;
  if (minY === null) settings.options.scales.y.beginAtZero = true;
  else settings.options.scales.y.beginAtZero = false;

  const chart = new Chart(ctx, settings);

  return canvas;
}
