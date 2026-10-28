/*
 * FLUXO DE CAIXA
 * Módulo compartilhado de Conformidade Jurídica (Termos de Serviço & LGPD),
 * Validação Estrita de CPF, Checklist Interativo de Senha Forte e Google OAuth 2.0.
 */

const CONTEUDO_TERMOS_SERVICO = `
<article class="legal-prose">
    <h1>Termos de Serviço — Fluxo de Caixa</h1>
    <span class="legal-meta">Vigência e última atualização: Outubro de 2026 · Versão 2.0</span>

    <p>
        Bem-vindo(a) ao <strong>Fluxo de Caixa</strong>. Estes Termos de Serviço regulam o acesso e a utilização da
        plataforma digital de gestão financeira e patrimonial pessoal ("Plataforma"), composta por interface web
        responsiva e API RESTful segura. Ao criar uma conta, autenticar-se ou utilizar qualquer funcionalidade,
        você ("Usuário" ou "Titular") declara ter lido, compreendido e aceitado integralmente estes Termos.
    </p>

    <h3>1. Objeto da Plataforma</h3>
    <p>
        O <strong>Fluxo de Caixa</strong> disponibiliza ferramentas tecnológicas para organização financeira pessoal,
        incluindo cadastro e conciliação de contas bancárias, registro de entradas, saídas e transferências com
        precisão decimal contábil, acompanhamento de carteira de investimentos (Poupança, CDB, LCI/LCA, Tesouro Direto,
        Fundos de Investimento, Ações, ETFs, FIIs e Subscrições), definição de metas financeiras, orçamentos mensais
        por categoria e alertas preventivos de vencimentos.
    </p>

    <h3>2. Natureza Informativa e Ausência de Consultoria Financeira</h3>
    <p>
        A Plataforma atua exclusivamente como ferramenta de organização, consolidação de dados inseridos pelo próprio
        Usuário e visualização analítica. <strong>Nenhuma informação, gráfico, alerta ou indicador exibido constitui
        recomendação de investimento, consultoria de valores mobiliários (CVM), assessoria tributária, jurídica ou
        intermediação bancária (BACEN).</strong> Decisões financeiras tomadas a partir dos registros cadastrados são
        de responsabilidade exclusiva do Usuário.
    </p>

    <h3>3. Elegibilidade, Cadastro, Validação de CPF e Verificação Anti-Bot</h3>
    <ul>
        <li>O cadastro é destinado a pessoas físicas plenamente capazes nos termos da legislação civil brasileira.</li>
        <li>O Usuário compromete-se a fornecer dados verdadeiros, exatos e atualizados, incluindo nome completo, CPF válido de sua titularidade e endereço de e-mail ativo.</li>
        <li>A Plataforma executa validação matemática estrita dos dígitos verificadores do CPF antes da confirmação cadastral e impede duplicidade de contas por meio de indexação criptográfica cega (<em>Blind Index</em>).</li>
        <li>Para prevenção contra automações abusivas (<em>bots</em>) e fraudes de identidade, o cadastro dispara código descartável de verificação por e-mail (OTP de 6 dígitos com expiração de 15 minutos) ou validação federada via Google OAuth 2.0.</li>
    </ul>

    <h3>4. Segurança de Credenciais, Senhas Fortes e Login Social (Google OAuth 2.0)</h3>
    <ul>
        <li>A senha de acesso é pessoal e intransferível, devendo atender obrigatoriamente aos requisitos mínimos de segurança: ao menos 8 caracteres, letra maiúscula, letra minúscula, algarismo numérico e caractere especial.</li>
        <li>O Usuário também pode autenticar-se utilizando sua conta Google (OAuth 2.0), hipótese em que a identidade e a posse do e-mail são validadas criptograficamente junto aos servidores oficiais do Google.</li>
        <li>É dever do Usuário manter a confidencialidade de suas credenciais e encerrar sua sessão ao utilizar dispositivos compartilhados.</li>
    </ul>

    <h3>5. Regras de Uso Aceitável e Condutas Vedadas</h3>
    <p>É expressamente proibido ao Usuário:</p>
    <ul>
        <li>Utilizar CPF, e-mail ou dados pessoais pertencentes a terceiros sem autorização legal;</li>
        <li>Empregar scripts automatizados, varreduras de força bruta, engenharia reversa ou tentativas de contorno dos mecanismos de limitação de requisições (<em>Rate Limiting</em>) e isolamento multiusuário;</li>
        <li>Utilizar a Plataforma para registrar, ocultar ou controlar atividades ilícitas de qualquer natureza.</li>
    </ul>

    <h3>6. Disponibilidade, Manutenção e Limites Operacionais</h3>
    <p>
        Empregamos boas práticas de engenharia para manter elevada disponibilidade e integridade transacional,
        incluindo bloqueio temporário automatizado contra tentativas excessivas de autenticação (HTTP 429).
        Interrupções pontuais poderão ocorrer para manutenção evolutiva, atualizações de segurança ou por falhas
        externas de provedores de nuvem e telecomunicações.
    </p>

    <h3>7. Propriedade Intelectual</h3>
    <p>
        Todo o código-fonte, algoritmos de cálculo financeiro, arquitetura visual, logotipos em SVG, textos e
        elementos de interface do <strong>Fluxo de Caixa</strong> são protegidos pela legislação de propriedade
        intelectual e direitos autorais, sendo concedida ao Usuário apenas licença de uso pessoal, não exclusiva
        e intransferível. Os dados financeiros inseridos pelo Usuário permanecem de titularidade do próprio Usuário.
    </p>

    <h3>8. Portabilidade e Exclusão Irreversível de Conta</h3>
    <p>
        O Usuário pode exportar seu histórico de movimentações em formato aberto CSV a qualquer momento na seção de
        Relatórios/Movimentações, bem como solicitar a <strong>exclusão permanente e imediata</strong> de sua conta e
        de todos os registros associados diretamente em <strong>Configurações &gt; Zona de Perigo</strong>, mediante
        confirmação de credencial.
    </p>

    <h3>9. Proteção de Dados Pessoais (LGPD)</h3>
    <p>
        O tratamento de dados pessoais observa rigorosamente a Lei nº 13.709/2018 (Lei Geral de Proteção de Dados — LGPD),
        conforme detalhado integralmente em nossa <strong>Política de Privacidade</strong>, que integra estes Termos
        para todos os fins de direito.
    </p>

    <h3>10. Limitação de Responsabilidade e Foro</h3>
    <p>
        O <strong>Fluxo de Caixa</strong> não se responsabiliza por prejuízos decorrentes de inserção incorreta de
        lançamentos pelo Usuário, compartilhamento voluntário de senhas ou indisponibilidade de serviços de terceiros.
        Estes Termos são regidos pelas leis da República Federativa do Brasil, ficando eleito o foro do domicílio do
        Titular para dirimir eventuais controvérsias.
    </p>
</article>
`;

const CONTEUDO_POLITICA_PRIVACIDADE = `
<article class="legal-prose">
    <h1>Política de Privacidade e Conformidade LGPD</h1>
    <span class="legal-meta">Lei Geral de Proteção de Dados (Lei nº 13.709/2018) · Atualização: Outubro de 2026</span>

    <p>
        Esta Política de Privacidade descreve de forma transparente como o <strong>Fluxo de Caixa</strong> coleta,
        utiliza, armazena, criptografa e protege os dados pessoais de seus Usuários, bem como os meios diretos para o
        exercício dos direitos previstos na <strong>Lei nº 13.709/2018 (LGPD)</strong>.
    </p>

    <h3>1. Princípios e Minimização de Dados</h3>
    <p>
        Coletamos estritamente os dados mínimos necessários para autenticação segura, prevenção à fraude e execução
        das funcionalidades de controle financeiro pessoal solicitadas pelo próprio Titular, observando os princípios
        da finalidade, adequação, necessidade, segurança e prevenção (Art. 6º da LGPD).
    </p>

    <h3>2. Dados Coletados e Respectivas Finalidades</h3>
    <ul>
        <li><strong>Dados Cadastrais de Identificação (Nome completo e E-mail):</strong> utilizados para identificação personalizada no painel, envio de códigos temporários de verificação anti-bot/recuperação de acesso e comunicação transacional.</li>
        <li><strong>CPF (Dado Pessoal de Alta Criticidade Cadastral):</strong> coletado exclusivamente para validação de unicidade cadastral, prevenção contra contas falsas/automatizadas e mecanismo alternativo de recuperação de credencial.</li>
        <li><strong>Telefone (Opcional):</strong> utilizado apenas se fornecido voluntariamente pelo Titular para segurança cadastral e contato de conta.</li>
        <li><strong>Credenciais de Autenticação:</strong> senha submetida exclusivamente a hash criptográfico irreversível ou identificador federado (<code>sub</code>) validado via Google OAuth 2.0.</li>
        <li><strong>Registros Financeiros Pessoais:</strong> nomes referenciais de contas, movimentações, categorias, metas e orçamentos cadastrados pelo Usuário para geração exclusiva de seus relatórios e gráficos. Note que <strong>não solicitamos senhas bancárias, números de cartão de crédito nem chaves Pix</strong>.</li>
        <li><strong>Registros Técnicos de Segurança:</strong> hashes anônimos de controle de tentativas por endereço IP/conta para mitigação de ataques de força bruta, descartados automaticamente após a janela de retenção de 24 horas.</li>
    </ul>

    <h3>3. Bases Legais do Tratamento (Art. 7º da LGPD)</h3>
    <ul>
        <li><strong>Execução de Contrato (Art. 7º, V):</strong> prestação dos serviços de gestão financeira da Plataforma mediante aceite dos Termos de Serviço;</li>
        <li><strong>Consentimento Livre, Informado e Inequívoco (Art. 7º, I):</strong> manifestado por meio das caixas de seleção obrigatórias no momento do cadastro;</li>
        <li><strong>Prevenção à Fraude e Segurança do Titular (Art. 11, II, "g" e Art. 7º, IX):</strong> verificação de e-mail anti-bot, validação matemática de CPF e proteção contra acessos não autorizados.</li>
    </ul>

    <h3>4. Arquitetura Criptográfica e Segurança da Informação (Art. 46 da LGPD)</h3>
    <p>Aplicamos controles criptográficos em nível de aplicação e banco de dados para proteger os dados em trânsito e em repouso:</p>
    <ul>
        <li><strong>Criptografia Simétrica Autenticada de CPF e Telefone:</strong> o CPF e o telefone jamais são gravados em texto puro no banco de dados. São cifrados em repouso com <strong>Fernet (AES-128-CBC + assinatura de integridade HMAC-SHA256)</strong> utilizando chave mestra segregada no servidor (<code>CPF_ENCRYPTION_KEY</code>).</li>
        <li><strong>Indexação Cega (<em>Blind Index</em> HMAC-SHA256):</strong> a verificação de unicidade de CPF e de vínculo OAuth ocorre via resumo criptográfico unidirecional com chave derivada e separação de domínio (<code>cpf_indice</code>), impedindo consultas reversas em caso de exposição de armazenamento.</li>
        <li><strong>Senhas Irreversíveis com Argon2id:</strong> nenhuma senha é armazenada ou conhecida pela Plataforma; utilizamos algoritmo vencedor da <em>Password Hashing Competition</em> resistente a ataques por GPU/ASIC e comparação em tempo constante.</li>
        <li><strong>Códigos OTP Descartáveis:</strong> códigos de verificação de e-mail possuem 6 dígitos gerados por fonte criptograficamente segura (CSPRNG), expiram em 15 minutos, têm apenas seu hash SHA-256 persistido e são invalidados imediatamente após o primeiro uso.</li>
        <li><strong>Isolamento Estrito Multiusuário:</strong> todas as consultas SQL filtram obrigatoriamente pelo identificador do usuário autenticado via token JWT assinado (HS256), impedindo acesso cruzado (IDOR).</li>
    </ul>

    <h3>5. Autenticação Social com Google OAuth 2.0</h3>
    <p>
        Quando o Usuário opta por "Entrar com o Google", recebemos apenas o token de identidade assinado pelo Google
        contendo identificador único (<code>sub</code>), nome de exibição e e-mail verificado. Não recebemos acesso à
        sua senha do Google, caixa de e-mails, contatos ou arquivos do Google Drive.
    </p>

    <h3>6. Armazenamento no Navegador e Ausência de Rastreadores Publicitários</h3>
    <p>
        Utilizamos apenas <code>sessionStorage</code> para manter o token JWT durante a aba ativa (encerrado ao fechar
        o navegador ou clicar em "Sair") e <code>localStorage</code> para lembrar sua preferência visual de Tema Claro
        ou Tema Escuro. <strong>Não utilizamos cookies de rastreamento comportamental nem vendemos ou compartilhamos
        dados financeiros com anunciantes ou birôs de crédito.</strong>
    </p>

    <h3>7. Direitos do Titular de Dados (Art. 18 da LGPD)</h3>
    <p>O Titular pode exercer seus direitos diretamente pela interface da Plataforma, de forma imediata e gratuita:</p>
    <ul>
        <li><strong>Confirmação, Acesso e Correção:</strong> visualização e atualização imediata de nome, e-mail, telefone e senha na aba <em>Configurações</em> (<code>GET/PUT /usuarios/me</code>);</li>
        <li><strong>Portabilidade de Dados:</strong> exportação integral das movimentações financeiras em arquivo estruturado CSV compatível com planilhas;</li>
        <li><strong>Eliminação Definitiva e Revogação:</strong> exclusão permanente e em cascata da conta, dados cifrados, contas bancárias, movimentações, orçamentos, alertas e metas em <em>Configurações &gt; Zona de Perigo</em> (<code>DELETE /usuarios/me</code>).</li>
    </ul>

    <h3>8. Retenção, Descarte e Governança</h3>
    <p>
        Os dados permanecem armazenados enquanto o Usuário mantiver sua conta ativa. Efetuada a exclusão da conta pelo
        Titular, todos os registros operacionais vinculados são removidos permanentemente do banco de dados ativo.
    </p>
</article>
`;

/* =========================================================
   1. VALIDAÇÃO MATEMÁTICA ESTRITA DE CPF (FRONTEND)
========================================================= */

function formatarMascaraCpf(valor) {
    const digitos = String(valor || "").replace(/\D/g, "").slice(0, 11);
    if (digitos.length > 9) {
        return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9, 11)}`;
    }
    if (digitos.length > 6) {
        return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
    }
    if (digitos.length > 3) {
        return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
    }
    return digitos;
}

function validarCpfMatematico(valor) {
    const bruto = String(valor || "").trim();
    if (!bruto) {
        return { valido: false, incompleto: true, mensagem: "Informe seu CPF." };
    }
    if (/[^0-9.\-\s]/.test(bruto)) {
        return { valido: false, incompleto: false, mensagem: "O CPF deve conter apenas números." };
    }

    const digitos = bruto.replace(/\D/g, "");
    if (digitos.length < 11) {
        return {
            valido: false,
            incompleto: true,
            mensagem: "CPF inválido. Verifique os números digitados."
        };
    }
    if (digitos.length !== 11) {
        return {
            valido: false,
            incompleto: false,
            mensagem: "CPF inválido. Verifique os números digitados."
        };
    }

    // Bloqueia sequências com todos os dígitos repetidos (000.000.000-00 a 999.999.999-99)
    if (/^(\d)\1{10}$/.test(digitos)) {
        return {
            valido: false,
            incompleto: false,
            mensagem: "CPF inválido. Verifique os números digitados."
        };
    }

    let soma1 = 0;
    for (let i = 0; i < 9; i += 1) {
        soma1 += Number(digitos[i]) * (10 - i);
    }
    let resto1 = (soma1 * 10) % 11;
    if (resto1 === 10) resto1 = 0;

    let soma2 = 0;
    for (let i = 0; i < 10; i += 1) {
        soma2 += Number(digitos[i]) * (11 - i);
    }
    let resto2 = (soma2 * 10) % 11;
    if (resto2 === 10) resto2 = 0;

    if (resto1 !== Number(digitos[9]) || resto2 !== Number(digitos[10])) {
        return {
            valido: false,
            incompleto: false,
            mensagem: "CPF inválido. Verifique os números digitados."
        };
    }

    return {
        valido: true,
        incompleto: false,
        digitos,
        mensagem: "CPF válido verificado."
    };
}

function vincularValidacaoCpfTempoReal(inputCpf, elementoFeedback = null, elementoErro = null) {
    if (!inputCpf) return;

    const erroEl =
        elementoErro ||
        inputCpf.closest(".form-field, label")?.querySelector("small.field-error");

    const ocultarErro = () => {
        if (erroEl) {
            erroEl.textContent = "";
            erroEl.hidden = true;
        }
    };

    const exibirErro = (mensagem) => {
        if (erroEl) {
            erroEl.textContent = mensagem || "CPF inválido. Verifique os números digitados.";
            erroEl.hidden = false;
        }
    };

    const atualizarEstado = (exibirIncompleto = false) => {
        inputCpf.value = formatarMascaraCpf(inputCpf.value);
        const digitos = inputCpf.value.replace(/\D/g, "");

        if (!digitos) {
            inputCpf.classList.remove("input-valid", "input-invalid");
            inputCpf.removeAttribute("aria-invalid");
            ocultarErro();
            if (elementoFeedback) {
                elementoFeedback.hidden = false;
                elementoFeedback.textContent = "Criptografado em repouso (Fernet AES + HMAC-SHA256).";
                elementoFeedback.className = "field-help";
            }
            return;
        }

        const resultado = validarCpfMatematico(inputCpf.value);
        if (resultado.valido) {
            inputCpf.classList.add("input-valid");
            inputCpf.classList.remove("input-invalid");
            inputCpf.setAttribute("aria-invalid", "false");
            ocultarErro();
            if (elementoFeedback) {
                elementoFeedback.hidden = false;
                elementoFeedback.textContent = "✓ CPF matematicamente válido.";
                elementoFeedback.className = "field-feedback is-valid";
            }
        } else if (!resultado.incompleto || exibirIncompleto) {
            inputCpf.classList.add("input-invalid");
            inputCpf.classList.remove("input-valid");
            inputCpf.setAttribute("aria-invalid", "true");
            exibirErro(resultado.mensagem);
            if (elementoFeedback) {
                if (erroEl) {
                    elementoFeedback.hidden = true;
                } else {
                    elementoFeedback.hidden = false;
                    elementoFeedback.textContent = resultado.mensagem;
                    elementoFeedback.className = "field-feedback is-invalid";
                }
            }
        } else {
            inputCpf.classList.remove("input-valid", "input-invalid");
            inputCpf.removeAttribute("aria-invalid");
            ocultarErro();
            if (elementoFeedback) {
                elementoFeedback.hidden = false;
                elementoFeedback.textContent = `Digite os 11 números (${digitos.length}/11).`;
                elementoFeedback.className = "field-help";
            }
        }
    };

    inputCpf.addEventListener("input", () => atualizarEstado(false));
    inputCpf.addEventListener("blur", () => atualizarEstado(true));
}

/* =========================================================
   1.B VALIDAÇÃO ESTRITA DE E-MAIL EM TEMPO REAL
========================================================= */

function validarEmailFormato(email) {
    const valor = String(email || "").trim();
    if (!valor || valor.length > 254 || /\s/.test(valor)) {
        return false;
    }
    const regexEmail = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    if (!regexEmail.test(valor)) {
        return false;
    }
    const partes = valor.split("@");
    if (partes.length !== 2) return false;
    const [usuario, dominio] = partes;
    if (
        usuario.startsWith(".") ||
        usuario.endsWith(".") ||
        usuario.includes("..") ||
        dominio.startsWith(".") ||
        dominio.startsWith("-") ||
        dominio.endsWith("-") ||
        dominio.includes("..")
    ) {
        return false;
    }
    return true;
}

function vincularValidacaoEmailTempoReal(inputEmail, elementoErro = null) {
    if (!inputEmail) return;

    const erroEl =
        elementoErro ||
        inputEmail.closest(".form-field, label")?.querySelector("small.field-error");

    let jaDesfocou = false;

    const limparEstado = () => {
        inputEmail.classList.remove("input-valid", "input-invalid");
        inputEmail.removeAttribute("aria-invalid");
        if (erroEl) {
            erroEl.textContent = "";
            erroEl.hidden = true;
        }
    };

    const marcarValido = () => {
        inputEmail.classList.add("input-valid");
        inputEmail.classList.remove("input-invalid");
        inputEmail.setAttribute("aria-invalid", "false");
        if (erroEl) {
            erroEl.textContent = "";
            erroEl.hidden = true;
        }
    };

    const marcarInvalido = () => {
        inputEmail.classList.add("input-invalid");
        inputEmail.classList.remove("input-valid");
        inputEmail.setAttribute("aria-invalid", "true");
        if (erroEl) {
            erroEl.textContent = "Informe um endereço de e-mail válido (ex.: nome@dominio.com).";
            erroEl.hidden = false;
        }
    };

    inputEmail.addEventListener("input", () => {
        const valor = inputEmail.value.trim();
        if (!valor) {
            limparEstado();
            return;
        }
        if (validarEmailFormato(valor)) {
            marcarValido();
            return;
        }
        if (jaDesfocou || inputEmail.classList.contains("input-invalid")) {
            marcarInvalido();
        } else {
            inputEmail.classList.remove("input-valid");
        }
    });

    inputEmail.addEventListener("blur", () => {
        const valor = inputEmail.value.trim();
        if (!valor) {
            limparEstado();
            return;
        }
        jaDesfocou = true;
        if (validarEmailFormato(valor)) {
            marcarValido();
        } else {
            marcarInvalido();
        }
    });
}

/* =========================================================
   2. CHECKLIST INTERATIVO DE FORÇA DE SENHA EM TEMPO REAL
========================================================= */

function avaliarForcaSenha(senha) {
    const valor = String(senha || "");
    const criterios = {
        tamanho: valor.length >= 8,
        maiuscula: /[A-Z]/.test(valor),
        minuscula: /[a-z]/.test(valor),
        numero: /\d/.test(valor),
        especial: /[!@#$%^&*(),.?":{}|<>_\-\[\]\\\/+=~`';]/.test(valor)
    };
    const atendidos = Object.values(criterios).filter(Boolean).length;
    const valida = atendidos === 5;
    return { ...criterios, atendidos, valida };
}

function obterMensagemErroSenha(senha) {
    const status = avaliarForcaSenha(senha);
    if (!status.tamanho) return "A senha deve possuir no mínimo 8 caracteres.";
    if (!status.maiuscula) return "A senha deve possuir pelo menos uma letra maiúscula (A-Z).";
    if (!status.minuscula) return "A senha deve possuir pelo menos uma letra minúscula (a-z).";
    if (!status.numero) return "A senha deve possuir pelo menos um número (0-9).";
    if (!status.especial) return "A senha deve possuir pelo menos um caractere especial.";
    return "";
}

function vincularChecklistSenha({
    inputSenha,
    containerChecklist,
    inputConfirmacao = null,
    feedbackConfirmacao = null,
    erroConfirmacao = null
}) {
    if (!inputSenha || !containerChecklist) return;

    if (!containerChecklist.querySelector('[data-req="tamanho"]')) {
        containerChecklist.classList.add("password-checklist");
        containerChecklist.innerHTML = `
            <div class="password-checklist-header">
                <span>Requisitos de segurança da senha</span>
                <strong data-password-status>0/5 requisitos</strong>
            </div>
            <div class="password-strength-track" aria-hidden="true">
                <div class="password-strength-bar level-weak" style="width: 0%"></div>
            </div>
            <ul class="password-req-list">
                <li class="password-req" data-req="tamanho"><span class="password-req-dot" aria-hidden="true"></span><span>Mínimo de 8 caracteres</span></li>
                <li class="password-req" data-req="maiuscula"><span class="password-req-dot" aria-hidden="true"></span><span>Pelo menos uma letra maiúscula (A-Z)</span></li>
                <li class="password-req" data-req="minuscula"><span class="password-req-dot" aria-hidden="true"></span><span>Pelo menos uma letra minúscula (a-z)</span></li>
                <li class="password-req" data-req="numero"><span class="password-req-dot" aria-hidden="true"></span><span>Pelo menos um número (0-9)</span></li>
                <li class="password-req" data-req="especial"><span class="password-req-dot" aria-hidden="true"></span><span>Pelo menos um caractere especial (!@#$%^&amp;*(),.?":{}|&lt;&gt;_-)</span></li>
            </ul>
        `;
    }

    const barra = containerChecklist.querySelector(".password-strength-bar");
    const rotuloStatus = containerChecklist.querySelector("[data-password-status]");
    const erroConfEl =
        erroConfirmacao ||
        inputConfirmacao?.closest(".form-field, label")?.querySelector("small.field-error");

    const atualizarConfirmacao = () => {
        if (!inputConfirmacao) return;
        const s1 = inputSenha.value;
        const s2 = inputConfirmacao.value;
        if (!s2) {
            inputConfirmacao.classList.remove("input-valid", "input-invalid");
            inputConfirmacao.removeAttribute("aria-invalid");
            if (erroConfEl) {
                erroConfEl.textContent = "";
                erroConfEl.hidden = true;
            }
            if (feedbackConfirmacao) {
                feedbackConfirmacao.hidden = false;
                feedbackConfirmacao.textContent = "";
                feedbackConfirmacao.className = "field-help";
            }
            return;
        }
        if (s1 && s1 === s2) {
            inputConfirmacao.classList.add("input-valid");
            inputConfirmacao.classList.remove("input-invalid");
            inputConfirmacao.setAttribute("aria-invalid", "false");
            if (erroConfEl) {
                erroConfEl.textContent = "";
                erroConfEl.hidden = true;
            }
            if (feedbackConfirmacao) {
                feedbackConfirmacao.hidden = false;
                feedbackConfirmacao.textContent = "✓ As senhas conferem.";
                feedbackConfirmacao.className = "field-feedback is-valid";
            }
        } else {
            inputConfirmacao.classList.add("input-invalid");
            inputConfirmacao.classList.remove("input-valid");
            inputConfirmacao.setAttribute("aria-invalid", "true");
            if (erroConfEl) {
                erroConfEl.textContent = "As senhas digitadas não coincidem.";
                erroConfEl.hidden = false;
                if (feedbackConfirmacao) {
                    feedbackConfirmacao.hidden = true;
                }
            } else if (feedbackConfirmacao) {
                feedbackConfirmacao.hidden = false;
                feedbackConfirmacao.textContent = "As senhas digitadas não coincidem.";
                feedbackConfirmacao.className = "field-feedback is-invalid";
            }
        }
    };

    const atualizar = () => {
        const res = avaliarForcaSenha(inputSenha.value);
        ["tamanho", "maiuscula", "minuscula", "numero", "especial"].forEach((chave) => {
            const item = containerChecklist.querySelector(`[data-req="${chave}"]`);
            if (!item) return;
            const cumprido = Boolean(res[chave]);
            item.classList.toggle("is-met", cumprido);
            const ponto = item.querySelector(".password-req-dot");
            if (ponto) {
                ponto.textContent = cumprido ? "✓" : "";
            }
        });

        if (barra) {
            const pct = (res.atendidos / 5) * 100;
            barra.style.width = `${pct}%`;
            barra.classList.remove("level-weak", "level-medium", "level-strong");
            if (res.atendidos === 5) {
                barra.classList.add("level-strong");
            } else if (res.atendidos >= 3) {
                barra.classList.add("level-medium");
            } else {
                barra.classList.add("level-weak");
            }
        }

        if (rotuloStatus) {
            if (!inputSenha.value) {
                rotuloStatus.textContent = "0/5 requisitos";
            } else if (res.valida) {
                rotuloStatus.textContent = "Senha forte aprovada (5/5)";
            } else {
                rotuloStatus.textContent = `${res.atendidos}/5 requisitos atendidos`;
            }
        }

        atualizarConfirmacao();
    };

    inputSenha.addEventListener("input", atualizar);
    if (inputConfirmacao) {
        inputConfirmacao.addEventListener("input", atualizarConfirmacao);
    }
    atualizar();
}

/* =========================================================
   3. MODAL INTERATIVO DE TERMOS DE SERVIÇO E LGPD
========================================================= */

function garantirModalJuridico() {
    let dialog = document.getElementById("legal-dialog");
    if (dialog) return dialog;

    dialog = document.createElement("dialog");
    dialog.id = "legal-dialog";
    dialog.className = "form-dialog legal-dialog";
    dialog.setAttribute("aria-labelledby", "legal-dialog-heading");
    dialog.innerHTML = `
        <div class="dialog-body-container">
            <div class="dialog-header">
                <div>
                    <h2 id="legal-dialog-heading">Conformidade Jurídica e LGPD</h2>
                    <p id="legal-dialog-subtitle">Transparência, segurança da informação e direitos do titular.</p>
                </div>
                <button type="button" class="dialog-close" id="legal-dialog-close" aria-label="Fechar documento">&times;</button>
            </div>
            <div class="legal-scroll-area" id="legal-dialog-content"></div>
            <div class="dialog-actions">
                <a href="termos.html" target="_blank" rel="noopener" class="button-secondary" id="legal-dialog-external">
                    Abrir em página completa
                </a>
                <button type="button" class="button-primary" id="legal-dialog-ok">
                    Compreendi e fechar
                </button>
            </div>
        </div>
    `;
    document.body.append(dialog);

    const fechar = () => {
        if (typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }
    };
    dialog.querySelector("#legal-dialog-close")?.addEventListener("click", fechar);
    dialog.querySelector("#legal-dialog-ok")?.addEventListener("click", fechar);
    return dialog;
}

function abrirDocumentoJuridico(tipo) {
    const dialog = garantirModalJuridico();
    const titulo = dialog.querySelector("#legal-dialog-heading");
    const subtitulo = dialog.querySelector("#legal-dialog-subtitle");
    const conteudo = dialog.querySelector("#legal-dialog-content");
    const linkExterno = dialog.querySelector("#legal-dialog-external");

    if (tipo === "privacidade") {
        if (titulo) titulo.textContent = "Política de Privacidade e Proteção de Dados (LGPD)";
        if (subtitulo) subtitulo.textContent = "Conformidade integral com a Lei nº 13.709/2018 e criptografia de dados.";
        if (conteudo) conteudo.innerHTML = CONTEUDO_POLITICA_PRIVACIDADE;
        if (linkExterno) linkExterno.setAttribute("href", "privacidade.html");
    } else {
        if (titulo) titulo.textContent = "Termos de Serviço — Fluxo de Caixa";
        if (subtitulo) subtitulo.textContent = "Regras de utilização, responsabilidades e segurança da plataforma.";
        if (conteudo) conteudo.innerHTML = CONTEUDO_TERMOS_SERVICO;
        if (linkExterno) linkExterno.setAttribute("href", "termos.html");
    }

    if (typeof dialog.showModal === "function") {
        dialog.showModal();
    } else {
        dialog.setAttribute("open", "open");
    }
    if (conteudo) conteudo.scrollTop = 0;
}

/* =========================================================
   4. INTEGRAÇÃO GOOGLE OAUTH 2.0 (GOOGLE IDENTITY SERVICES)
========================================================= */

let _googleScriptPromise = null;

function carregarScriptGoogleGsi() {
    if (window.google && window.google.accounts && window.google.accounts.id) {
        return Promise.resolve(true);
    }
    if (_googleScriptPromise) return _googleScriptPromise;

    _googleScriptPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://accounts.google.com/gsi/client";
        script.async = true;
        script.defer = true;
        script.onload = () => resolve(true);
        script.onerror = () => reject(new Error("Não foi possível carregar o serviço de autenticação do Google."));
        document.head.append(script);
    });
    return _googleScriptPromise;
}

async function inicializarBotaoGoogleOAuth({
    buttonSelector = "#google-oauth-btn",
    gsiContainerSelector = "#google-gsi-button",
    messageSelector = "#login-message"
} = {}) {
    const botaoFallback = document.querySelector(buttonSelector);
    const containerGsi = document.querySelector(gsiContainerSelector);
    const msgEl = document.querySelector(messageSelector);
    if (!botaoFallback && !containerGsi) return;

    const exibirMensagem = (texto, tipo = "error") => {
        if (!msgEl) return;
        msgEl.textContent = texto;
        msgEl.className = `form-message ${tipo}`;
    };

    const processarCredencialGoogle = async (credential) => {
        if (!credential) {
            exibirMensagem("Não foi possível obter a credencial do Google.", "error");
            return;
        }
        if (botaoFallback) botaoFallback.disabled = true;
        exibirMensagem("Validando autenticação segura com o Google...", "info");

        try {
            api.clearToken();
            const dados = await api.post("/usuarios/auth/google", { credential });
            if (!dados || typeof dados.access_token !== "string" || !dados.access_token) {
                throw new Error("A API não retornou um token de sessão válido.");
            }
            api.setToken(dados.access_token);
            if (dados.usuario && dados.usuario.nome_completo) {
                sessionStorage.setItem("fluxo_caixa_nome_usuario", dados.usuario.nome_completo);
            }
            window.location.assign("index.html");
        } catch (erro) {
            exibirMensagem(erro.message || "Falha ao autenticar com o Google.", "error");
        } finally {
            if (botaoFallback) botaoFallback.disabled = false;
        }
    };

    let clientId = (
        window.__GOOGLE_CLIENT_ID__ ||
        document.querySelector('meta[name="google-client-id"]')?.getAttribute("content") ||
        ""
    ).trim();

    if (!clientId && typeof api !== "undefined") {
        try {
            const cfg = await api.get("/usuarios/auth/google/config");
            if (cfg && typeof cfg.client_id === "string") {
                clientId = cfg.client_id.trim();
            }
        } catch {
            // Mantém botão visível com mensagem orientativa caso a API ainda esteja iniciando
        }
    }

    if (clientId) {
        try {
            await carregarScriptGoogleGsi();
            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: (response) => processarCredencialGoogle(response?.credential),
                ux_mode: "popup",
                auto_select: false
            });

            if (containerGsi) {
                containerGsi.hidden = false;
                window.google.accounts.id.renderButton(containerGsi, {
                    type: "standard",
                    theme: "outline",
                    size: "large",
                    text: "continue_with",
                    shape: "rectangular",
                    logo_alignment: "left",
                    locale: "pt-BR",
                    width: 360
                });
                if (botaoFallback) botaoFallback.hidden = true;
                return;
            }
        } catch {
            // Se o script externo estiver bloqueado pela rede, mantém o botão customizado funcional
        }
    }

    if (botaoFallback) {
        botaoFallback.addEventListener("click", async () => {
            if (!clientId) {
                exibirMensagem(
                    "O Login com Google está pronto para uso: configure a variável GOOGLE_CLIENT_ID no servidor para habilitar a janela oficial do Google OAuth 2.0.",
                    "info"
                );
                return;
            }
            try {
                await carregarScriptGoogleGsi();
                window.google.accounts.id.prompt();
            } catch (erro) {
                exibirMensagem(erro.message, "error");
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Injeta conteúdo nas páginas dedicadas (termos.html / privacidade.html)
    const containerTermos = document.getElementById("standalone-termos-content");
    if (containerTermos) {
        containerTermos.innerHTML = CONTEUDO_TERMOS_SERVICO;
    }
    const containerPrivacidade = document.getElementById("standalone-privacidade-content");
    if (containerPrivacidade) {
        containerPrivacidade.innerHTML = CONTEUDO_POLITICA_PRIVACIDADE;
    }

    // Delegação global para abrir Termos ou Política de Privacidade em modal interativo
    document.addEventListener("click", (event) => {
        const gatilho = event.target.closest("[data-open-legal]");
        if (!gatilho) return;
        event.preventDefault();
        const tipo = gatilho.getAttribute("data-open-legal");
        abrirDocumentoJuridico(tipo);
    });
});

window.FluxoLegal = {
    formatarMascaraCpf,
    validarCpfMatematico,
    vincularValidacaoCpfTempoReal,
    validarEmailFormato,
    vincularValidacaoEmailTempoReal,
    avaliarForcaSenha,
    obterMensagemErroSenha,
    vincularChecklistSenha,
    abrirDocumentoJuridico,
    inicializarBotaoGoogleOAuth
};
