import { TELEMETRY_CONFIG } from './config';

function isLocalAccess() {
  const host = window.location.hostname;
  return (
    import.meta.env.DEV ||
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '::1'
  );
}

async function notifyBackendWithRetry(notifyUrl, maxAttempts, delayMs) {
  if (!notifyUrl) return;

  const payload = {
    source: 'Auto Data Analyst',
    path: window.location.pathname,
    referrer: document.referrer,
    language: navigator.language,
    screen: `${window.screen.width}x${window.screen.height}`,
  };

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const res = await fetch(notifyUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const json = await res.json();
      if (json.success) {
        console.log(`[telemetry] backend notified on attempt ${attempt}`);
        return;
      }

      console.warn(`[telemetry] backend response unsuccessful on attempt ${attempt}`, json);
    } catch (error) {
      console.warn(`[telemetry] notify attempt ${attempt} failed`, error);
    }

    if (attempt < maxAttempts) {
      await delay(delayMs);
    }
  }

  console.error('[telemetry] all backend notify attempts failed');
}

export function initTelemetry() {
  if (!TELEMETRY_CONFIG.enabled || isLocalAccess()) {
    console.log('[telemetry] skipped (local access or disabled)');
    return;
  }

  notifyBackendWithRetry(
    TELEMETRY_CONFIG.notifyBackendUrl,
    TELEMETRY_CONFIG.maxNotifyAttempts,
    TELEMETRY_CONFIG.notifyRetryDelayMs,
  );
}
