/**
 * ParaJudge 前端 API 封装
 * 统一调用后端 FastAPI 接口，支持同步 / 异步 / SSE 三种模式
 *
 * 使用方式：
 *   const api = new ParaJudgeAPI('http://localhost:8000');
 *   const result = await api.runSync({ problem: '...' });
 *   await api.runStream({ problem: '...' }, { onArgument: (a) => {...} });
 */

const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 60_000;

class ParaJudgeAPIError extends Error {
    constructor(message, code, httpStatus, details) {
        super(message);
        this.name = 'ParaJudgeAPIError';
        this.code = code;
        this.httpStatus = httpStatus;
        this.details = details;
    }
}

class ParaJudgeAPI {
    /**
     * @param {string} baseURL 后端 API 根地址
     */
    constructor(baseURL = DEFAULT_BASE_URL) {
        this.baseURL = baseURL.replace(/\/+$/, '');
    }

    // ============================================================
    // 通用请求
    // ============================================================

    async _request(path, options = {}) {
        const url = `${this.baseURL}${path}`;
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(options.headers || {}),
        };
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), options.timeout || DEFAULT_TIMEOUT_MS);

        try {
            const res = await fetch(url, { ...options, headers, signal: controller.signal });
            const text = await res.text();
            let data = null;
            if (text) {
                try { data = JSON.parse(text); } catch { data = text; }
            }
            if (!res.ok) {
                const err = (data && data.error) || {};
                throw new ParaJudgeAPIError(
                    err.message || `HTTP ${res.status}`,
                    err.code || 'HTTP_ERROR',
                    res.status,
                    data
                );
            }
            return data;
        } finally {
            clearTimeout(timer);
        }
    }

    // ============================================================
    // 健康检查 / 版本
    // ============================================================

    async health() {
        return this._request('/api/health', { method: 'GET' });
    }

    async version() {
        return this._request('/api/version', { method: 'GET' });
    }

    async listJudges() {
        return this._request('/api/judges', { method: 'GET' });
    }

    async listProviders() {
        return this._request('/api/llm/providers', { method: 'GET' });
    }

    async listExamples(category) {
        const q = category ? `?category=${encodeURIComponent(category)}` : '';
        return this._request(`/api/examples/questions${q}`, { method: 'GET' });
    }

    // ============================================================
    // 同步执行（短任务）
    // ============================================================

    /**
     * 同步执行完整 ParaJudge 流程
     * @param {object} payload
     * @param {string} payload.problem
     * @param {string} [payload.pro_stance]
     * @param {string} [payload.con_stance]
     * @param {number} [payload.rounds=3]
     * @param {number} [payload.max_evidence=20]
     * @param {boolean} [payload.enable_llm_review=true]
     * @param {object} [payload.llm] { provider, model, api_key, temperature, max_tokens }
     * @param {object} [payload.moderator]
     */
    async runSync(payload) {
        return this._request('/api/parajudge/run', {
            method: 'POST',
            body: JSON.stringify(payload),
            timeout: 90_000,
        });
    }

    // ============================================================
    // 异步任务 + SSE 流
    // ============================================================

    async createJob(payload) {
        return this._request('/api/parajudge/jobs', {
            method: 'POST',
            body: JSON.stringify({ ...payload, stream: true }),
            timeout: 5_000,
        });
    }

    async getJobStatus(jobId) {
        return this._request(`/api/parajudge/jobs/${jobId}`, { method: 'GET' });
    }

    async getJobResult(jobId) {
        return this._request(`/api/parajudge/jobs/${jobId}/result`, { method: 'GET', timeout: 30_000 });
    }

    /**
     * 通过 SSE 订阅 job 进度
     * @param {string} jobId
     * @param {object} handlers
     *   onStarted, onPhaseStart, onPhaseProgress, onArgument,
     *   onReviewIssue, onJudgeScored, onPhaseFinished,
     *   onCompleted, onFailed, onError
     * @returns {{ close: function }}
     */
    subscribeJob(jobId, handlers = {}) {
        const url = `${this.baseURL}/api/parajudge/jobs/${jobId}/stream`;
        const es = new EventSource(url);

        const bind = (eventName, handler) => {
            if (!handler) return;
            es.addEventListener(eventName, (e) => {
                try { handler(JSON.parse(e.data)); }
                catch (err) { console.warn(`[SSE] ${eventName} parse error`, err); }
            });
        };

        bind('job.started', handlers.onStarted);
        bind('job.snapshot', handlers.onSnapshot);
        bind('phase.started', handlers.onPhaseStart);
        bind('phase.progress', handlers.onPhaseProgress);
        bind('argument.added', handlers.onArgument);
        bind('review.issue', handlers.onReviewIssue);
        bind('judge.scored', handlers.onJudgeScored);
        bind('phase.finished', handlers.onPhaseFinished);
        bind('job.completed', handlers.onCompleted);
        bind('job.failed', handlers.onFailed);
        bind('job.cancelled', handlers.onCancelled);

        es.onerror = (e) => {
            if (handlers.onError) handlers.onError(e);
        };

        return {
            close: () => es.close(),
        };
    }

    /**
     * 一站式：异步执行并流式接收进度
     */
    async runStream(payload, handlers = {}) {
        const { job_id, stream_url } = await this.createJob(payload);
        if (handlers.onJobCreated) handlers.onJobCreated(job_id);

        return new Promise((resolve, reject) => {
            const sub = this.subscribeJob(job_id, {
                onArgument: handlers.onArgument,
                onReviewIssue: handlers.onReviewIssue,
                onJudgeScored: handlers.onJudgeScored,
                onPhaseStart: handlers.onPhaseStart,
                onPhaseFinished: handlers.onPhaseFinished,
                onCompleted: async (data) => {
                    sub.close();
                    if (handlers.onCompleted) handlers.onCompleted(data);
                    try {
                        const result = await this.getJobResult(job_id);
                        resolve(result);
                    } catch (e) { reject(e); }
                },
                onFailed: (data) => {
                    sub.close();
                    if (handlers.onFailed) handlers.onFailed(data);
                    reject(new ParaJudgeAPIError(data.message || 'job failed', data.code || 'JOB_FAILED'));
                },
                onError: (e) => {
                    sub.close();
                    if (handlers.onError) handlers.onError(e);
                },
            });
        });
    }

    // ============================================================
    // 单阶段执行（调试用）
    // ============================================================

    async runPhase0(payload) {
        return this._request('/api/parajudge/run/phase/0', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async runPhase1(payload) {
        return this._request('/api/parajudge/run/phase/1', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async runPhase21(payload) {
        return this._request('/api/parajudge/run/phase/2.1', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async runPhase22(payload) {
        return this._request('/api/parajudge/run/phase/2.2', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }
}

// 暴露为全局对象（支持 <script> 直接引入）
if (typeof window !== 'undefined') {
    window.ParaJudgeAPI = ParaJudgeAPI;
    window.ParaJudgeAPIError = ParaJudgeAPIError;
}

// CommonJS / ESM 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ParaJudgeAPI, ParaJudgeAPIError };
}
export { ParaJudgeAPI, ParaJudgeAPIError };
