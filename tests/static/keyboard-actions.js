window.actionLog = document.getElementById('action-log');

function log(type, details) {
  details = details || '';
  window.actionLog.textContent += type + (details ? ' ' + details : '') + '\n';
}

function setupEventListeners() {
  var typeInput = document.getElementById('type-input');
  var comboInput = document.getElementById('combo-input');
  var specialInput = document.getElementById('special-input');

  // Type with delay events (input event)
  typeInput.addEventListener('input', function(e) {
    log('type', typeInput.value);
  });

  // Key combinations events
  comboInput.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === 'a' || e.key === 'A' || e.key === 'c' || e.key === 'C' || e.key === 'v' || e.key === 'V')) {
      log('keydown', 'Ctrl+' + e.key.toUpperCase());
    }
  });

  comboInput.addEventListener('select', function(e) {
    log('select', comboInput.value);
  });

  // Special keys events
  specialInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      log('keydown', 'Enter');
    } else if (e.key === 'Tab') {
      e.preventDefault();
      log('keydown', 'Tab');
    } else if (e.key === 'Escape') {
      e.preventDefault();
      log('keydown', 'Escape');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      log('keydown', 'ArrowDown');
    }
  });
}

document.addEventListener('DOMContentLoaded', setupEventListeners);
