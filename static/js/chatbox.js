// chatbox.js - simple chat UI and fetch to /api/chat
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('chat-toggle');
  const windowEl = document.getElementById('chat-window');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messagesEl = document.getElementById('chat-messages');
  const closeBtn = document.getElementById('chat-close');

  function appendMessage(author, text) {
    const m = document.createElement('div');
    m.className = 'chat-msg ' + (author === 'user' ? 'from-user' : 'from-bot');
    m.innerHTML = '<div class="author">' + (author === 'user' ? 'You' : 'Assistant') + '</div><div class="text"></div>';
    m.querySelector('.text').textContent = text;
    messagesEl.appendChild(m);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  toggle.addEventListener('click', () => {
    windowEl.classList.toggle('hidden');
    input.focus();
  });
  if (closeBtn) closeBtn.addEventListener('click', () => windowEl.classList.add('hidden'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    appendMessage('user', text);
    input.value = '';
    appendMessage('bot', 'Typing…');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      // remove the "Typing…" placeholder
      const placeholders = messagesEl.querySelectorAll('.from-bot');
      if (placeholders.length) placeholders[placeholders.length - 1].remove();

      if (res.ok && data.reply) {
        appendMessage('bot', data.reply);
      } else {
        appendMessage('bot', data.error || 'Error from server');
      }
    } catch (err) {
      // remove placeholder
      const placeholders = messagesEl.querySelectorAll('.from-bot');
      if (placeholders.length) placeholders[placeholders.length - 1].remove();
      appendMessage('bot', 'Network error');
      console.error(err);
    }
  });
});