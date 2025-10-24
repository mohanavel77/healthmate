document.addEventListener('DOMContentLoaded', () => {
  // -------------------- Water Controls --------------------
  const buttons = document.querySelectorAll('.water-controls .btn');
  const todayEl = document.getElementById('today-ml');
  const fillEl = document.getElementById('fill');

  function refreshWater() {
    fetch('/api/water')
      .then(r => r.json())
      .then(rows => {
        const today = rows.reduce((s, r) => s + (r.amount_ml || 0), 0);
        todayEl.textContent = today;
        const pct = Math.min(100, Math.round((today / 2000) * 100));
        fillEl.style.height = pct + '%';
      });
  }

  buttons.forEach(b => {
    b.onclick = () => {
      const amt = parseInt(b.dataset.amt);
      fetch('/api/water', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amt })
      }).then(() => refreshWater());
    };
  });

  // -------------------- Tablet Reminder --------------------
  const tform = document.getElementById('tablet-form');
  const tlist = document.getElementById('tablets-list');

  tform.addEventListener('submit', e => {
    e.preventDefault();
    const name = document.getElementById('t-name').value;
    const dosage = document.getElementById('t-dosage').value;
    const time = document.getElementById('t-time').value;
    

    fetch('/api/tablet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, dosage, time })
    }).then(() => {
      tform.reset();
      loadTablets();
    });
  });

  function loadTablets() {
    fetch('/api/tablet')
      .then(r => r.json())
      .then(rows => {
        tlist.innerHTML = '';
        rows.forEach(r => {
          const li = document.createElement('li');
          li.textContent = `The tablet ${r.name} (${r.dosage || 'No dosage'}) is to be taken at ${r.time || 'N/A'} .`;
          tlist.appendChild(li);
        });
      });
  }

  // -------------------- Glucose Tracker --------------------
  const gform = document.getElementById('glucose-form');
  const gchart = document.getElementById('glucose-chart').getContext('2d');
  let glucoseChart = new Chart(gchart, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'mg/dL', data: [], borderColor: 'orange', fill: false, tension: 0.2 }] },
    options: { responsive: true, plugins: { legend: { display: true } } }
  });

  gform.addEventListener('submit', e => {
    e.preventDefault();
    const val = document.getElementById('g-value').value;
    fetch('/api/glucose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: val })
    }).then(() => {
      gform.reset();
      loadGlucose();
    });
  });

  function loadGlucose() {
    fetch('/api/glucose')
      .then(r => r.json())
      .then(rows => {
        glucoseChart.data.labels = rows.map(r => new Date(r.ts).toLocaleString());
        glucoseChart.data.datasets[0].data = rows.map(r => r.value);
        glucoseChart.update();
      });
  }

  // -------------------- Blood Pressure Tracker --------------------
  const bpform = document.getElementById('bp-form');
  const bpchart = document.getElementById('bp-chart').getContext('2d');
  let bpChart = new Chart(bpchart, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Systolic (mmHg)',
          data: [],
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: false,
          tension: 0.2
        },
        {
          label: 'Diastolic (mmHg)',
          data: [],
          borderColor: 'rgba(153, 102, 255, 1)',
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          fill: false,
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: {
        x: { title: { display: true, text: 'Time' } },
        y: { title: { display: true, text: 'mmHg' }, beginAtZero: false }
      }
    }
  });

  bpform.addEventListener('submit', e => {
    e.preventDefault();
    const systolic = parseInt(document.getElementById('bp-systolic').value);
    const diastolic = parseInt(document.getElementById('bp-diastolic').value);

    if (!systolic || !diastolic) return alert('Please enter valid numbers!');

    fetch('/api/bp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ systolic, diastolic })
    }).then(() => {
      bpform.reset();
      loadBP();
    });
  });

  function loadBP() {
    fetch('/api/bp')
      .then(r => r.json())
      .then(rows => {
        bpChart.data.labels = rows.map(r => new Date(r.ts).toLocaleString());
        bpChart.data.datasets[0].data = rows.map(r => r.systolic);
        bpChart.data.datasets[1].data = rows.map(r => r.diastolic);
        bpChart.update();
      });
  }

  // -------------------- Initial Load --------------------
  refreshWater();
  loadTablets();
  loadGlucose();
  loadBP();
});
