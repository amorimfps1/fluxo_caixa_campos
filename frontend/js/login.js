/*
 * FLUXO DE CAIXA
 * Login, alternância de visibilidade de senha (olhinho) e recuperação de senha via OTP/CPF.
 */

function inicializarBotoesVerSenha(root = document) {
    const botoes = root.querySelectorAll("[data-toggle-password]");
    botoes.forEach((botao) => {
        botao.addEventListener("click", () => {
            const targetId = botao.getAttribute("data-toggle-password");
            const input = document.getElementById(targetId);
            if (!input) return;

            const mostrar = input.type === "password";
            input.type = mostrar ? "text" : "password";
            botao.classList.toggle("is-visible", mostrar);
            botao.setAttribute("aria-pressed", String(mostrar));
            botao.setAttribute(
                "aria-label",
                mostrar ? "Ocultar senha" : "Mostrar senha"
            );
        });
    });
}

function aplicarMascaraCpf(input) {
    if (!input) return;
    input.addEventListener("input", () => {
        const digitos = input.value.replace(/\D/g, "").slice(0, 11);
        let formatado = digitos;
        if (digitos.length > 9) {
            formatado = `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9, 11)}`;
        } else if (digitos.length > 6) {
            formatado = `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
        } else if (digitos.length > 3) {
            formatado = `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
        }
        input.value = formatado;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    inicializarBotoesVerSenha();

    const message = document.querySelector("#login-message");
    if (
        message &&
        new URLSearchParams(window.location.search).get("cadastro") ===
            "sucesso"
    ) {
        message.textContent =
            "Cadastro criado! Enviamos um e-mail de confirmação. Entre com seu e-mail e senha.";
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

    // =========================================================
    // MODAL: ESQUECEU A SENHA? (OTP POR E-MAIL OU CPF)
    // =========================================================
    const forgotTrigger = document.querySelector("#forgot-password-trigger");
    const forgotDialog = document.querySelector("#forgot-password-dialog");
    const forgotForm = document.querySelector("#forgot-password-form");
    const forgotClose = document.querySelector("#forgot-password-close");
    const forgotCancel = document.querySelector("#forgot-password-cancel");
    const forgotSubmit = document.querySelector("#forgot-password-submit");
    const sendOtpButton = document.querySelector("#send-otp-button");

    const resetEmailInput = document.querySelector("#reset-email");
    const resetOtpInput = document.querySelector("#reset-otp");
    const resetCpfInput = document.querySelector("#reset-cpf");
    const resetPasswordInput = document.querySelector("#reset-password");
    const resetConfirmInput = document.querySelector("#reset-password-confirm");
    const resetMessage = document.querySelector("#reset-message");

    aplicarMascaraCpf(resetCpfInput);

    if (resetOtpInput) {
        resetOtpInput.addEventListener("input", () => {
            resetOtpInput.value = resetOtpInput.value.replace(/\D/g, "").slice(0, 6);
        });
    }

    function abrirModalRedefinicao() {
        if (!forgotDialog) return;
        if (forgotForm) forgotForm.reset();
        if (resetMessage) {
            resetMessage.textContent = "";
            resetMessage.className = "form-message";
        }
        if (resetEmailInput && emailInput.value.trim()) {
            resetEmailInput.value = emailInput.value.trim();
        }
        if (typeof forgotDialog.showModal === "function") {
            forgotDialog.showModal();
        } else {
            forgotDialog.setAttribute("open", "open");
        }
    }

    function fecharModalRedefinicao() {
        if (!forgotDialog) return;
        if (typeof forgotDialog.close === "function") {
            forgotDialog.close();
        } else {
            forgotDialog.removeAttribute("open");
        }
    }

    if (forgotTrigger) {
        forgotTrigger.addEventListener("click", abrirModalRedefinicao);
    }
    if (forgotClose) {
        forgotClose.addEventListener("click", fecharModalRedefinicao);
    }
    if (forgotCancel) {
        forgotCancel.addEventListener("click", fecharModalRedefinicao);
    }

    if (sendOtpButton && resetEmailInput && resetMessage) {
        sendOtpButton.addEventListener("click", async () => {
            const email = resetEmailInput.value.trim();
            resetMessage.textContent = "";
            resetMessage.className = "form-message";

            if (!email || !resetEmailInput.checkValidity()) {
                resetMessage.textContent = "Informe um e-mail válido para receber o código.";
                resetMessage.classList.add("error");
                resetEmailInput.focus();
                return;
            }

            sendOtpButton.disabled = true;
            resetMessage.textContent = "Enviando código de verificação para seu e-mail...";
            resetMessage.classList.add("info");

            try {
                const resposta = await api.post("/usuarios/esqueci-senha", { email });
                resetMessage.textContent =
                    resposta?.mensagem ||
                    "Código enviado! Verifique sua caixa de entrada e digite os 6 dígitos.";
                resetMessage.className = "form-message info";
                if (resetOtpInput) resetOtpInput.focus();
            } catch (error) {
                resetMessage.textContent = error.message;
                resetMessage.className = "form-message error";
            } finally {
                sendOtpButton.disabled = false;
            }
        });
    }

    if (
        forgotForm &&
        resetEmailInput &&
        resetPasswordInput &&
        resetConfirmInput &&
        resetMessage
    ) {
        forgotForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            resetMessage.textContent = "";
            resetMessage.className = "form-message";

            const email = resetEmailInput.value.trim();
            const codigoOtp = resetOtpInput ? resetOtpInput.value.trim() : "";
            const cpf = resetCpfInput ? resetCpfInput.value.trim() : "";
            const novaSenha = resetPasswordInput.value;
            const confirmarSenha = resetConfirmInput.value;

            if (!email || (!codigoOtp && !cpf) || !novaSenha || !confirmarSenha) {
                resetMessage.textContent =
                    "Informe o e-mail, o código OTP (ou CPF) e a nova senha.";
                resetMessage.classList.add("error");
                return;
            }

            if (novaSenha !== confirmarSenha) {
                resetMessage.textContent = "As senhas informadas não conferem.";
                resetMessage.classList.add("error");
                resetConfirmInput.focus();
                return;
            }

            if (forgotSubmit) forgotSubmit.disabled = true;
            resetMessage.textContent = "Validando código e redefinindo senha...";
            resetMessage.classList.add("info");

            try {
                const payload = {
                    email,
                    nova_senha: novaSenha
                };
                if (codigoOtp) {
                    payload.codigo_otp = codigoOtp;
                }
                if (cpf) {
                    payload.cpf = cpf;
                }

                await api.post("/usuarios/redefinir-senha", payload);

                fecharModalRedefinicao();
                emailInput.value = email;
                senhaInput.value = "";
                senhaInput.focus();
                message.textContent = "Senha redefinida com sucesso! Entre com sua nova senha.";
                message.className = "form-message info";
            } catch (error) {
                resetMessage.textContent = error.message;
                resetMessage.className = "form-message error";
            } finally {
                if (forgotSubmit) forgotSubmit.disabled = false;
            }
        });
    }
});
