// Opt-in, read-only checks for a device we cannot inspect through DevTools.
// These checks do not expose Chrome's native installability error or study records.
export async function showPWADiagnostics(snapshot) {
  const dialog = document.querySelector('#settings-dialog');
  const panel = document.createElement('section');
  panel.id = 'pwa-diagnostics';
  panel.innerHTML = `<h3>インストールの確認</h3>
    <p class="small muted">端末での読み込み状況を確認します。学習記録は含めません。</p>
    <p id="diagnostic-status" class="small" role="status">確認中…</p>
    <button type="button" class="button secondary" id="copy-pwa-diagnostics" disabled>確認結果をコピー</button>
    <details><summary>確認結果</summary><textarea id="pwa-diagnostic-report" readonly aria-label="インストール確認結果" rows="12" style="width:100%;box-sizing:border-box"></textarea></details>`;
  dialog.querySelector('form').after(panel);
  if (!dialog.open) dialog.showModal();
  const status = panel.querySelector('#diagnostic-status');
  const output = panel.querySelector('textarea');
  const report = {
    diagnosticVersion: 1, checkedAt: new Date().toISOString(),
    page: location.origin + location.pathname, userAgent: navigator.userAgent,
    secureContext: isSecureContext, online: navigator.onLine,
    standalone: matchMedia('(display-mode: standalone)').matches,
    manifestLink: document.querySelector('link[rel="manifest"]')?.href || null,
    checksComplete: false, manifest: null, icons: []
  };
  async function update() {
    let worker = null;
    try {
      const reg = await navigator.serviceWorker?.getRegistration(location.href);
      const describe = worker => worker ? {scriptURL: worker.scriptURL, state: worker.state} : null;
      worker = reg ? {scope: reg.scope, active: describe(reg.active), installing: describe(reg.installing), waiting: describe(reg.waiting)} : null;
    } catch (error) { worker = {error: String(error)}; }
    report.browser = snapshot();
    report.worker = worker;
    report.controller = navigator.serviceWorker?.controller?.scriptURL || null;
    output.value = JSON.stringify(report, null, 2);
  }
  panel.querySelector('button').addEventListener('click', async () => {
    await update();
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = 'コピーしました。この会話に貼り付けてください。';
    } catch {
      panel.querySelector('details').open = true;
      output.focus(); output.select();
      status.textContent = '確認結果を選択しました。コピーして、この会話に貼り付けてください。';
    }
  });
  async function download(url) {
    const start = performance.now();
    const response = await fetch(url, {cache: 'no-store', signal: AbortSignal.timeout(8000)});
    const blob = await response.blob();
    const result = {url: response.url, status: response.status, type: response.headers.get('content-type'),
      offlineCache: response.headers.get('X-Hitomon-Offline') === '1', bytes: blob.size,
      elapsedMs: Math.round(performance.now() - start)};
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
    return {blob, result};
  }
  await update();
  try {
    if (!report.manifestLink) throw new Error('マニフェストのリンクがありません');
    const {blob, result} = await download(report.manifestLink);
    report.manifest = result;
    const manifest = JSON.parse(await blob.text());
    const start = new URL(manifest.start_url || location.href, report.manifestLink);
    result.definition = manifest;
    result.resolved = {
      // Manifest id is relative to the start URL origin, not the manifest path.
      id: new URL(manifest.id || start.href, start.origin + '/').href,
      startURL: start.href, scope: new URL(manifest.scope || './', start).href
    };
    report.icons = await Promise.all((manifest.icons || []).map(async icon => {
      const url = new URL(icon.src, report.manifestLink).href;
      let objectURL;
      try {
        const {blob, result} = await download(url);
        objectURL = URL.createObjectURL(blob);
        const image = new Image(); image.src = objectURL; await image.decode();
        return {...result, declaredSizes: icon.sizes, purpose: icon.purpose || 'any',
          decodedSize: `${image.naturalWidth}x${image.naturalHeight}`};
      } catch (error) { return {url, error: String(error)}; }
      finally { if (objectURL) URL.revokeObjectURL(objectURL); }
    }));
  } catch (error) { report.error = String(error); }
  report.checksComplete = true;
  panel.querySelector('button').disabled = false;
  status.textContent = '読み込みの確認が終わりました。「確認結果をコピー」を押して、この会話に貼り付けてください。';
  await update();
  // Chrome's prompt and SW activation can finish after the asset probes.
  const refresh = () => { if (dialog.isConnected) void update(); };
  window.addEventListener('beforeinstallprompt', refresh);
  navigator.serviceWorker?.addEventListener('controllerchange', refresh);
  dialog.addEventListener('close', () => {
    window.removeEventListener('beforeinstallprompt', refresh);
    navigator.serviceWorker?.removeEventListener('controllerchange', refresh);
  }, {once: true});
}
