function showNotification(message = '') {
  const notification = document.querySelector('.notification');
  if (notification) {
    notification.textContent = message;
    notification.style.display = 'block';

    setTimeout(() => {
      notification.classList.add('show');
    }, 100);

    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        notification.style.display = 'none';
      }, 400);
    }, 2000);
  }
}

function cartNotification(text) {
  const note = document.createElement('div');
  note.className = 'notification';
  note.textContent = text;
  document.body.appendChild(note);

  requestAnimationFrame(() => {
    note.classList.add('show');
  });

  setTimeout(() => {
    note.classList.remove('show');
  }, 4000);

  setTimeout(() => {
    note.remove();
  }, 4500);
}

