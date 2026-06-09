// ==================== LINE CHART VISUALIZATION ====================

/**
 * Instantiates or updates the Chart.js line chart for historical and projected stock paths.
 * @param {Array<number>} historical - 13 data points (Months -12 to 0)
 * @param {Array<number>} projected - 7 data points (Months 0 to 6)
 */
function renderChart(historical, projected) {
  const ctx = document.getElementById('projectionChart').getContext('2d');
  
  // Destroy existing chart if it exists to avoid overlapping canvases
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  // Build chart labels
  const labels = [];
  for (let i = 12; i > 0; i--) {
    labels.push(`Month -${i}`);
  }
  labels.push("Current (0)");
  for (let i = 1; i <= 6; i++) {
    labels.push(`Month +${i}`);
  }
  
  // Map historical prices: first 13 elements, then nulls for projection range
  const histData = [...historical];
  while (histData.length < labels.length) {
    histData.push(null);
  }
  
  // Map projected prices: 12 nulls, then 7 elements (overlapping at current month 0)
  const projData = Array(12).fill(null).concat(projected);
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Historical Trend',
          data: histData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.05)',
          borderWidth: 3,
          pointBackgroundColor: '#3b82f6',
          fill: true,
          tension: 0.1
        },
        {
          label: 'Future Swarm Projection',
          data: projData,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.05)',
          borderDash: [6, 4],
          borderWidth: 3,
          pointBackgroundColor: '#06b6d4',
          fill: true,
          tension: 0.1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8',
            font: { family: 'Outfit', size: 12 }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
        }
      }
    }
  });
}
