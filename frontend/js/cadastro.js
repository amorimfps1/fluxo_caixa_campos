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

    const form = document.querySelector("#register-form");
    if (!form) return;

    const nameInput = document.querySelector("#register-name");
    const cpfInput = document.querySelector("#register-cpf");
    const emailInput = document.querySelector("#register-email");
    const phoneInput = document.querySelector("#register-phone");
    const passwordInput = document.querySelector("#register-password");
    const confirmationInput = document.querySelector(
        "#register-password-confirm"
    );
    const message = document.querySelector("#register-message");
    const submitButton = form.querySelector('[type="submit"]');

    aplicarMascaraCpf(cpfInput);

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

        if (passwordInput.value !== confirmationInput.value) {
            message.textContent = "As senhas não conferem.";
            message.classList.add("error");
            confirmationInput.focus();
            return;
        }

        if (submitButton) submitButton.disabled = true;
        message.textContent = "Criando sua conta...";
        message.classList.add("info");

        try {
            await api.post("/usuarios/", {
                nome_completo: nameInput.value.trim(),
                cpf: cpfInput.value.trim(),
                email: emailInput.value.trim(),
                telefone: phoneInput.value.trim() || null,
                senha: passwordInput.value
            });
            window.location.assign("login.html?cadastro=sucesso");
        } catch (error) {
            message.textContent = error.message;
            message.className = "form-message error";
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });
});
