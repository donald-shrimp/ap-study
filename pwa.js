const appURL = new URL('./', import.meta.url);
const cachePrefix = `hitomon-${appURL.pathname}`;

// Read only this app's public asset caches. Learning records remain in IndexedDB.
export async function savedAssetURLs() {
  if (!('caches' in window)) return new Set();
  try {
    const names = (await caches.keys()).filter(name => name.startsWith(cachePrefix));
    const requests = await Promise.all(names.map(async name => (await caches.open(name)).keys()));
    return new Set(requests.flat().map(request => {
      const url = new URL(request.url); url.search = ''; return url.href;
    }));
  } catch { return new Set(); }
}

export function initPWA({beforeUpdate=async()=>true}={}) {
  const installButton = document.querySelector('#install-app');
  const installHelp = document.querySelector('#install-help');
  const updateButton = document.querySelector('#update-app');
  const status = document.querySelector('#pwa-status');
  let installPrompt = null, registration = null, reloadForUpdate = false;
  let promptReceived = false, workerError = null;
  const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1;
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone;
  function showInstallState() {
    installButton.hidden = standalone() || !installPrompt;
    installHelp.textContent = standalone() ? 'ホーム画面から起動しています。'
      : installPrompt ? 'ホーム画面やアプリ一覧から起動できます。'
      : iOS
        ? 'Safariの共有メニューから「ホーム画面に追加」を選びます。'
        : 'ブラウザのメニューから「アプリをインストール」または「ホーム画面に追加」を選びます。';
  }
  showInstallState();
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault(); promptReceived = true; installPrompt = event; showInstallState();
  });
  window.addEventListener('appinstalled', () => {
    installPrompt = null; installButton.hidden = true; installHelp.textContent = 'ホーム画面に追加しました。';
  });
  installButton.addEventListener('click', async () => {
    if (!installPrompt) return;
    const prompt = installPrompt; installPrompt = null;
    await prompt.prompt(); await prompt.userChoice; showInstallState();
  });
  // Only the explicit troubleshooting URL exposes diagnostics; normal study stays unchanged.
  if (new URL(location.href).searchParams.get('pwa-check') === '1') {
    import('./pwa-diagnostics.js').then(({showPWADiagnostics}) => showPWADiagnostics(() => ({
      promptReceived, promptAvailable: !!installPrompt, workerError
    }))).catch(() => { status.textContent = '診断画面を読み込めませんでした。接続後に開き直してください。'; });
  }
  if (!('serviceWorker' in navigator) || !isSecureContext) {
    status.textContent = 'このブラウザではオフライン保存を利用できません。'; return;
  }
  updateButton.addEventListener('click', async () => {
    if (!registration?.waiting) return;
    updateButton.disabled = true;
    if(!await beforeUpdate()){updateButton.disabled=false;status.textContent='記録を保存できていません。先に書き出して保管してください。';return;}
    reloadForUpdate = true;
    registration.waiting.postMessage({type: 'ACTIVATE_UPDATE'});
  });
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloadForUpdate) location.reload();
  });
  navigator.serviceWorker.register(new URL('sw.js', appURL), {scope: appURL.pathname, updateViaCache: 'none'})
    .then(reg => {
      registration = reg;
      const showUpdate = () => { updateButton.hidden = !reg.waiting; };
      showUpdate();
      reg.addEventListener('updatefound', () => {
        reg.installing?.addEventListener('statechange', showUpdate);
      });
    }).catch(error => {
      workerError = String(error);
      if (!navigator.serviceWorker.controller) status.textContent = 'オフライン用の保存ができませんでした。接続後に開き直してください。';
    });
}
