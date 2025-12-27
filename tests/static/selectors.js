window.actionLog = document.getElementById("action-log");
function log(type, id, value) {
  value = value || "";
  window.actionLog.textContent +=
    type + " " + id + (value ? " " + value : "") + "\n";
}
function setupEventListeners() {
  var allElements = document.querySelectorAll("button, input, h1, div[id]");
  var wrapperIds = ["nth-element-section"];
  for (var i = 0; i < allElements.length; i++) {
    var el = allElements[i];
    if (el.tagName === "INPUT") {
      el.addEventListener("input", function (e) {
        log("fill", this.id, e.target.value);
      });
    } else if (wrapperIds.indexOf(el.id) === -1) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        log("click", this.id);
      });
    }
  }
}
document.addEventListener("DOMContentLoaded", setupEventListeners);
