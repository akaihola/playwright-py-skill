window.actionLog = document.getElementById('action-log');

function log(type, id, details) {
  details = details || '';
  window.actionLog.textContent += type + ' ' + id + (details ? ' ' + details : '') + '\n';
}

function setupEventListeners() {
  var button = document.getElementById('test-button');
  var menuItem = document.getElementById('menu-item');
  var source = document.getElementById('source');
  var target = document.getElementById('target');

  // Click events on button
  button.addEventListener('click', function(e) {
    var msg = 'x=' + e.offsetX + ',y=' + e.offsetY;
    log('click', 'test-button', msg);
  });

  button.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    log('contextmenu', 'test-button');
  });

  button.addEventListener('dblclick', function(e) {
    log('dblclick', 'test-button');
  });

  // Hover event
  menuItem.addEventListener('mouseenter', function(e) {
    log('hover', 'menu-item');
  });

  // Drag and drop events
  source.addEventListener('dragstart', function(e) {
    log('dragstart', 'source');
  });

  target.addEventListener('drop', function(e) {
    e.preventDefault();
    log('drop', 'target');
  });

  target.addEventListener('dragover', function(e) {
    e.preventDefault(); // Required to allow dropping
  });
}

document.addEventListener('DOMContentLoaded', setupEventListeners);
