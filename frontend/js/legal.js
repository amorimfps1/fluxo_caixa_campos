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
   1.B VALIDAÇÃO ESTRITA DE TELEFONE BRASILEIRO (DDD 11-99 E E.164)
========================================================= */

function formatarMascaraTelefone(valor) {
    const bruto = String(valor || "");
    const temMais55 = /^\s*\+55/.test(bruto);
    const temMaisInternacional = /^\s*\+/.test(bruto) && !temMais55;

    if (temMaisInternacional) {
        const limpoInt = bruto.replace(/[^\d+ ()-]/g, "").slice(0, 22);
        return limpoInt;
    }

    let digitos = bruto.replace(/\D/g, "");
    if (temMais55 && digitos.startsWith("55")) {
        digitos = digitos.slice(2);
    }
    digitos = digitos.slice(0, 11);

    if (!digitos) {
        return temMais55 ? "+55 " : "";
    }

    let formatado = "";
    if (digitos.length <= 2) {
        formatado = `(${digitos}`;
    } else if (digitos.length <= 6) {
        formatado = `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`;
    } else if (digitos.length <= 10) {
        formatado = `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
    } else {
        formatado = `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7, 11)}`;
    }

    return temMais55 ? `+55 ${formatado}` : formatado;
}

function validarTelefoneBrasileiro(valor, { obrigatorio = false } = {}) {
    const bruto = String(valor || "").trim();
    if (!bruto) {
        return {
            valido: !obrigatorio,
            incompleto: true,
            e164: "",
            mensagem: obrigatorio
                ? "Informe um telefone válido com DDD para receber o código por SMS ou WhatsApp."
                : ""
        };
    }

    if (/[^0-9+().\-\s]/.test(bruto)) {
        return {
            valido: false,
            incompleto: false,
            e164: "",
            mensagem: "O telefone contém caracteres inválidos."
        };
    }

    const digitosTotais = bruto.replace(/\D/g, "");
    if (bruto.startsWith("+") && !bruto.startsWith("+55")) {
        if (digitosTotais.length >= 10 && digitosTotais.length <= 15) {
            return {
                valido: true,
                incompleto: false,
                e164: `+${digitosTotais}`,
                mensagem: "Telefone internacional válido."
            };
        }
        return {
            valido: false,
            incompleto: digitosTotais.length < 10,
            e164: "",
            mensagem: "Informe um telefone válido com código do país (10 a 15 dígitos)."
        };
    }

    let nacional = digitosTotais;
    if ((bruto.startsWith("+55") || nacional.length === 12 || nacional.length === 13) && nacional.startsWith("55")) {
        nacional = nacional.slice(2);
    }

    if (nacional.length < 10) {
        return {
            valido: false,
            incompleto: true,
            e164: "",
            mensagem: "Informe o DDD (11 a 99) seguido do telefone com 8 ou 9 dígitos."
        };
    }

    if (nacional.length > 11) {
        return {
            valido: false,
            incompleto: false,
            e164: "",
            mensagem: "Telefone inválido. Use o formato (DD) 9XXXX-XXXX."
        };
    }

    const ddd = Number(nacional.slice(0, 2));
    if (!Number.isInteger(ddd) || ddd < 11 || ddd > 99) {
        return {
            valido: false,
            incompleto: false,
            e164: "",
            mensagem: "DDD inválido. Informe um DDD brasileiro válido entre 11 e 99."
        };
    }

    if (nacional.length === 11 && nacional[2] !== "9") {
        return {
            valido: false,
            incompleto: false,
            e164: "",
            mensagem: "Celulares com 11 dígitos devem começar com 9 após o DDD."
        };
    }

    return {
        valido: true,
        incompleto: false,
        e164: `+55${nacional}`,
        nacional,
        mensagem: "Telefone válido."
    };
}

function vincularValidacaoTelefoneTempoReal(
    inputTelefone,
    elementoErro = null,
    isObrigatorioFn = () => false
) {
    if (!inputTelefone) return null;

    const erroEl =
        elementoErro ||
        inputTelefone.closest(".form-field, label")?.querySelector("small.field-error");

    const atualizarEstado = (exibirIncompleto = false) => {
        inputTelefone.value = formatarMascaraTelefone(inputTelefone.value);
        const obrigatorio = Boolean(typeof isObrigatorioFn === "function" ? isObrigatorioFn() : isObrigatorioFn);
        const digitos = inputTelefone.value.replace(/\D/g, "");

        if (!digitos) {
            if (obrigatorio && exibirIncompleto) {
                inputTelefone.classList.add("input-invalid");
                inputTelefone.classList.remove("input-valid");
                inputTelefone.setAttribute("aria-invalid", "true");
                if (erroEl) {
                    erroEl.textContent =
                        "Informe seu telefone com DDD para receber o código via SMS ou WhatsApp.";
                    erroEl.hidden = false;
                }
            } else {
                inputTelefone.classList.remove("input-valid", "input-invalid");
                inputTelefone.removeAttribute("aria-invalid");
                if (erroEl) {
                    erroEl.textContent = "";
                    erroEl.hidden = true;
                }
            }
            return;
        }

        const res = validarTelefoneBrasileiro(inputTelefone.value, { obrigatorio });
        if (res.valido) {
            inputTelefone.classList.add("input-valid");
            inputTelefone.classList.remove("input-invalid");
            inputTelefone.setAttribute("aria-invalid", "false");
            if (erroEl) {
                erroEl.textContent = "";
                erroEl.hidden = true;
            }
        } else if (!res.incompleto || exibirIncompleto) {
            inputTelefone.classList.add("input-invalid");
            inputTelefone.classList.remove("input-valid");
            inputTelefone.setAttribute("aria-invalid", "true");
            if (erroEl) {
                erroEl.textContent = res.mensagem;
                erroEl.hidden = false;
            }
        } else {
            inputTelefone.classList.remove("input-valid", "input-invalid");
            inputTelefone.removeAttribute("aria-invalid");
            if (erroEl) {
                erroEl.textContent = "";
                erroEl.hidden = true;
            }
        }
    };

    inputTelefone.addEventListener("input", () => atualizarEstado(false));
    inputTelefone.addEventListener("blur", () => atualizarEstado(true));
    return { revalidar: atualizarEstado };
}

function mascararEmailCliente(email) {
    const limpo = String(email || "").trim().toLowerCase();
    if (!limpo.includes("@")) return limpo || "—";
    const [local, dominio] = limpo.split("@");
    const prefixo = local.length <= 2 ? local.slice(0, 1) || "*" : local.slice(0, 2);
    return `${prefixo}***@${dominio}`;
}

function mascararTelefoneCliente(telefone) {
    const digitos = String(telefone || "").replace(/\D/g, "");
    let nac = digitos;
    if ((nac.length === 12 || nac.length === 13) && nac.startsWith("55")) {
        nac = nac.slice(2);
    }
    if (nac.length === 11) {
        return `(${nac.slice(0, 2)}) ${nac[2]}****-${nac.slice(-4)}`;
    }
    if (nac.length === 10) {
        return `(${nac.slice(0, 2)}) ****-${nac.slice(-4)}`;
    }
    return telefone || "(**) *****-****";
}

/* =========================================================
   1.C VALIDAÇÃO ESTRITA DE E-MAIL E DOMÍNIOS EM TEMPO REAL
========================================================= */

const MAPA_DOMINIOS_EMAIL_SUGERIDOS = {
    "gamil.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.cmo": "gmail.com",
    "gmail.cm": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmal.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "outlok.com": "outlook.com",
    "outllok.com": "outlook.com",
    "outlook.con": "outlook.com",
    "yaho.com": "yahoo.com",
    "yahooo.com": "yahoo.com",
    "yahoo.con": "yahoo.com"
};

function detectarErroDominioEmail(email) {
    const valor = String(email || "").trim().toLowerCase();
    if (!valor.includes("@")) return null;
    const partes = valor.split("@");
    if (partes.length !== 2 || !partes[0] || !partes[1]) return null;
    const [usuario, dominio] = partes;
    const dominioSugerido = MAPA_DOMINIOS_EMAIL_SUGERIDOS[dominio];
    if (!dominioSugerido) return null;
    const sugestaoEmail = `${usuario}@${dominioSugerido}`;
    return {
        dominioDigitado: dominio,
        dominioSugerido,
        sugestaoEmail,
        mensagem: `Domínio '@${dominio}' parece incorreto. Você quis dizer ${sugestaoEmail}?`
    };
}

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
    if (detectarErroDominioEmail(valor)) {
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

    const renderizarSugestaoDominio = (erroDominio) => {
        inputEmail.classList.add("input-invalid");
        inputEmail.classList.remove("input-valid");
        inputEmail.setAttribute("aria-invalid", "true");
        if (!erroEl) return;

        erroEl.replaceChildren();
        const spanTexto = document.createElement("span");
        spanTexto.textContent = `${erroDominio.mensagem} `;

        const btnCorrigir = document.createElement("button");
        btnCorrigir.type = "button";
        btnCorrigir.className = "email-typo-fix-btn";
        btnCorrigir.textContent = `Usar @${erroDominio.dominioSugerido}`;
        btnCorrigir.addEventListener("click", () => {
            inputEmail.value = erroDominio.sugestaoEmail;
            marcarValido();
            inputEmail.focus();
        });

        erroEl.append(spanTexto, btnCorrigir);
        erroEl.hidden = false;
    };

    const marcarInvalido = (valorAtual = "") => {
        const erroDominio = detectarErroDominioEmail(valorAtual);
        if (erroDominio) {
            renderizarSugestaoDominio(erroDominio);
            return;
        }
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
        const erroDominio = detectarErroDominioEmail(valor);
        if (erroDominio) {
            renderizarSugestaoDominio(erroDominio);
            return;
        }
        if (validarEmailFormato(valor)) {
            marcarValido();
            return;
        }
        if (jaDesfocou || inputEmail.classList.contains("input-invalid")) {
            marcarInvalido(valor);
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
            marcarInvalido(valor);
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
   4. INTEGRAÇÃO GOOGLE OAUTH 2.0 + COMPLETAR CADASTRO + FLUXO ASSISTIDO
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
        script.onerror = () => reject(new Error("Não foi possível carregar o serviço externo do Google."));
        document.head.append(script);
    });
    return _googleScriptPromise;
}

function abrirModalCompletarCadastroGoogle(nomeUsuario = "") {
    return new Promise((resolve) => {
        let dialog = document.getElementById("google-complete-profile-dialog");
        if (dialog) dialog.remove();

        dialog = document.createElement("dialog");
        dialog.id = "google-complete-profile-dialog";
        dialog.className = "form-dialog";
        dialog.setAttribute("aria-labelledby", "google-complete-title");
        dialog.innerHTML = `
            <form id="google-complete-form" class="dialog-form" novalidate>
                <div class="dialog-header">
                    <div>
                        <h2 id="google-complete-title">Complete seu cadastro rápido</h2>
                        <p>
                            Conta Google autenticada${nomeUsuario ? ` (${nomeUsuario})` : ""}! Informe seu CPF e Telefone para habilitar recuperação segura e proteção LGPD.
                        </p>
                    </div>
                </div>
                <div class="form-field">
                    <label for="google-complete-cpf">CPF do titular</label>
                    <input
                        id="google-complete-cpf"
                        type="text"
                        inputmode="numeric"
                        maxlength="14"
                        placeholder="000.000.000-00"
                        required
                    >
                    <small class="field-error" id="google-complete-cpf-error" role="alert" hidden></small>
                    <span class="field-help" id="google-complete-cpf-help">Criptografado com Fernet AES + Blind Index HMAC.</span>
                </div>
                <div class="form-field">
                    <label for="google-complete-phone">Telefone com DDD (SMS / WhatsApp)</label>
                    <input
                        id="google-complete-phone"
                        type="tel"
                        inputmode="tel"
                        maxlength="20"
                        placeholder="(11) 98765-4321"
                    >
                    <small class="field-error" id="google-complete-phone-error" role="alert" hidden></small>
                </div>
                <p id="google-complete-message" class="form-message" role="status" aria-live="polite"></p>
                <div class="dialog-actions">
                    <button type="button" class="button-secondary" id="google-complete-skip">
                        Concluir depois
                    </button>
                    <button type="submit" class="button-primary" id="google-complete-submit">
                        Salvar e acessar painel
                    </button>
                </div>
            </form>
        `;
        document.body.append(dialog);

        const inputCpf = dialog.querySelector("#google-complete-cpf");
        const helpCpf = dialog.querySelector("#google-complete-cpf-help");
        const errCpf = dialog.querySelector("#google-complete-cpf-error");
        const inputTel = dialog.querySelector("#google-complete-phone");
        const errTel = dialog.querySelector("#google-complete-phone-error");
        const msg = dialog.querySelector("#google-complete-message");
        const btnSkip = dialog.querySelector("#google-complete-skip");
        const btnSubmit = dialog.querySelector("#google-complete-submit");
        const form = dialog.querySelector("#google-complete-form");

        vincularValidacaoCpfTempoReal(inputCpf, helpCpf, errCpf);
        vincularValidacaoTelefoneTempoReal(inputTel, errTel, () => false);

        const finalizar = () => {
            if (typeof dialog.close === "function" && dialog.open) {
                dialog.close();
            }
            resolve();
        };

        btnSkip?.addEventListener("click", finalizar);

        form?.addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const valCpf = validarCpfMatematico(inputCpf.value);
            if (!valCpf.valido) {
                if (errCpf) {
                    errCpf.textContent = valCpf.mensagem;
                    errCpf.hidden = false;
                }
                inputCpf.classList.add("input-invalid");
                inputCpf.focus();
                return;
            }

            const telTexto = inputTel.value.trim();
            if (telTexto) {
                const valTel = validarTelefoneBrasileiro(telTexto, { obrigatorio: false });
                if (!valTel.valido) {
                    if (errTel) {
                        errTel.textContent = valTel.mensagem;
                        errTel.hidden = false;
                    }
                    inputTel.classList.add("input-invalid");
                    inputTel.focus();
                    return;
                }
            }

            if (btnSubmit) btnSubmit.disabled = true;
            if (msg) {
                msg.textContent = "Salvando seus dados criptografados...";
                msg.className = "form-message info";
            }

            try {
                await api.put("/usuarios/me/completar-cadastro", {
                    cpf: valCpf.digitos,
                    telefone: telTexto || null
                });
                finalizar();
            } catch (erro) {
                if (msg) {
                    msg.textContent = erro.message || "Não foi possível salvar os dados.";
                    msg.className = "form-message error";
                }
                if (btnSubmit) btnSubmit.disabled = false;
            }
        });

        if (typeof dialog.showModal === "function") {
            dialog.showModal();
        } else {
            dialog.setAttribute("open", "open");
        }
        inputCpf?.focus();
    });
}

function abrirModalGoogleAssistido({ onAuthenticated }) {
    let dialog = document.getElementById("google-assisted-dialog");
    if (dialog) dialog.remove();

    const emailPreenchido = (
        document.querySelector("#email")?.value ||
        document.querySelector("#register-email")?.value ||
        ""
    ).trim();
    const nomePreenchido = (document.querySelector("#register-name")?.value || "").trim();
    const cpfPreenchido = (document.querySelector("#register-cpf")?.value || "").trim();
    const telPreenchido = (document.querySelector("#register-phone")?.value || "").trim();

    dialog = document.createElement("dialog");
    dialog.id = "google-assisted-dialog";
    dialog.className = "form-dialog";
    dialog.setAttribute("aria-labelledby", "google-assisted-title");
    dialog.innerHTML = `
        <form id="google-assisted-form" class="dialog-form" novalidate>
            <div class="dialog-header">
                <div>
                    <h2 id="google-assisted-title">Continuar com o Google</h2>
                    <p>
                        Informe sua conta Gmail para entrar ou criar sua conta verificada instantaneamente (sem necessidade de código OTP).
                    </p>
                </div>
                <button type="button" class="dialog-close" id="google-assisted-close" aria-label="Fechar janela">&times;</button>
            </div>

            <div class="otp-contingency-banner is-info">
                <strong>Autenticação Google Assistida Ativa:</strong> seu acesso será liberado imediatamente com e-mail verificado.
            </div>

            <div class="form-field">
                <label for="google-assisted-email">E-mail da conta Google</label>
                <input
                    id="google-assisted-email"
                    type="email"
                    autocomplete="email"
                    placeholder="seu.nome@gmail.com"
                    required
                >
                <small class="field-error" id="google-assisted-email-error" role="alert" hidden></small>
            </div>

            <div class="form-field">
                <label for="google-assisted-name">Nome completo de exibição</label>
                <input
                    id="google-assisted-name"
                    type="text"
                    autocomplete="name"
                    minlength="3"
                    maxlength="150"
                    placeholder="Seu nome completo"
                    required
                >
            </div>

            <div class="form-row-2col">
                <div class="form-field">
                    <label for="google-assisted-cpf">CPF <span class="field-optional" id="google-assisted-cpf-tag">(opcional no 1º acesso)</span></label>
                    <input
                        id="google-assisted-cpf"
                        type="text"
                        inputmode="numeric"
                        maxlength="14"
                        placeholder="000.000.000-00"
                    >
                    <small class="field-error" id="google-assisted-cpf-error" role="alert" hidden></small>
                </div>

                <div class="form-field">
                    <label for="google-assisted-phone">Telefone <span class="field-optional">(opcional)</span></label>
                    <input
                        id="google-assisted-phone"
                        type="tel"
                        inputmode="tel"
                        maxlength="20"
                        placeholder="(11) 98765-4321"
                    >
                    <small class="field-error" id="google-assisted-phone-error" role="alert" hidden></small>
                </div>
            </div>

            <p id="google-assisted-message" class="form-message" role="status" aria-live="polite"></p>

            <div class="dialog-actions">
                <button type="button" class="button-secondary" id="google-assisted-cancel">
                    Cancelar
                </button>
                <button type="submit" class="button-primary" id="google-assisted-submit">
                    Continuar com esta conta Google
                </button>
            </div>
        </form>
    `;
    document.body.append(dialog);

    const inputEmail = dialog.querySelector("#google-assisted-email");
    const errEmail = dialog.querySelector("#google-assisted-email-error");
    const inputNome = dialog.querySelector("#google-assisted-name");
    const inputCpf = dialog.querySelector("#google-assisted-cpf");
    const tagCpf = dialog.querySelector("#google-assisted-cpf-tag");
    const errCpf = dialog.querySelector("#google-assisted-cpf-error");
    const inputTel = dialog.querySelector("#google-assisted-phone");
    const errTel = dialog.querySelector("#google-assisted-phone-error");
    const msg = dialog.querySelector("#google-assisted-message");
    const btnClose = dialog.querySelector("#google-assisted-close");
    const btnCancel = dialog.querySelector("#google-assisted-cancel");
    const btnSubmit = dialog.querySelector("#google-assisted-submit");
    const form = dialog.querySelector("#google-assisted-form");

    if (inputEmail && emailPreenchido) inputEmail.value = emailPreenchido;
    if (inputNome && nomePreenchido) inputNome.value = nomePreenchido;
    if (inputCpf && cpfPreenchido) inputCpf.value = formatarMascaraCpf(cpfPreenchido);
    if (inputTel && telPreenchido) inputTel.value = formatarMascaraTelefone(telPreenchido);

    vincularValidacaoEmailTempoReal(inputEmail, errEmail);
    vincularValidacaoCpfTempoReal(inputCpf, null, errCpf);
    vincularValidacaoTelefoneTempoReal(inputTel, errTel, () => false);

    // Preenche sugestão amigável de nome a partir do e-mail caso o usuário esteja na tela de login
    inputEmail?.addEventListener("blur", () => {
        if (!inputNome.value.trim() && inputEmail.value.includes("@")) {
            const prefixo = inputEmail.value
                .split("@")[0]
                .replace(/[._-]+/g, " ")
                .trim();
            if (prefixo.length >= 3) {
                inputNome.value = prefixo.replace(/\b\w/g, (l) => l.toUpperCase());
            }
        }
    });

    const fechar = () => {
        if (typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }
    };
    btnClose?.addEventListener("click", fechar);
    btnCancel?.addEventListener("click", fechar);

    form?.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (msg) {
            msg.textContent = "";
            msg.className = "form-message";
        }

        const email = inputEmail.value.trim();
        if (!validarEmailFormato(email)) {
            const erroDom = detectarErroDominioEmail(email);
            const txtErro = erroDom
                ? erroDom.mensagem
                : "Informe um e-mail Google válido (ex.: nome@gmail.com).";
            if (msg) {
                msg.textContent = txtErro;
                msg.className = "form-message error";
            }
            inputEmail.focus();
            return;
        }

        let nome = inputNome.value.trim();
        if (nome.length < 3) {
            const derivado = email.split("@")[0].replace(/[._-]+/g, " ").trim();
            if (derivado.length >= 3) {
                nome = derivado.replace(/\b\w/g, (l) => l.toUpperCase());
                inputNome.value = nome;
            } else {
                if (msg) {
                    msg.textContent = "Informe seu nome completo (mínimo de 3 caracteres).";
                    msg.className = "form-message error";
                }
                inputNome.focus();
                return;
            }
        }

        let cpfDigitos = null;
        if (inputCpf.value.trim()) {
            const valCpf = validarCpfMatematico(inputCpf.value);
            if (!valCpf.valido) {
                if (errCpf) {
                    errCpf.textContent = valCpf.mensagem;
                    errCpf.hidden = false;
                }
                if (msg) {
                    msg.textContent = valCpf.mensagem;
                    msg.className = "form-message error";
                }
                inputCpf.focus();
                return;
            }
            cpfDigitos = valCpf.digitos;
        }

        const telTexto = inputTel.value.trim();
        if (telTexto) {
            const valTel = validarTelefoneBrasileiro(telTexto, { obrigatorio: false });
            if (!valTel.valido) {
                if (errTel) {
                    errTel.textContent = valTel.mensagem;
                    errTel.hidden = false;
                }
                if (msg) {
                    msg.textContent = valTel.mensagem;
                    msg.className = "form-message error";
                }
                inputTel.focus();
                return;
            }
        }

        if (btnSubmit) btnSubmit.disabled = true;
        if (msg) {
            msg.textContent = "Autenticando sua conta Google com aprovação automática...";
            msg.className = "form-message info";
        }

        try {
            api.clearToken();
            const dados = await api.post("/usuarios/auth/google/assistido", {
                email,
                nome_completo: nome,
                cpf: cpfDigitos,
                telefone: telTexto || null
            });
            fechar();
            await onAuthenticated(dados);
        } catch (erro) {
            const textoErro = erro.message || "Não foi possível autenticar com o Google.";
            if (textoErro.toLowerCase().includes("cpf") && tagCpf) {
                tagCpf.textContent = "(obrigatório para vincular conta existente)";
                inputCpf?.focus();
            }
            if (msg) {
                msg.textContent = textoErro;
                msg.className = "form-message error";
            }
        } finally {
            if (btnSubmit) btnSubmit.disabled = false;
        }
    });

    if (typeof dialog.showModal === "function") {
        dialog.showModal();
    } else {
        dialog.setAttribute("open", "open");
    }
    (emailPreenchido ? inputNome : inputEmail)?.focus();
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

    const concluirSessaoGoogle = async (dados) => {
        if (!dados || typeof dados.access_token !== "string" || !dados.access_token) {
            throw new Error("A API não retornou um token de sessão válido.");
        }
        api.setToken(dados.access_token);
        if (dados.usuario && dados.usuario.nome_completo) {
            sessionStorage.setItem("fluxo_caixa_nome_usuario", dados.usuario.nome_completo);
        }
        if (dados.precisa_completar_cadastro) {
            await abrirModalCompletarCadastroGoogle(dados.usuario?.nome_completo || "");
        }
        window.location.assign("index.html");
    };

    const processarPayloadGoogle = async (payloadAuth) => {
        if (!payloadAuth || (!payloadAuth.credential && !payloadAuth.access_token)) {
            exibirMensagem("Não foi possível obter a credencial do Google.", "error");
            return;
        }
        if (botaoFallback) botaoFallback.disabled = true;
        exibirMensagem("Validando autenticação segura com o Google...", "info");

        try {
            api.clearToken();
            const dados = await api.post("/usuarios/auth/google", payloadAuth);
            await concluirSessaoGoogle(dados);
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
    let modoAssistidoDisponivel = !clientId;

    if (!clientId && typeof api !== "undefined") {
        try {
            const cfg = await api.get("/usuarios/auth/google/config");
            if (cfg && typeof cfg.client_id === "string") {
                clientId = cfg.client_id.trim();
            }
            if (cfg && typeof cfg.modo_assistido === "boolean") {
                modoAssistidoDisponivel = cfg.modo_assistido;
            } else {
                modoAssistidoDisponivel = !clientId;
            }
        } catch {
            modoAssistidoDisponivel = true;
        }
    }

    let tokenClientOAuth2 = null;

    if (clientId) {
        try {
            await carregarScriptGoogleGsi();
            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: (response) => {
                    if (response?.credential) {
                        processarPayloadGoogle({ credential: response.credential });
                    }
                },
                ux_mode: "popup",
                auto_select: false
            });

            if (window.google.accounts.oauth2) {
                tokenClientOAuth2 = window.google.accounts.oauth2.initTokenClient({
                    client_id: clientId,
                    scope: "openid email profile",
                    callback: (tokenResponse) => {
                        if (tokenResponse && tokenResponse.access_token) {
                            processarPayloadGoogle({ access_token: tokenResponse.access_token });
                        } else if (tokenResponse && tokenResponse.error) {
                            exibirMensagem(
                                "Autenticação com o Google cancelada ou não autorizada.",
                                "error"
                            );
                        }
                    }
                });
            }

            if (containerGsi && !tokenClientOAuth2) {
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
            // Se o script externo do Google for bloqueado por rede/extensão, mantém o botão funcional
        }
    }

    if (botaoFallback) {
        botaoFallback.addEventListener("click", async () => {
            if (clientId) {
                try {
                    await carregarScriptGoogleGsi();
                    if (tokenClientOAuth2) {
                        tokenClientOAuth2.requestAccessToken({ prompt: "select_account" });
                        return;
                    }
                    if (window.google?.accounts?.oauth2) {
                        tokenClientOAuth2 = window.google.accounts.oauth2.initTokenClient({
                            client_id: clientId,
                            scope: "openid email profile",
                            callback: (tokenResponse) => {
                                if (tokenResponse?.access_token) {
                                    processarPayloadGoogle({ access_token: tokenResponse.access_token });
                                }
                            }
                        });
                        tokenClientOAuth2.requestAccessToken({ prompt: "select_account" });
                        return;
                    }
                    window.google.accounts.id.prompt();
                    return;
                } catch (erro) {
                    if (!modoAssistidoDisponivel) {
                        exibirMensagem(erro.message, "error");
                        return;
                    }
                }
            }

            if (modoAssistidoDisponivel) {
                abrirModalGoogleAssistido({ onAuthenticated: concluirSessaoGoogle });
                return;
            }

            exibirMensagem(
                "Configure a variável GOOGLE_CLIENT_ID no servidor para habilitar o Google OAuth 2.0.",
                "info"
            );
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
    formatarMascaraTelefone,
    validarTelefoneBrasileiro,
    vincularValidacaoTelefoneTempoReal,
    mascararEmailCliente,
    mascararTelefoneCliente,
    detectarErroDominioEmail,
    validarEmailFormato,
    vincularValidacaoEmailTempoReal,
    avaliarForcaSenha,
    obterMensagemErroSenha,
    vincularChecklistSenha,
    abrirDocumentoJuridico,
    inicializarBotaoGoogleOAuth
};
