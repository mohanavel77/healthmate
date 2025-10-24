// static/js/reminder.js
document.getElementById("reminderForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    tablet_name: document.getElementById("tablet_name").value,
    time: document.getElementById("time").value,
    days: document.getElementById("days").value,
    user_phone: document.getElementById("user_phone").value
  };

  const res = await fetch("/add_reminder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  const result = await res.json();
  document.getElementById("responseMsg").innerText = result.message;
});
