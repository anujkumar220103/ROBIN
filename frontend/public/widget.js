// Loads the ROBIN chatbot widget into an external website using an isolated iframe.

(function () {
  var script = document.currentScript;
  if (!script) return;

  var publicId = script.getAttribute("data-robin-chatbot");
  var widgetBase = script.getAttribute("data-robin-widget-base") || "http://localhost:5173/widget";
  if (!publicId) return;

  var launcher = document.createElement("button");
  launcher.textContent = "Chat";
  launcher.setAttribute("aria-label", "Open chatbot");
  launcher.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483000;border:0;border-radius:999px;background:#2563EB;color:white;padding:14px 18px;box-shadow:0 8px 24px rgba(15,23,42,.25);cursor:pointer;font:600 14px Arial";
  document.body.appendChild(launcher);

  var iframe = document.createElement("iframe");
  var widgetUrl = widgetBase.replace(/\/+$/, "") + "/" + encodeURIComponent(publicId) + "?origin=" + encodeURIComponent(window.location.origin);
  iframe.src = widgetUrl;
  iframe.title = "ROBIN chatbot";
  iframe.setAttribute("allow", "clipboard-write");
  iframe.style.cssText = "position:fixed;right:20px;bottom:78px;width:380px;height:560px;max-width:calc(100vw - 32px);max-height:calc(100vh - 110px);border:0;border-radius:16px;box-shadow:0 16px 48px rgba(15,23,42,.25);z-index:2147483000;display:none;background:white";
  document.body.appendChild(iframe);

  launcher.addEventListener("click", function () {
    var open = iframe.style.display === "block";
    iframe.style.display = open ? "none" : "block";
    launcher.textContent = open ? "Chat" : "Close";
  });
})();
