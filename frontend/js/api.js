/*
 * FLUXO DE CAIXA
 * Comunicação com a API FastAPI.
 */

// URL padrão da API em produção no Render
const RENDER_API_URL = "https://fluxo-caixa-cuq1.onrender.com";

function obterUrlBaseApi() {
    if (window.__API_URL__) {
        return window.__API_URL__.replace(/\/+$/, "");
    }
    const urlPersistida = localStorage.getItem("fluxo_caixa_api_url");
    if (urlPersistida) {
        return urlPersistida.trim().replace(/\/+$/, "");
    }
    // Quando executado em HTTPS (Vercel / Produção), conecta ao backend no Render
    if (window.location.protocol === "https:") {
        return RENDER_API_URL;
    }
    // Ambiente de desenvolvimento local em HTTP
    return "http://127.0.0.1:8000";
}

const API_BASE_URL = obterUrlBaseApi();

const api = {
    getToken() {
        return sessionStorage.getItem("fluxo_caixa_token");
    },

    setToken(token) {
        sessionStorage.setItem("fluxo_caixa_token", token);
    },

    clearToken() {
        sessionStorage.removeItem("fluxo_caixa_token");
    },

    async request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        const body = options.body;

        if (
            body !== undefined &&
            body !== null &&
            !(body instanceof FormData) &&
            !(body instanceof URLSearchParams) &&
            !headers.has("Content-Type")
        ) {
            headers.set("Content-Type", "application/json");
        }

        const token = this.getToken();
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }

        let response;
        try {
            response = await fetch(`${API_BASE_URL}${path}`, {
                ...options,
                headers
            });
        } catch (erro) {
            console.error("Erro na comunicação com a API:", erro);
            if (window.location.protocol === "https:" && API_BASE_URL.startsWith("http://")) {
                throw new Error(
                    "Bloqueio de conteúdo misto (HTTPS para HTTP). Para conectar à API a partir da Vercel, configure a URL segura da API: localStorage.setItem('fluxo_caixa_api_url', 'https://sua-api.com')"
                );
            }
            throw new Error(
                "Não foi possível conectar à API. Verifique se o servidor está ativo."
            );
        }

        if (response.status === 401 && token) {
            this.clearToken();
            throw new Error(
                "Sessão expirada ou não autorizada. Faça login novamente."
            );
        }

        if (response.status === 401) {
            let message = "E-mail ou senha inválidos.";
            try {
                const data = await response.json();
                if (typeof data.detail === "string") {
                    message = data.detail;
                }
            } catch {
                // Mantém a mensagem de autenticação padrão.
            }
            throw new Error(message);
        }

        if (!response.ok) {
            let message = `Erro HTTP ${response.status}.`;
            try {
                const data = await response.json();
                if (typeof data.detail === "string") {
                    message = data.detail;
                } else if (Array.isArray(data.detail)) {
                    message = data.detail
                        .map((error) => error.msg)
                        .filter(Boolean)
                        .join(" ");
                }
            } catch {
                // Mantém a mensagem HTTP quando a resposta não contém JSON.
            }
            throw new Error(message);
        }

        if (response.status === 204) {
            return null;
        }

        try {
            return await response.json();
        } catch (erro) {
            console.error("Erro na comunicação com a API:", erro);
            if (window.location.protocol === "https:" && API_BASE_URL.startsWith("http://")) {
                throw new Error(
                    "Bloqueio de conteúdo misto (HTTPS para HTTP). Para conectar à API a partir da Vercel, configure a URL segura da API: localStorage.setItem('fluxo_caixa_api_url', 'https://sua-api.com')"
                );
            }
            throw new Error("A API retornou uma resposta inválida.");
        }
    },

    get(path) {
        return this.request(path);
    },

    post(path, data) {
        return this.request(path, {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    postForm(path, data) {
        return this.request(path, {
            method: "POST",
            body: new URLSearchParams(data)
        });
    },

    put(path, data) {
        return this.request(path, {
            method: "PUT",
            body: JSON.stringify(data)
        });
    },

    delete(path) {
        return this.request(path, {
            method: "DELETE"
        });
    }
};
