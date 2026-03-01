// 저장된 설정 로드
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get(
    { apiEndpoint: "http://localhost:8000/api/upload-policy", apiKey: "", insurer: "" },
    (items) => {
      document.getElementById("apiEndpoint").value = items.apiEndpoint;
      document.getElementById("apiKey").value = items.apiKey;
      document.getElementById("insurer").value = items.insurer;
    }
  );

  document.getElementById("btnSave").addEventListener("click", () => {
    const apiEndpoint = document.getElementById("apiEndpoint").value.trim();
    const apiKey = document.getElementById("apiKey").value.trim();
    const insurer = document.getElementById("insurer").value.trim();

    if (!apiEndpoint) {
      document.getElementById("status").style.color = "#e74c3c";
      document.getElementById("status").textContent = "⚠️ API 서버 주소를 입력해주세요.";
      return;
    }

    chrome.storage.sync.set({ apiEndpoint, apiKey, insurer }, () => {
      const statusEl = document.getElementById("status");
      statusEl.style.color = "#27ae60";
      statusEl.textContent = "✅ 저장 완료!";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
    });
  });
});
