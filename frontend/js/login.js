/*
 * FLUXO DE CAIXA
 * Login e tratamento de erros de autenticação.
 *
 * O formulário deverá ter:
 * form#login-form
 * input#email
 * input#senha
 * elemento#login-message
 */

document.addEventListener("DOMContentLoaded", () => {
    const message = document.querySelector("#login-message");
    if (
        message &&
        new URLSearchParams(window.location.search).get("cadastro") ===
            "sucesso"
    ) {
        message.textContent = "Cadastro criado. Entre com seu e-mail e senha.";
        message.className = "form-message info";
    }

    const form = document.querySelector("#login-form");
    if (!form) return;

    if (api.getToken()) {
        window.location.replace("index.html");
        return;
    }

    const emailInput = document.querySelector("#email");
    const senhaInput = document.querySelector("#senha");
    const submitButton = form.querySelector('[type="submit"]');

    if (!emailInput || !senhaInput || !message) {
        console.error(
            "O formulário de login precisa dos campos #email, #senha e #login-message."
        );
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = emailInput.value.trim();
        const senha = senhaInput.value;

        message.textContent = "";
        message.className = "form-message";

        if (!email || !senha) {
            message.textContent = "Preencha o e-mail e a senha.";
            message.classList.add("error");
            return;
        }

        if (!emailInput.checkValidity()) {
            message.textContent = "Informe um endereço de e-mail válido.";
            message.classList.add("error");
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
        }

        message.textContent = "Entrando...";
        message.classList.add("info");

        try {
            api.clearToken();
            const data = await api.postForm("/login", {
                username: email,
                password: senha
            });

            if (
                !data ||
                typeof data.access_token !== "string" ||
                !data.access_token
            ) {
                throw new Error("A API não retornou um token de acesso válido.");
            }

            api.setToken(data.access_token);
            window.location.assign("index.html");
        } catch (error) {
            message.textContent = error.message;
            message.className = "form-message error";
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
            }
        }
    });
});
