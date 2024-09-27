/**
 * ownChartGenerator.js
 * This file contains a function to generate a simple chart on a canvas element without using external libraries.
 * It returns the canvas object containing the drawn chart.
 */

/**
 * Function to generate a chart on a canvas and return it
 * @param {Array} data - The data points for the chart
 * @param {Array} labels - The labels for the X-axis
 * @param {String} title - The title of the chart
 * @param {String} chartType - The type of the chart (default: "line")
 * @returns {HTMLCanvasElement} The canvas element with the drawn chart
 */
function generateChart(data, labels, title, chartType = "line") {
  // Create a canvas element
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Set canvas dimensions
  canvas.width = 400; // Set width as needed
  canvas.height = 300; // Set height as needed

  // Draw the chart
  drawChart(ctx, data, labels, title, chartType);

  // Return the canvas element with the chart
  return canvas;
}

/**
 * Function to draw the chart
 * @param {CanvasRenderingContext2D} ctx - The canvas rendering context
 * @param {Array} data - The data points for the chart
 * @param {Array} labels - The labels for the X-axis
 * @param {String} title - The title of the chart
 * @param {String} chartType - The type of the chart
 */
function drawChart(ctx, data, labels, title, chartType) {
  const margin = 50; // Margin for the chart
  const width = ctx.canvas.width - margin * 2; // Chart width
  const height = ctx.canvas.height - margin * 2; // Chart height
  const maxDataValue = Math.max(...data); // Maximum value in data

  // Draw axes
  ctx.beginPath();
  ctx.moveTo(margin, margin + height);
  ctx.lineTo(margin, margin);
  ctx.lineTo(margin + width, margin + height);
  ctx.stroke();

  // Draw title
  ctx.font = "16px Arial";
  ctx.fillText(title, margin + width / 2 - ctx.measureText(title).width / 2, margin - 10);

  // Draw labels on X-axis
  labels.forEach((label, index) => {
    const x = margin + (index * width) / (labels.length - 1);
    ctx.fillText(label, x, margin + height + 20);
  });

  // Draw data points and lines
  ctx.beginPath();
  data.forEach((value, index) => {
    const x = margin + (index * width) / (data.length - 1);
    const y = margin + height - (value / maxDataValue) * height;
    ctx.lineTo(x, y);
  });
  ctx.strokeStyle = "rgba(75, 192, 192, 1)";
  ctx.stroke();

  // Optionally fill the area below the line
  ctx.lineTo(margin + width, margin + height);
  ctx.lineTo(margin, margin + height);
  ctx.fillStyle = "rgba(75, 192, 192, 0.2)";
  ctx.fill();
}

// Example usage
// const canvasElement = generateChart([10, 20, 30, 40], ['A', 'B', 'C', 'D'], 'My Chart');
