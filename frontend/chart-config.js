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
}

let sentimentChartInstance = null;

/**
 * Renders the 30-turn Swarm Sentiment & Conviction trajectory chart.
 * @param {Array<Object>} transcript - The 30 debate turns.
 */
function renderSwarmSentimentChart(transcript) {
  const canvas = document.getElementById('sentimentTrajectoryChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (sentimentChartInstance) {
    sentimentChartInstance.destroy();
  }

  if (!transcript || transcript.length === 0) return;

  const labels = transcript.map(t => `Turn #${t.turn}`);
  const sentimentData = transcript.map(t => parseFloat(t.sentiment_after || 0.0));
  const convictionData = transcript.map(t => (parseFloat(t.conviction_after || 0.5) * 100));

  sentimentChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Swarm Sentiment (-1.0 to +1.0)',
          data: sentimentData,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#10b981',
          pointRadius: 4,
          fill: true,
          tension: 0.3,
          yAxisID: 'y'
        },
        {
          label: 'Swarm Conviction % (0% to 100%)',
          data: convictionData,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.05)',
          borderWidth: 2,
          borderDash: [5, 5],
          pointBackgroundColor: '#6366f1',
          pointRadius: 3,
          fill: false,
          tension: 0.3,
          yAxisID: 'y1'
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
          type: 'linear',
          display: true,
          position: 'left',
          min: -1.0,
          max: 1.0,
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#10b981', font: { family: 'Inter', size: 10 } },
          title: { display: true, text: 'Sentiment (-1.0 to +1.0)', color: '#10b981' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          min: 0,
          max: 100,
          grid: { drawOnChartArea: false },
          ticks: { color: '#6366f1', font: { family: 'Inter', size: 10 } },
          title: { display: true, text: 'Conviction %', color: '#6366f1' }
        }
      }
    }
  });
}

