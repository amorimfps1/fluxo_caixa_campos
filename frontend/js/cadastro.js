document.addEventListener("DOMContentLoaded", () => {
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
