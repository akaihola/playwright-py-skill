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
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'a') {
        log('keydown', 'Ctrl+A');
      } else if (e.key === 'c') {
        log('keydown', 'Ctrl+C');
      } else if (e.key === 'v') {
        log('keydown', 'Ctrl+V');
      }
    }
  });

  comboInput.addEventListener('select', function(e) {
    log('select', comboInput.value);
  });

  // Special keys events
  specialInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      log('keydown', 'Enter');
    } else if (e.key === 'Tab') {
      log('keydown', 'Tab');
    } else if (e.key === 'Escape') {
      log('keydown', 'Escape');
    } else if (e.key === 'ArrowDown') {
      log('keydown', 'ArrowDown');
    }
  });
}

document.addEventListener('DOMContentLoaded', setupEventListeners);
