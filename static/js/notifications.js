function showNotification() {
  const notification = document.querySelector('.notification');
  if (notification) {
    setTimeout(() => {
      notification.classList.add('show');
    }, 100);

    setTimeout(() => {
      notification.classList.remove('show');
    }, 4000);
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

