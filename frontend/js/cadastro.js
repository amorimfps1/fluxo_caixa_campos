/*
 * FLUXO DE CAIXA
 * Cadastro institucional com validação estrita de CPF em tempo real,
 * checklist visual interativo de senha forte, aceite obrigatório LGPD,
 * Google OAuth 2.0 e verificação de e-mail anti-bot via código OTP.
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

document.addEventListener("DOMContentLoaded", () => {
    inicializarBotoesVerSenha();

    if (api.getToken()) {
        window.location.replace("index.html");
        return;
    }

    if (typeof inicializarBotaoGoogleOAuth === "function") {
        inicializarBotaoGoogleOAuth({
            buttonSelector: "#google-oauth-btn",
            gsiContainerSelector: "#google-gsi-button",
            messageSelector: "#register-message"
        });
    }

    const form = document.querySelector("#register-form");
    if (!form) return;

    const nameInput = document.querySelector("#register-name");
    const cpfInput = document.querySelector("#register-cpf");
    const cpfFeedback = document.querySelector("#cpf-feedback");
    const emailInput = document.querySelector("#register-email");
    const phoneInput = document.querySelector("#register-phone");
    const passwordInput = document.querySelector("#register-password");
    const passwordChecklist = document.querySelector("#register-password-checklist");
    const confirmationInput = document.querySelector("#register-password-confirm");
    const confirmFeedback = document.querySelector("#password-confirm-feedback");
    const acceptTermsCheckbox = document.querySelector("#accept-terms");
    const acceptPrivacyCheckbox = document.querySelector("#accept-privacy");
    const message = document.querySelector("#register-message");
    const submitButton = form.querySelector('[type="submit"]');

    // Modal Anti-Bot de Verificação de E-mail
    const verifyDialog = document.querySelector("#verify-email-dialog");
    const verifyForm = document.querySelector("#verify-email-form");
    const verifyEmailDisplay = document.querySelector("#verify-email-display");
    const verifyOtpInput = document.querySelector("#verify-otp-input");
    const verifyMessage = document.querySelector("#verify-email-message");
    const verifySubmitBtn = document.querySelector("#verify-email-submit");
    const resendBtn = document.querySelector("#resend-verification-btn");
    const verifyCloseBtn = document.querySelector("#verify-email-close");

    let emailPendenteVerificacao = "";

    if (typeof vincularValidacaoCpfTempoReal === "function") {
        vincularValidacaoCpfTempoReal(cpfInput, cpfFeedback);
    }

    if (typeof vincularChecklistSenha === "function") {
        vincularChecklistSenha({
            inputSenha: passwordInput,
            containerChecklist: passwordChecklist,
            inputConfirmacao: confirmationInput,
            feedbackConfirmacao: confirmFeedback
        });
    }

    if (verifyOtpInput) {
        verifyOtpInput.addEventListener("input", () => {
            verifyOtpInput.value = verifyOtpInput.value.replace(/\D/g, "").slice(0, 6);
        });
    }

    function abrirModalVerificacaoEmail(emailCadastrado) {
        emailPendenteVerificacao = emailCadastrado;
        if (!verifyDialog) {
            window.location.assign("login.html?cadastro=sucesso");
            return;
        }
        if (verifyEmailDisplay) verifyEmailDisplay.textContent = emailCadastrado;
        if (verifyOtpInput) verifyOtpInput.value = "";
        if (verifyMessage) {
            verifyMessage.textContent =
                "Conta criada! Insira o código de 6 dígitos enviado para o seu e-mail.";
            verifyMessage.className = "form-message info";
        }
        if (typeof verifyDialog.showModal === "function") {
            verifyDialog.showModal();
        } else {
            verifyDialog.setAttribute("open", "open");
        }
        verifyOtpInput?.focus();
    }

    verifyCloseBtn?.addEventListener("click", () => {
        if (verifyDialog && typeof verifyDialog.close === "function") {
            verifyDialog.close();
        }
        window.location.assign("login.html?cadastro=sucesso");
    });

    resendBtn?.addEventListener("click", async () => {
        if (!emailPendenteVerificacao || !verifyMessage) return;
        resendBtn.disabled = true;
        verifyMessage.textContent = "Reenviando um novo código de verificação...";
        verifyMessage.className = "form-message info";
        try {
            const resp = await api.post("/usuarios/reenviar-verificacao", {
                email: emailPendenteVerificacao
            });
            verifyMessage.textContent =
                resp?.mensagem || "Novo código enviado! Confira sua caixa de entrada.";
            verifyMessage.className = "form-message info";
        } catch (erro) {
            verifyMessage.textContent = erro.message;
            verifyMessage.className = "form-message error";
        } finally {
            resendBtn.disabled = false;
        }
    });

    verifyForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!verifyOtpInput || !verifyMessage) return;

        const codigo = verifyOtpInput.value.trim();
        if (!/^\d{6}$/.test(codigo)) {
            verifyMessage.textContent = "Digite os 6 dígitos numéricos do código recebido.";
            verifyMessage.className = "form-message error";
            verifyOtpInput.focus();
            return;
        }

        if (verifySubmitBtn) verifySubmitBtn.disabled = true;
        verifyMessage.textContent = "Confirmando código e liberando seu acesso...";
        verifyMessage.className = "form-message info";

        try {
            const dados = await api.post("/usuarios/verificar-email", {
                email: emailPendenteVerificacao,
                codigo_otp: codigo
            });

            if (dados && typeof dados.access_token === "string" && dados.access_token) {
                api.setToken(dados.access_token);
                window.location.assign("index.html");
                return;
            }

            window.location.assign("login.html?verificado=sucesso");
        } catch (erro) {
            verifyMessage.textContent = erro.message;
            verifyMessage.className = "form-message error";
        } finally {
            if (verifySubmitBtn) verifySubmitBtn.disabled = false;
        }
    });

    if (
        !nameInput ||
        !cpfInput ||
        !emailInput ||
        !phoneInput ||
        !passwordInput ||
        !confirmationInput ||
        !message
    ) {
        console.error("O formulário de cadastro está incompleto.");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        message.textContent = "";
        message.className = "form-message";

        const nome = nameInput.value.trim();
        if (nome.length < 3) {
            message.textContent = "Informe seu nome completo (mínimo de 3 caracteres).";
            message.classList.add("error");
            nameInput.focus();
            return;
        }

        // 1. Validação matemática estrita de CPF antes do envio
        const validacaoCpf = typeof validarCpfMatematico === "function"
            ? validarCpfMatematico(cpfInput.value)
            : { valido: cpfInput.value.replace(/\D/g, "").length === 11, mensagem: "CPF inválido." };

        if (!validacaoCpf.valido) {
            cpfInput.classList.add("input-invalid");
            message.textContent = validacaoCpf.mensagem;
            message.classList.add("error");
            cpfInput.focus();
            return;
        }

        // 2. Validação de e-mail
        const email = emailInput.value.trim();
        if (!email || !emailInput.checkValidity()) {
            message.textContent = "Informe um endereço de e-mail válido.";
            message.classList.add("error");
            emailInput.focus();
            return;
        }

        // 3. Validação estrita dos 5 requisitos de senha forte
        if (typeof obterMensagemErroSenha === "function") {
            const erroSenha = obterMensagemErroSenha(passwordInput.value);
            if (erroSenha) {
                message.textContent = erroSenha;
                message.classList.add("error");
                passwordInput.focus();
                return;
            }
        }

        if (passwordInput.value !== confirmationInput.value) {
            message.textContent = "As senhas informadas não conferem.";
            message.classList.add("error");
            confirmationInput.focus();
            return;
        }

        // 4. Validação obrigatória dos Termos de Serviço e Política de Privacidade (LGPD)
        const aceitouTermos = Boolean(acceptTermsCheckbox?.checked);
        const aceitouPrivacidade = Boolean(acceptPrivacyCheckbox?.checked);
        if (!aceitouTermos || !aceitouPrivacidade) {
            message.textContent =
                "Para prosseguir, marque o aceite obrigatório dos Termos de Serviço e da Política de Privacidade (LGPD).";
            message.classList.add("error");
            (!aceitouTermos ? acceptTermsCheckbox : acceptPrivacyCheckbox)?.focus();
            return;
        }

        if (submitButton) submitButton.disabled = true;
        message.textContent = "Criando sua conta protegida e enviando código de verificação...";
        message.classList.add("info");

        try {
            await api.post("/usuarios/", {
                nome_completo: nome,
                cpf: cpfInput.value.trim(),
                email,
                telefone: phoneInput.value.trim() || null,
                senha: passwordInput.value,
                aceite_termos: true,
                aceite_privacidade: true
            });

            message.textContent =
                "Cadastro registrado! Confirme o código de 6 dígitos enviado para o seu e-mail.";
            message.className = "form-message info";
            abrirModalVerificacaoEmail(email);
        } catch (error) {
            message.textContent = error.message;
            message.className = "form-message error";
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });
});
