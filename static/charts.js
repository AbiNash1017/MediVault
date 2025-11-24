// Utility: create pie chart
export function createPieChart(ctx, labels, values) {
  return new Chart(ctx, {
    type: "pie",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: [
          "#2563eb", "#10b981", "#f59e0b", "#ef4444",
          "#8b5cf6", "#ec4899", "#14b8a6"
        ]
      }]
    }
  });
}

// Utility: create bar chart
export function createBarChart(ctx, labels, values) {
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Quantity",
        data: values,
        backgroundColor: "#2563eb"
      }]
    },
    options: {
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}
// Attach utilities to window for simple usage (non-module)
window.createPieChart = function(ctx, labels, values) {
  return new Chart(ctx, {
    type: 'pie',
    data: { labels: labels, datasets: [{ data: values }] }
  });
};

window.createBarChart = function(ctx, labels, values) {
  return new Chart(ctx, {
    type: 'bar',
    data: { labels: labels, datasets: [{ data: values }] },
    options: { scales: { y: { beginAtZero: true } } }
  });
};
