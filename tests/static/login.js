// Log form field interactions for test verification
function log(type, selector, value) {
  const logElement = document.getElementById('action-log');
  logElement.textContent += `${type} ${selector} ${value}\n`;
}

function setupEventListeners() {
  const emailInput = document.querySelector('input[name="email"]');
  const passwordInput = document.querySelector('input[name="password"]');
  const submitButton = document.querySelector('button[type="submit"]');

  log('load', 'login-page', '');

  emailInput.addEventListener('input', (e) => {
    log('fill', 'email', e.target.value);
  });

  emailInput.addEventListener('change', (e) => {
    log('change', 'email', e.target.value);
  });

  passwordInput.addEventListener('input', (e) => {
    log('fill', 'password', e.target.value);
  });

  passwordInput.addEventListener('change', (e) => {
    log('change', 'password', e.target.value);
  });

  submitButton.addEventListener('click', () => {
    log('click', 'submit-button', '');
  });
}

document.addEventListener('DOMContentLoaded', setupEventListeners);
