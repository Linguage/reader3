document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const statusEl = document.getElementById("status");
  const splitSelect = document.getElementById("split-level");

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.style.color = isError ? "#fca5a5" : "#d1d5db";
  }

  async function uploadFile(file) {
    if (!file) return;
    setStatus("正在上传并解析 EPUB……");

    const formData = new FormData();
    formData.append("file", file);
    const splitLevel = splitSelect ? splitSelect.value : "2";
    formData.append("split_level", splitLevel);

    try {
      const res = await fetch("http://localhost:8123/api/upload_epub", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("上传失败，HTTP 状态码：" + res.status);
      }

      const data = await res.json();
      const title = data.title || "书籍";
      setStatus(`完成：${title} 已加入本地书库`);

      if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.create) {
        chrome.tabs.create({ url: "http://localhost:8123" });
      }
    } catch (err) {
      setStatus("错误：" + err.message, true);
    }
  }

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("hover");
  });

  dropZone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    dropZone.classList.remove("hover");
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("hover");
    const file = event.dataTransfer.files[0];
    if (file) {
      uploadFile(file);
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) {
      uploadFile(file);
    }
  });
});
