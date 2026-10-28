/*
 * FLUXO DE CAIXA
 * Login institucional, Google OAuth 2.0 (oficial + fluxo assistido), verificação
 * multi-canal de código OTP (E-mail Gmail ou Telefone SMS/WhatsApp) e recuperação
 * segura de senha com contador regressivo de 60s, troca de canal e modo de contingência.
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

    const params = new URLSearchParams(window.location.search);
    const message = document.querySelector("#login-message");
    if (message) {
        if (params.get("verificado") === "sucesso") {
            message.textContent =
                "Código verificado com sucesso! Entre com suas credenciais para acessar o painel.";
            message.className = "form-message info";
        } else if (params.get("cadastro") === "sucesso") {
            message.textContent =
                "Cadastro criado! Entre com seu e-mail e senha ou confirme seu código de 6 dígitos abaixo.";
            message.className = "form-message info";
        }
    }

    const form = document.querySelector("#login-form");
    if (!form) return;

    if (api.getToken()) {
        window.location.replace("index.html");
        return;
    }

    if (typeof inicializarBotaoGoogleOAuth === "function") {
        inicializarBotaoGoogleOAuth({
            buttonSelector: "#google-oauth-btn",
            gsiContainerSelector: "#google-gsi-button",
            messageSelector: "#login-message"
        });
    }

    const emailInput = document.querySelector("#email");
    const loginEmailError = document.querySelector("#login-email-error");
    const senhaInput = document.querySelector("#senha");
    const submitButton = form.querySelector('[type="submit"]');

    if (!emailInput || !senhaInput || !message) {
        console.error(
            "O formulário de login precisa dos campos #email, #senha e #login-message."
        );
        return;
    }

    if (typeof vincularValidacaoEmailTempoReal === "function") {
        vincularValidacaoEmailTempoReal(emailInput, loginEmailError);
    }

    function validarEmailComFeedback(inputEl, erroEl, mensagemContainer = null) {
        const valor = inputEl.value.trim();
        const erroDominio =
            typeof detectarErroDominioEmail === "function"
                ? detectarErroDominioEmail(valor)
                : null;
        const formatoValido =
            typeof validarEmailFormato === "function"
                ? validarEmailFormato(valor)
                : Boolean(valor && inputEl.checkValidity());

        if (!formatoValido || erroDominio) {
            const msgErro = erroDominio
                ? erroDominio.mensagem
                : "Informe um endereço de e-mail válido (ex.: nome@dominio.com).";
            inputEl.classList.add("input-invalid");
            inputEl.classList.remove("input-valid");
            inputEl.setAttribute("aria-invalid", "true");
            if (erroEl && !erroDominio) {
                erroEl.textContent = msgErro;
                erroEl.hidden = false;
            }
            if (mensagemContainer) {
                mensagemContainer.textContent = msgErro;
                mensagemContainer.className = "form-message error";
            }
            inputEl.focus();
            return false;
        }
        return true;
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
            (!email ? emailInput : senhaInput).focus();
            return;
        }

        if (!validarEmailComFeedback(emailInput, loginEmailError, message)) {
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add("is-loading");
        }

        message.textContent = "Autenticando com segurança...";
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
                submitButton.classList.remove("is-loading");
            }
        }
    });

    // =========================================================
    // 1. MODAL MULTI-CANAL DE VERIFICAÇÃO DE CÓDIGO NO LOGIN
    // =========================================================
    const openLoginVerifyTrigger = document.querySelector("#open-login-verify-trigger");
    const loginVerifyDialog = document.querySelector("#login-verify-dialog");
    const loginVerifyForm = document.querySelector("#login-verify-form");
    const loginVerifyClose = document.querySelector("#login-verify-close");
    const loginVerifySubtitle = document.querySelector("#login-verify-subtitle");
    const loginVerifyEmail = document.querySelector("#login-verify-email");
    const loginVerifyEmailError = document.querySelector("#login-verify-email-error");
    const loginChannelRadios = document.querySelectorAll('input[name="login_canal_verificacao"]');
    const loginVerifySendBtn = document.querySelector("#login-verify-send-btn");
    const loginVerifySwitchBtn = document.querySelector("#login-verify-switch-btn");
    const loginVerifyContingencyBanner = document.querySelector("#login-verify-contingency-banner");
    const loginVerifyContingencyCode = document.querySelector("#login-verify-contingency-code");
    const loginVerifyFillContingency = document.querySelector("#login-verify-fill-contingency");
    const loginVerifyOtp = document.querySelector("#login-verify-otp");
    const loginVerifyMessage = document.querySelector("#login-verify-message");
    const loginVerifySubmit = document.querySelector("#login-verify-submit");

    let timerLoginVerifyId = null;
    let segundosLoginVerify = 0;

    if (typeof vincularValidacaoEmailTempoReal === "function" && loginVerifyEmail) {
        vincularValidacaoEmailTempoReal(loginVerifyEmail, loginVerifyEmailError);
    }

    if (loginVerifyOtp) {
        loginVerifyOtp.addEventListener("input", () => {
            loginVerifyOtp.value = loginVerifyOtp.value.replace(/\D/g, "").slice(0, 6);
        });
    }

    function obterCanalLoginVerify() {
        const marcado = document.querySelector('input[name="login_canal_verificacao"]:checked');
        return marcado ? marcado.value : "email";
    }

    function atualizarCardsCanalLoginVerify() {
        const canal = obterCanalLoginVerify();
        const porTel = canal === "telefone";
        loginChannelRadios.forEach((radio) => {
            const card = radio.closest(".channel-option-card");
            if (card) card.classList.toggle("is-selected", radio.checked);
        });
        if (loginVerifySwitchBtn) {
            loginVerifySwitchBtn.textContent = porTel
                ? "Não recebeu no Telefone? Enviar código para o meu E-mail"
                : "Não recebeu no Gmail? Enviar código para o meu Telefone";
        }
    }

    loginChannelRadios.forEach((radio) => {
        radio.addEventListener("change", atualizarCardsCanalLoginVerify);
    });
    atualizarCardsCanalLoginVerify();

    function iniciarContadorLoginVerify(segundos = 60) {
        if (timerLoginVerifyId) {
            clearInterval(timerLoginVerifyId);
            timerLoginVerifyId = null;
        }
        segundosLoginVerify = segundos;
        const atualizar = () => {
            if (!loginVerifySendBtn) return;
            if (segundosLoginVerify > 0) {
                loginVerifySendBtn.disabled = true;
                loginVerifySendBtn.textContent = `Reenviar código (${segundosLoginVerify}s)`;
            } else {
                loginVerifySendBtn.disabled = false;
                loginVerifySendBtn.textContent = "Reenviar código";
                if (timerLoginVerifyId) {
                    clearInterval(timerLoginVerifyId);
                    timerLoginVerifyId = null;
                }
            }
        };
        atualizar();
        timerLoginVerifyId = setInterval(() => {
            segundosLoginVerify -= 1;
            atualizar();
        }, 1000);
    }

    async function enviarCodigoLoginVerify(canalForcado = null) {
        if (!loginVerifyEmail || !loginVerifyMessage) return;

        if (canalForcado) {
            loginChannelRadios.forEach((radio) => {
                radio.checked = radio.value === canalForcado;
            });
            atualizarCardsCanalLoginVerify();
        }

        if (!validarEmailComFeedback(loginVerifyEmail, loginVerifyEmailError, loginVerifyMessage)) {
            return;
        }

        const email = loginVerifyEmail.value.trim();
        const canal = obterCanalLoginVerify();

        if (loginVerifySendBtn) loginVerifySendBtn.disabled = true;
        if (loginVerifySwitchBtn) loginVerifySwitchBtn.disabled = true;
        loginVerifyMessage.textContent =
            canal === "telefone"
                ? "Enviando código de 6 dígitos para o seu telefone cadastrado..."
                : "Enviando código de 6 dígitos para o seu e-mail...";
        loginVerifyMessage.className = "form-message info";

        try {
            const resp = await api.post("/usuarios/enviar-codigo", {
                email,
                canal_verificacao: canal
            });

            if (loginVerifySubtitle && resp?.destino_mascarado) {
                loginVerifySubtitle.textContent = `Código de 6 dígitos enviado para ${resp.destino_mascarado}.`;
            }

            if (loginVerifyContingencyBanner && loginVerifyContingencyCode) {
                if (resp?.modo_contingencia && resp?.codigo_demonstracao) {
                    loginVerifyContingencyCode.textContent = resp.codigo_demonstracao;
                    loginVerifyContingencyBanner.hidden = false;
                } else {
                    loginVerifyContingencyCode.textContent = "";
                    loginVerifyContingencyBanner.hidden = true;
                }
            }

            loginVerifyMessage.textContent =
                resp?.mensagem || "Código enviado! Digite os 6 dígitos abaixo.";
            loginVerifyMessage.className = "form-message info";
            iniciarContadorLoginVerify(60);
            loginVerifyOtp?.focus();
        } catch (erro) {
            loginVerifyMessage.textContent = erro.message;
            loginVerifyMessage.className = "form-message error";
            if (segundosLoginVerify <= 0 && loginVerifySendBtn) {
                loginVerifySendBtn.disabled = false;
            }
        } finally {
            if (loginVerifySwitchBtn) loginVerifySwitchBtn.disabled = false;
        }
    }

    loginVerifyFillContingency?.addEventListener("click", () => {
        if (loginVerifyOtp && loginVerifyContingencyCode?.textContent) {
            loginVerifyOtp.value = loginVerifyContingencyCode.textContent.trim();
            loginVerifyOtp.focus();
        }
    });

    openLoginVerifyTrigger?.addEventListener("click", () => {
        if (!loginVerifyDialog) return;
        loginVerifyForm?.reset();
        atualizarCardsCanalLoginVerify();
        if (loginVerifyContingencyBanner) loginVerifyContingencyBanner.hidden = true;
        if (loginVerifyMessage) {
            loginVerifyMessage.textContent = "";
            loginVerifyMessage.className = "form-message";
        }
        if (loginVerifyEmail && emailInput.value.trim()) {
            loginVerifyEmail.value = emailInput.value.trim();
        }
        if (typeof loginVerifyDialog.showModal === "function") {
            loginVerifyDialog.showModal();
        } else {
            loginVerifyDialog.setAttribute("open", "open");
        }
    });

    loginVerifyClose?.addEventListener("click", () => {
        if (timerLoginVerifyId) {
            clearInterval(timerLoginVerifyId);
            timerLoginVerifyId = null;
        }
        if (loginVerifyDialog && typeof loginVerifyDialog.close === "function") {
            loginVerifyDialog.close();
        } else {
            loginVerifyDialog?.removeAttribute("open");
        }
    });

    loginVerifySendBtn?.addEventListener("click", async () => {
        if (segundosLoginVerify > 0) return;
        await enviarCodigoLoginVerify();
    });

    loginVerifySwitchBtn?.addEventListener("click", async () => {
        const proximo = obterCanalLoginVerify() === "email" ? "telefone" : "email";
        await enviarCodigoLoginVerify(proximo);
    });

    loginVerifyForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!loginVerifyEmail || !loginVerifyOtp || !loginVerifyMessage) return;

        if (!validarEmailComFeedback(loginVerifyEmail, loginVerifyEmailError, loginVerifyMessage)) {
            return;
        }

        const codigo = loginVerifyOtp.value.trim();
        if (!/^\d{6}$/.test(codigo)) {
            loginVerifyMessage.textContent = "Digite os 6 dígitos numéricos do código recebido.";
            loginVerifyMessage.className = "form-message error";
            loginVerifyOtp.focus();
            return;
        }

        if (loginVerifySubmit) loginVerifySubmit.disabled = true;
        loginVerifyMessage.textContent = "Confirmando código e autenticando...";
        loginVerifyMessage.className = "form-message info";

        try {
            const dados = await api.post("/usuarios/verificar-email", {
                email: loginVerifyEmail.value.trim(),
                codigo_otp: codigo
            });
            if (timerLoginVerifyId) {
                clearInterval(timerLoginVerifyId);
                timerLoginVerifyId = null;
            }
            if (dados && typeof dados.access_token === "string" && dados.access_token) {
                api.setToken(dados.access_token);
                window.location.assign("index.html");
                return;
            }
            loginVerifyDialog?.close?.();
            message.textContent = "Conta verificada com sucesso! Entre com sua senha.";
            message.className = "form-message info";
        } catch (erro) {
            loginVerifyMessage.textContent = erro.message;
            loginVerifyMessage.className = "form-message error";
        } finally {
            if (loginVerifySubmit) loginVerifySubmit.disabled = false;
        }
    });

    // =========================================================
    // 2. MODAL: ESQUECEU A SENHA? (OTP POR E-MAIL, TELEFONE OU CPF)
    // =========================================================
    const forgotTrigger = document.querySelector("#forgot-password-trigger");
    const forgotDialog = document.querySelector("#forgot-password-dialog");
    const forgotForm = document.querySelector("#forgot-password-form");
    const forgotClose = document.querySelector("#forgot-password-close");
    const forgotCancel = document.querySelector("#forgot-password-cancel");
    const forgotSubmit = document.querySelector("#forgot-password-submit");
    const sendOtpButton = document.querySelector("#send-otp-button");
    const resetSwitchChannelBtn = document.querySelector("#reset-switch-channel-btn");
    const resetChannelRadios = document.querySelectorAll('input[name="reset_canal_verificacao"]');
    const resetDestinationHelp = document.querySelector("#reset-destination-help");
    const resetContingencyBanner = document.querySelector("#reset-contingency-banner");
    const resetContingencyCode = document.querySelector("#reset-contingency-code");
    const resetFillContingencyBtn = document.querySelector("#reset-fill-contingency-btn");

    const resetEmailInput = document.querySelector("#reset-email");
    const resetEmailError = document.querySelector("#reset-email-error");
    const resetOtpInput = document.querySelector("#reset-otp");
    const resetCpfInput = document.querySelector("#reset-cpf");
    const resetCpfFeedback = document.querySelector("#reset-cpf-feedback");
    const resetPasswordInput = document.querySelector("#reset-password");
    const resetPasswordChecklist = document.querySelector("#reset-password-checklist");
    const resetConfirmInput = document.querySelector("#reset-password-confirm");
    const resetConfirmFeedback = document.querySelector("#reset-confirm-feedback");
    const resetMessage = document.querySelector("#reset-message");

    let timerResetOtpId = null;
    let segundosResetOtp = 0;

    if (typeof vincularValidacaoEmailTempoReal === "function" && resetEmailInput) {
        vincularValidacaoEmailTempoReal(resetEmailInput, resetEmailError);
    }

    if (typeof vincularValidacaoCpfTempoReal === "function") {
        vincularValidacaoCpfTempoReal(resetCpfInput, resetCpfFeedback);
    }

    if (typeof vincularChecklistSenha === "function") {
        vincularChecklistSenha({
            inputSenha: resetPasswordInput,
            containerChecklist: resetPasswordChecklist,
            inputConfirmacao: resetConfirmInput,
            feedbackConfirmacao: resetConfirmFeedback
        });
    }

    if (resetOtpInput) {
        resetOtpInput.addEventListener("input", () => {
            resetOtpInput.value = resetOtpInput.value.replace(/\D/g, "").slice(0, 6);
        });
    }

    function obterCanalResetSelecionado() {
        const marcado = document.querySelector('input[name="reset_canal_verificacao"]:checked');
        return marcado ? marcado.value : "email";
    }

    function atualizarCardsCanalReset() {
        const canal = obterCanalResetSelecionado();
        const porTel = canal === "telefone";
        resetChannelRadios.forEach((radio) => {
            const card = radio.closest(".channel-option-card");
            if (card) card.classList.toggle("is-selected", radio.checked);
        });
        if (resetSwitchChannelBtn) {
            resetSwitchChannelBtn.textContent = porTel
                ? "Não recebeu no Telefone? Enviar código para o meu E-mail"
                : "Não recebeu no Gmail? Enviar código para o meu Telefone";
        }
    }

    resetChannelRadios.forEach((radio) => {
        radio.addEventListener("change", atualizarCardsCanalReset);
    });
    atualizarCardsCanalReset();

    function iniciarContadorResetOtp(segundos = 60) {
        if (timerResetOtpId) {
            clearInterval(timerResetOtpId);
            timerResetOtpId = null;
        }
        segundosResetOtp = segundos;

        const atualizar = () => {
            if (!sendOtpButton) return;
            if (segundosResetOtp > 0) {
                sendOtpButton.disabled = true;
                sendOtpButton.textContent = `Reenviar (${segundosResetOtp}s)`;
            } else {
                sendOtpButton.disabled = false;
                sendOtpButton.textContent = "Reenviar código";
                if (timerResetOtpId) {
                    clearInterval(timerResetOtpId);
                    timerResetOtpId = null;
                }
            }
        };

        atualizar();
        timerResetOtpId = setInterval(() => {
            segundosResetOtp -= 1;
            atualizar();
        }, 1000);
    }

    resetFillContingencyBtn?.addEventListener("click", () => {
        if (resetOtpInput && resetContingencyCode?.textContent) {
            resetOtpInput.value = resetContingencyCode.textContent.trim();
            resetOtpInput.focus();
        }
    });

    function abrirModalRedefinicao() {
        if (!forgotDialog) return;
        if (forgotForm) forgotForm.reset();
        if (timerResetOtpId) {
            clearInterval(timerResetOtpId);
            timerResetOtpId = null;
        }
        segundosResetOtp = 0;
        if (sendOtpButton) {
            sendOtpButton.disabled = false;
            sendOtpButton.textContent = "Enviar código";
        }
        if (resetContingencyBanner) {
            resetContingencyBanner.hidden = true;
        }
        if (resetDestinationHelp) {
            resetDestinationHelp.textContent =
                "Código seguro de 6 dígitos válido por 15 minutos.";
        }
        atualizarCardsCanalReset();
        if (resetMessage) {
            resetMessage.textContent = "";
            resetMessage.className = "form-message";
        }
        if (resetEmailInput && emailInput.value.trim()) {
            resetEmailInput.value = emailInput.value.trim();
        }
        if (resetPasswordInput) {
            resetPasswordInput.dispatchEvent(new Event("input"));
        }
        if (typeof forgotDialog.showModal === "function") {
            forgotDialog.showModal();
        } else {
            forgotDialog.setAttribute("open", "open");
        }
    }

    function fecharModalRedefinicao() {
        if (timerResetOtpId) {
            clearInterval(timerResetOtpId);
            timerResetOtpId = null;
        }
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

    async function solicitarCodigoRecuperacao(canalForcado = null) {
        if (!sendOtpButton || !resetEmailInput || !resetMessage) return;

        if (canalForcado) {
            resetChannelRadios.forEach((radio) => {
                radio.checked = radio.value === canalForcado;
            });
            atualizarCardsCanalReset();
        }

        resetMessage.textContent = "";
        resetMessage.className = "form-message";

        if (!validarEmailComFeedback(resetEmailInput, resetEmailError, resetMessage)) {
            return;
        }

        const email = resetEmailInput.value.trim();
        const canal = obterCanalResetSelecionado();

        sendOtpButton.disabled = true;
        if (resetSwitchChannelBtn) resetSwitchChannelBtn.disabled = true;
        resetMessage.textContent =
            canal === "telefone"
                ? "Enviando código de recuperação para o seu telefone cadastrado..."
                : "Enviando código de recuperação para o seu e-mail...";
        resetMessage.classList.add("info");

        try {
            const resposta = await api.post("/usuarios/esqueci-senha", {
                email,
                canal_verificacao: canal
            });

            if (resetDestinationHelp && resposta?.destino_mascarado) {
                resetDestinationHelp.textContent = `Código enviado para ${resposta.destino_mascarado} (válido por 15 minutos).`;
            }

            if (resetContingencyBanner && resetContingencyCode) {
                if (resposta?.modo_contingencia && resposta?.codigo_demonstracao) {
                    resetContingencyCode.textContent = resposta.codigo_demonstracao;
                    resetContingencyBanner.hidden = false;
                } else {
                    resetContingencyCode.textContent = "";
                    resetContingencyBanner.hidden = true;
                }
            }

            resetMessage.textContent =
                resposta?.mensagem ||
                "Código enviado! Digite os 6 dígitos recebidos abaixo.";
            resetMessage.className = "form-message info";
            iniciarContadorResetOtp(60);
            if (resetOtpInput) resetOtpInput.focus();
        } catch (error) {
            resetMessage.textContent = error.message;
            resetMessage.className = "form-message error";
            if (segundosResetOtp <= 0) {
                sendOtpButton.disabled = false;
            }
        } finally {
            if (resetSwitchChannelBtn) resetSwitchChannelBtn.disabled = false;
        }
    }

    sendOtpButton?.addEventListener("click", async () => {
        if (segundosResetOtp > 0) return;
        await solicitarCodigoRecuperacao();
    });

    resetSwitchChannelBtn?.addEventListener("click", async () => {
        const proximoCanal = obterCanalResetSelecionado() === "email" ? "telefone" : "email";
        await solicitarCodigoRecuperacao(proximoCanal);
    });

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

            if (!validarEmailComFeedback(resetEmailInput, resetEmailError, resetMessage)) {
                return;
            }

            if (codigoOtp && !/^\d{6}$/.test(codigoOtp)) {
                resetMessage.textContent = "O código OTP deve conter exatamente 6 números.";
                resetMessage.classList.add("error");
                resetOtpInput?.focus();
                return;
            }

            if (!codigoOtp && cpf && typeof validarCpfMatematico === "function") {
                const validacaoCpf = validarCpfMatematico(cpf);
                if (!validacaoCpf.valido) {
                    resetMessage.textContent = validacaoCpf.mensagem;
                    resetMessage.classList.add("error");
                    resetCpfInput?.focus();
                    return;
                }
            }

            if (typeof obterMensagemErroSenha === "function") {
                const erroSenha = obterMensagemErroSenha(novaSenha);
                if (erroSenha) {
                    resetMessage.textContent = erroSenha;
                    resetMessage.classList.add("error");
                    resetPasswordInput.focus();
                    return;
                }
            }

            if (novaSenha !== confirmarSenha) {
                resetMessage.textContent = "As senhas informadas não conferem.";
                resetMessage.classList.add("error");
                resetConfirmInput.focus();
                return;
            }

            if (forgotSubmit) forgotSubmit.disabled = true;
            resetMessage.textContent = "Validando credencial e redefinindo senha...";
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
