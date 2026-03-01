/**
 * 골드키 약관 RAG 전송기 — Service Worker (Manifest V3)
 *
 * 동작 흐름:
 * 1. 관리자가 PDF 링크를 우클릭 → "RAG 버킷으로 전송" 메뉴 클릭
 * 2. 현재 탭의 브라우저 세션(쿠키 포함)으로 PDF를 Fetch (Blob)
 * 3. 로컬 FastAPI 서버(또는 배포 서버)로 multipart/form-data POST 전송
 * 4. 성공/실패 알림 표시
 *
 * 설정:
 * - API_ENDPOINT : FastAPI 서버 주소 (chrome.storage.sync에 저장, 기본값 아래)
 * - API_KEY      : X-API-Key 헤더 값
 */

// ── 기본 설정값 ──────────────────────────────────────────────────────────────
const DEFAULT_API_ENDPOINT = "http://localhost:8000/api/upload-policy";
const DEFAULT_API_KEY = "";  // 설치 후 팝업 또는 chrome.storage.sync으로 설정

// ── 컨텍스트 메뉴 등록 (Service Worker 시작 시 1회) ──────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "rag-upload",
    title: "📤 RAG 버킷으로 전송 (골드키)",
    contexts: ["link"],
    // PDF 링크에만 표시 — targetUrlPatterns으로 필터
    targetUrlPatterns: ["*://*/*.pdf", "*://*/*.PDF"],
  });

  // 일반 링크에도 항상 보이도록 추가 (PDF가 리다이렉트되는 경우 대비)
  chrome.contextMenus.create({
    id: "rag-upload-any",
    title: "📤 RAG 버킷으로 전송 (모든 링크)",
    contexts: ["link"],
  });

  console.log("[골드키 RAG] 컨텍스트 메뉴 등록 완료");
});

// ── 컨텍스트 메뉴 클릭 핸들러 ────────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "rag-upload" && info.menuItemId !== "rag-upload-any") return;

  const pdfUrl = info.linkUrl;
  if (!pdfUrl) {
    showNotification("오류", "URL을 가져올 수 없습니다.");
    return;
  }

  console.log(`[골드키 RAG] 전송 시작: ${pdfUrl}`);
  showNotification("다운로드 중...", `${getFilename(pdfUrl)} 파일을 가져오는 중입니다.`);

  try {
    // ── STEP 1: 현재 탭의 세션(쿠키)으로 PDF Fetch ─────────────────────────
    // chrome.scripting.executeScript를 통해 컨텐츠 스크립트에서 fetch 실행
    // → 브라우저가 이미 로그인된 세션으로 요청하므로 보험사 인증 통과
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: fetchPdfAsBase64,
      args: [pdfUrl],
    });

    if (!result || result.error) {
      throw new Error(result?.error || "PDF 다운로드 실패");
    }

    const { base64Data, filename, mimeType } = result.result;

    // ── STEP 2: Base64 → Blob 변환 후 FastAPI 서버로 전송 ──────────────────
    const settings = await getSettings();
    await uploadToServer(base64Data, filename, mimeType, pdfUrl, settings);

    showNotification(
      "✅ 전송 완료",
      `${filename} 이(가) RAG 버킷으로 전송되었습니다.`
    );
    console.log(`[골드키 RAG] 전송 완료: ${filename}`);

  } catch (err) {
    console.error("[골드키 RAG] 전송 실패:", err);
    showNotification("❌ 전송 실패", `오류: ${err.message}`);
  }
});

// ── 컨텐츠 스크립트 컨텍스트에서 실행되는 PDF Fetch 함수 ─────────────────────
// (chrome.scripting.executeScript의 func 인자로 주입됨)
function fetchPdfAsBase64(url) {
  return fetch(url, {
    method: "GET",
    credentials: "include",  // 현재 탭의 쿠키·세션 사용
  })
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      return res.blob();
    })
    .then((blob) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result.split(",")[1];
          const contentType = blob.type || "application/pdf";
          // 파일명 추출: URL 마지막 세그먼트 사용
          const parts = url.split("/");
          const raw = parts[parts.length - 1].split("?")[0];
          const filename = decodeURIComponent(raw) || "policy.pdf";
          resolve({ base64Data: base64, filename, mimeType: contentType });
        };
        reader.onerror = () => reject(new Error("FileReader 오류"));
        reader.readAsDataURL(blob);
      });
    })
    .catch((err) => ({ error: err.message }));
}

// ── FastAPI 서버로 multipart/form-data 업로드 ─────────────────────────────────
async function uploadToServer(base64Data, filename, mimeType, sourceUrl, settings) {
  const { apiEndpoint, apiKey, insurer } = settings;

  // Base64 → Uint8Array → Blob
  const binary = atob(base64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([bytes], { type: mimeType || "application/pdf" });

  const formData = new FormData();
  formData.append("file", blob, filename);
  formData.append("source_url", sourceUrl);
  formData.append("insurer", insurer || "");
  formData.append("doc_type", "보험약관");

  const headers = {};
  if (apiKey) headers["X-API-Key"] = apiKey;

  const res = await fetch(apiEndpoint, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`서버 응답 오류 ${res.status}: ${errText.slice(0, 200)}`);
  }

  return res.json();
}

// ── 크롬 알림 표시 헬퍼 ──────────────────────────────────────────────────────
function showNotification(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon48.png",
    title: `골드키 RAG | ${title}`,
    message: message.slice(0, 200),
  });
}

// ── 설정 로드 (chrome.storage.sync) ──────────────────────────────────────────
async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      {
        apiEndpoint: DEFAULT_API_ENDPOINT,
        apiKey: DEFAULT_API_KEY,
        insurer: "",
      },
      (items) => resolve(items)
    );
  });
}

// ── URL에서 파일명 추출 헬퍼 ─────────────────────────────────────────────────
function getFilename(url) {
  try {
    const parts = new URL(url).pathname.split("/");
    return decodeURIComponent(parts[parts.length - 1]) || "policy.pdf";
  } catch {
    return "policy.pdf";
  }
}
