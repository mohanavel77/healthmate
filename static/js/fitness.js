
document.addEventListener('DOMContentLoaded', ()=>{
  // calorie calc - Mifflin St Jeor
  document.getElementById('calc-calories').addEventListener('click', ()=>{
    const age = parseFloat(document.getElementById('cal-age').value) || 30;
    const gender = (document.getElementById('cal-gender').value||'male').toLowerCase();
    const weight = parseFloat(document.getElementById('cal-weight').value) || 70;
    const height = parseFloat(document.getElementById('cal-height').value) || 170;
    const act = parseFloat(document.getElementById('cal-activity').value) || 1.2;
    let bmr = (10*weight) + (6.25*height) - (5*age) + (gender==='male'?5:-161);
    const calories = Math.round(bmr * act);
    document.getElementById('cal-result').textContent = 'Estimated calories/day: ' + calories;
  });

  // simple weight tracker saved in localStorage for demo (can be server-backed)
  const wform = document.getElementById('weight-form');
  const ctx = document.getElementById('weight-chart').getContext('2d');
  let weightChart = new Chart(ctx, {type:'line', data:{labels:[],datasets:[{label:'kg',data:[]}]}, options:{}});
  wform.addEventListener('submit', e=>{
    e.preventDefault();
    const v = parseFloat(document.getElementById('w-value').value);
    if(!v) return;
    let arr = JSON.parse(localStorage.getItem('weights')||'[]');
    arr.push({ts:new Date().toISOString(),v});
    localStorage.setItem('weights', JSON.stringify(arr));
    loadWeights();
  });
  function loadWeights(){
    let arr = JSON.parse(localStorage.getItem('weights')||'[]');
    weightChart.data.labels = arr.map(a=> new Date(a.ts).toLocaleDateString());
    weightChart.data.datasets[0].data = arr.map(a=> a.v);
    weightChart.update();
  }

  // workouts timer
  let timer = null, seconds = 0;
  document.querySelectorAll('.start-workout').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      seconds = 0;
      clearInterval(timer);
      timer = setInterval(()=> {
        seconds++;
        const mm = String(Math.floor(seconds/60)).padStart(2,'0');
        const ss = String(seconds%60).padStart(2,'0');
        document.getElementById('workout-timer').textContent = `${mm}:${ss}`;
      },1000);
    });
  });
document.querySelectorAll('.stop-workout').forEach(btn => {
  btn.addEventListener('click', () => {
    clearInterval(timer); // Stop the timer
    timer = null;
  });
});
document.querySelectorAll('.reset-workout').forEach(btn => {
  btn.addEventListener('click', () => {
    clearInterval(timer);
    timer = null;
    seconds = 0;
    document.getElementById('workout-timer').textContent = `00:00`;
  });
});
  loadWeights();
});
