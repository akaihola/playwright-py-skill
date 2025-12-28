window.actionLog = document.getElementById("action-log");

function log(type, id, value) {
  value = value || "";
  window.actionLog.textContent +=
    type + " " + id + (value ? " " + value : "") + "\n";
}

function setupEventListeners() {
  // Text inputs
  var textInputs = document.querySelectorAll("input[type='text'], input[type='email']");
  textInputs.forEach(function (input) {
    input.addEventListener("input", function (e) {
      log("fill", this.id, this.value);
    });

    input.addEventListener("change", function (e) {
      log("change", this.id, this.value);
    });
  });

  // Checkboxes
  var checkboxes = document.querySelectorAll("input[type='checkbox']");
  checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener("change", function (e) {
      var action = this.checked ? "check" : "uncheck";
      log(action, this.id);
    });
  });

  // Radio buttons
  var radioButtons = document.querySelectorAll("input[type='radio']");
  radioButtons.forEach(function (radio) {
    radio.addEventListener("change", function (e) {
      log("select", this.name, this.value);
    });
  });

  // Select dropdowns (single and multi)
  var selects = document.querySelectorAll("select");
  selects.forEach(function (select) {
    select.addEventListener("change", function (e) {
      var selectedOptions = Array.from(this.selectedOptions).map(function (opt) {
        return opt.value;
      });
      log("select", this.id, selectedOptions.join(","));
    });
  });

  // File upload
  var fileInput = document.getElementById("file-upload");
  fileInput.addEventListener("change", function (e) {
    var files = Array.from(this.files);
    var fileNames = files.map(function (file) {
      return file.name + ":" + file.size;
    });
    log("upload", this.id, fileNames.join(","));
  });
}

document.addEventListener("DOMContentLoaded", setupEventListeners);
