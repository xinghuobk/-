/**
 * ParaJudge 桌面端桥接层
 *
 * 自动检测运行环境：
 *   - 桌面端（PyWebView）：window.pywebview.api 可用 → 走原生 API
 *   - 浏览器：                无原生 API → 降级为 Web 下载
 *
 * 使用方式：
 *   const result = await desktop.saveFileDialog({...});
 *   if (result.ok) console.log('保存到', result.path);
 */
(function (global) {
    'use strict';

    // ============================================================
    // 环境检测
    // ============================================================

    const isDesktop = !!(global.pywebview && global.pywebview.api);

    const Desktop = {
        isDesktop,
        api: isDesktop ? global.pywebview.api : null,

        /**
         * 安全调用原生 API（带超时与降级）
         */
        async _call(method, ...args) {
            if (!isDesktop) {
                return { ok: false, reason: 'not_desktop', fallback: true };
            }
            try {
                const fn = this.api[method];
                if (typeof fn !== 'function') {
                    return { ok: false, reason: 'method_not_found', method };
                }
                const result = await fn(...args);
                return { ok: true, data: result };
            } catch (e) {
                console.error(`[DesktopBridge] ${method} 调用失败`, e);
                return { ok: false, reason: 'exception', error: e.message };
            }
        },

        // ============================================================
        // 文件操作
        // ============================================================

        /**
         * 选择本地文件
         * @param {object} opts
         * @param {string} [opts.title] 对话框标题
         * @param {string} [opts.fileTypes] "PDF (*.pdf)|*.pdf|所有文件 (*.*)|*.*"
         */
        async openFile(opts = {}) {
            const title = opts.title || '选择文件';
            const fileTypes = opts.fileTypes || '所有文件 (*.*)|*.*';
            return this._call('open_file_dialog', title, fileTypes);
        },

        /**
         * 弹出保存对话框
         * @param {object} opts
         * @param {string} opts.defaultFilename
         * @param {string} [opts.title]
         * @param {string} [opts.fileTypes]
         */
        async saveFile(opts = {}) {
            const title = opts.title || '保存文件';
            const defaultFilename = opts.defaultFilename || '';
            const fileTypes = opts.fileTypes || '所有文件 (*.*)|*.*';
            return this._call('save_file_dialog', title, defaultFilename, fileTypes);
        },

        /**
         * 用系统默认应用打开文件
         */
        async openPath(path) {
            return this._call('open_path', path);
        },

        /**
         * 在文件管理器中显示
         */
        async showInFolder(path) {
            return this._call('show_in_folder', path);
        },

        // ============================================================
        // 导出
        // ============================================================

        /**
         * 导出 JSON 裁决
         * @param {object} payload 完整 FullPipelineOutput
         * @returns {Promise<{ok, path?}>}
         */
        async exportVerdictJSON(payload) {
            if (!isDesktop) {
                return this._fallbackDownloadJSON(payload);
            }
            const r = await this._call('export_verdict_json', JSON.stringify(payload));
            return r.ok ? { ok: true, path: r.data, native: true } : { ok: false, ...r };
        },

        /**
         * 导出 Markdown 裁决
         */
        async exportVerdictMarkdown(markdown, problem) {
            if (!isDesktop) {
                return this._fallbackDownloadText(markdown, `${problem || 'verdict'}.md`, 'text/markdown');
            }
            const r = await this._call('export_verdict_markdown', markdown, problem || 'verdict');
            return r.ok ? { ok: true, path: r.data, native: true } : { ok: false, ...r };
        },

        // ============================================================
        // 元信息
        // ============================================================

        async getAppInfo() {
            return this._call('get_app_info');
        },

        async getDataDir() {
            return this._call('get_data_dir');
        },

        // ============================================================
        // 应用控制
        // ============================================================

        async quit() {
            return this._call('quit_app');
        },

        // ============================================================
        // 降级方案（浏览器环境）
        // ============================================================

        _fallbackDownloadJSON(payload) {
            try {
                const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
                this._triggerDownload(blob, `parajudge-${new Date().toISOString().slice(0, 10)}.json`);
                return { ok: true, fallback: true };
            } catch (e) {
                return { ok: false, reason: e.message };
            }
        },

        _fallbackDownloadText(text, filename, mime) {
            try {
                const blob = new Blob([text], { type: mime });
                this._triggerDownload(blob, filename);
                return { ok: true, fallback: true };
            } catch (e) {
                return { ok: false, reason: e.message };
            }
        },

        _triggerDownload(blob, filename) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        },
    };

    // 暴露到 window
    global.Desktop = Desktop;

    // 桌面环境下，DOM ready 后在 body 加个标记，方便 CSS 适配
    if (isDesktop) {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.classList.add('desktop-mode');
            console.log('[ParaJudge] Running in DESKTOP mode (PyWebView)');
        });
    } else {
        console.log('[ParaJudge] Running in BROWSER mode (will use fallback)');
    }
})(window);
