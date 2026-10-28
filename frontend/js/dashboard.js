/*
 * FLUXO DE CAIXA
 * Inicialização, navegação SPA, gráficos Chart.js, metas, relatórios e exportação CSV.
 */

let todasContas = [];
let contasCarregadas = [];
let todasMovimentacoesCache = [];
let movimentacoesFiltradasCache = [];
let metasCarregadas = [];
let calculosCarregados = [];
let usuarioAtual = null;

// Instâncias ativas do Chart.js para destruição segura antes de recriar
const graficosAtivos = {
    dashboardEvolucao: null,
    dashboardCategoria: null,
    categoriasDistribuicao: null,
    investimentosEvolucao: null,
    relatoriosConsolidado: null
};

const NOMES_CATEGORIAS = {
    alimentacao: "Alimentação",
    moradia: "Moradia",
    salario: "Salário",
    transporte: "Transporte",
    saude: "Saúde",
    educacao: "Educação",
    lazer: "Lazer",
    investimento: "Investimento",
    contas: "Contas",
    compras: "Compras",
    impostos: "Impostos",
    freelance: "Freelance",
    vendas: "Vendas",
    transferencia: "Transferência",
    ajuste: "Ajuste",
    outros: "Outros"
};

const CORES_GRAFICOS = [
    "#16a34a",
    "#0ea5e9",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    "#f97316",
    "#6366f1",
    "#84cc16"
];

function obterSaudacaoUsuario(usuario = usuarioAtual) {
    const nome = (
        usuario?.nome_completo ||
        sessionStorage.getItem("fluxo_caixa_nome_usuario") ||
        ""
    ).trim();
    return nome ? `Olá, Sr(a). ${nome}` : "Olá, bem-vindo(a)";
}

const titulosViews = {
    dashboard: {
        eyebrow: "Olá, bem-vindo(a)",
        title: "Dashboard financeiro",
        subtitle: "Acompanhe suas finanças em um só lugar."
    },
    contas: {
        eyebrow: "GESTÃO",
        title: "Contas bancárias",
        subtitle: "Gerencie suas contas correntes, poupanças e investimentos."
    },
    movimentacoes: {
        eyebrow: "EXTRATO",
        title: "Movimentações financeiras",
        subtitle: "Histórico completo de entradas, saídas, transferências e ajustes."
    },
    categorias: {
        eyebrow: "CLASSIFICAÇÃO",
        title: "Categorias financeiras",
        subtitle: "Distribuição e controle de gastos e receitas por categoria."
    },
    investimentos: {
        eyebrow: "PATRIMÔNIO E METAS",
        title: "Investimentos e Metas",
        subtitle: "Acompanhe seus aportes, poupanças e objetivos financeiros."
    },
    relatorios: {
        eyebrow: "CONSOLIDAÇÃO",
        title: "Relatórios financeiros",
        subtitle: "Balanços por período customizado, histórico e exportação CSV."
    },
    configuracoes: {
        eyebrow: "PREFERÊNCIAS E CONTA",
        title: "Configurações do sistema",
        subtitle: "Personalize o tema, atualize seus dados cadastrais e gerencie a segurança da conta."
    }
};

/* =========================================================
   UTILITÁRIOS VISUAIS (TOAST, LOADING E FORMATAÇÃO)
========================================================= */

function mostrarToast(mensagem, tipo = "success") {
    const container = document.querySelector("#toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    toast.setAttribute("role", "status");

    const texto = document.createElement("span");
    texto.textContent = mensagem;
    toast.append(texto);

    container.append(toast);

    setTimeout(() => {
        toast.remove();
    }, 4200);
}

function definirCarregamentoGlobal(ativo) {
    const indicador = document.querySelector("#global-loading");
    if (indicador) {
        indicador.hidden = !ativo;
    }
}

function definirMensagem(seletor, texto, tipo) {
    const mensagem = document.querySelector(seletor);
    if (!mensagem) return;
    mensagem.textContent = texto;
    mensagem.className = `form-message ${tipo}`;
}

function limparMensagem(seletor) {
    const mensagem = document.querySelector(seletor);
    if (!mensagem) return;
    mensagem.textContent = "";
    mensagem.className = "form-message";
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function formatarData(valor) {
    if (!valor) return "—";
    const partes = String(valor).split("-");
    if (partes.length !== 3) return valor;
    const [ano, mes, dia] = partes;
    return `${dia}/${mes}/${ano}`;
}

function formatarIso(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
}

function formatarCategoria(slug) {
    if (!slug) return "Outros";
    const chave = String(slug).toLowerCase();
    return NOMES_CATEGORIAS[chave] || slug;
}

function criarElemento(tag, texto, classe) {
    const elemento = document.createElement(tag);
    elemento.textContent = texto;
    if (classe) elemento.className = classe;
    return elemento;
}

function definirTexto(seletor, texto) {
    const elemento = document.querySelector(seletor);
    if (elemento) elemento.textContent = texto;
}

function obterNomeConta(contaId) {
    const conta = todasContas.find((c) => c.id === Number(contaId));
    return conta ? conta.nome_banco : `Conta #${contaId}`;
}

/* =========================================================
   NAVEGAÇÃO SPA
========================================================= */

function configurarNavegacao() {
    const navLinks = document.querySelectorAll(".navigation .nav-link");

    function ativarSecao(hash) {
        let viewName = (hash || window.location.hash || "#dashboard")
            .replace("#", "")
            .trim()
            .toLowerCase();

        if (!titulosViews[viewName]) {
            viewName = "dashboard";
        }

        document.querySelectorAll(".app-view").forEach((view) => {
            view.hidden = view.id !== `view-${viewName}`;
        });

        navLinks.forEach((link) => {
            const linkTarget = (link.getAttribute("href") || "")
                .replace("#", "")
                .toLowerCase();
            const ativo = linkTarget === viewName;
            link.classList.toggle("active", ativo);
            if (ativo) {
                link.setAttribute("aria-current", "page");
            } else {
                link.removeAttribute("aria-current");
            }
        });

        const info = titulosViews[viewName] || titulosViews.dashboard;
        const textoSaudacao =
            viewName === "dashboard"
                ? obterSaudacaoUsuario(usuarioAtual)
                : info.eyebrow;
        definirTexto("#user-greeting", textoSaudacao);
        definirTexto("#view-title", info.title);
        definirTexto("#view-subtitle", info.subtitle);

        const metricasTopo = document.querySelector("#topbar-dashboard-metrics");
        if (metricasTopo) {
            metricasTopo.hidden = viewName !== "dashboard";
        }

        // Tarefa 1 e Tarefa 2: Visibilidade e ação contextual do botão principal no topo
        const botaoTopo = document.querySelector("#new-movement");
        if (botaoTopo) {
            if (viewName === "investimentos") {
                botaoTopo.hidden = false;
                botaoTopo.textContent = "+ Novo investimento";
                botaoTopo.dataset.action = "investment";
            } else if (
                viewName === "dashboard" ||
                viewName === "movimentacoes" ||
                viewName === "relatorios"
            ) {
                botaoTopo.hidden = false;
                botaoTopo.textContent = "+ Nova movimentação";
                botaoTopo.dataset.action = "movement";
            } else {
                // Oculto em Contas Bancárias (#view-contas), Categorias e Configurações
                botaoTopo.hidden = true;
            }
        }

        // Redimensiona gráficos ativos quando a aba se torna visível
        Object.values(graficosAtivos).forEach((grafico) => {
            if (grafico && typeof grafico.resize === "function") {
                grafico.resize();
            }
        });

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    navLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            const href = link.getAttribute("href");
            if (href && href.startsWith("#")) {
                event.preventDefault();
                history.pushState(null, "", href);
                ativarSecao(href);
            }
        });
    });

    window.addEventListener("hashchange", () => {
        ativarSecao(window.location.hash);
    });

    document.querySelectorAll("a[href^='#']:not(.nav-link)").forEach((link) => {
        link.addEventListener("click", (event) => {
            const href = link.getAttribute("href");
            if (href && titulosViews[href.replace("#", "")]) {
                event.preventDefault();
                history.pushState(null, "", href);
                ativarSecao(href);
            }
        });
    });

    ativarSecao(window.location.hash);
}

/* =========================================================
   INICIALIZAÇÃO E SESSÃO
========================================================= */

function verificarSessao() {
    if (!api.getToken()) {
        window.location.replace("login.html");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.addEventListener("pageshow", verificarSessao);
    if (!api.getToken()) return;

    atualizarData();
    inicializarDatasPadraoRelatorio();
    configurarNavegacao();
    configurarDialogos();
    configurarFiltrosEExportacao();
    configurarConfiguracoes();
    inicializarSelectsArredondados();
    configurarBotaoSair();
    carregarDashboard();
    inicializarOrcamentosAlertas();
});

function configurarBotaoSair() {
    const botao = document.querySelector("#logout");
    const dialogoSair = document.querySelector("#logout-confirm-dialog");
    const botaoConfirmarSair = document.querySelector("#logout-confirm-btn");
    if (!botao) return;

    const executarLogout = () => {
        api.clearToken();
        sessionStorage.removeItem("fluxo_caixa_nome_usuario");
        window.location.replace("login.html");
    };

    botao.addEventListener("click", () => {
        if (dialogoSair instanceof HTMLDialogElement) {
            dialogoSair.showModal();
        } else if (window.confirm("Deseja realmente sair da sua conta?")) {
            executarLogout();
        }
    });

    botaoConfirmarSair?.addEventListener("click", executarLogout);
}

function atualizarData() {
    const dateElement = document.querySelector("#current-date");
    if (!dateElement) return;

    dateElement.textContent = new Date().toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}

function inicializarDatasPadraoRelatorio() {
    const hoje = new Date();
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const inputInicio = document.querySelector("#report-start-date");
    const inputFim = document.querySelector("#report-end-date");

    if (inputInicio && !inputInicio.value) {
        inputInicio.value = formatarIso(inicioMes);
    }
    if (inputFim && !inputFim.value) {
        inputFim.value = formatarIso(hoje);
    }
}

/* =========================================================
   MODAIS E FORMULÁRIOS (CONTAS, MOVIMENTAÇÕES E METAS)
========================================================= */

function aplicarScrollLock(ativo) {
    if (ativo) {
        document.body.classList.add("modal-open");
    } else {
        const abertos = document.querySelectorAll("dialog[open]");
        if (abertos.length === 0) {
            document.body.classList.remove("modal-open");
        }
    }
}

// Interceptador global para garantir scroll lock em todos os modais (<dialog>)
if (typeof HTMLDialogElement !== "undefined" && !HTMLDialogElement.prototype.__scrollLockHooked) {
    HTMLDialogElement.prototype.__scrollLockHooked = true;
    const showModalOriginal = HTMLDialogElement.prototype.showModal;
    HTMLDialogElement.prototype.showModal = function(...args) {
        document.body.classList.add("modal-open");
        return showModalOriginal.apply(this, args);
    };
    const closeOriginal = HTMLDialogElement.prototype.close;
    HTMLDialogElement.prototype.close = function(...args) {
        const res = closeOriginal.apply(this, args);
        setTimeout(() => {
            const abertos = document.querySelectorAll("dialog[open]");
            if (abertos.length === 0) {
                document.body.classList.remove("modal-open");
            }
        }, 0);
        return res;
    };
}

function configurarDialogos() {
    const formularioConta = document.querySelector("#account-form");
    const formularioMovimentacao = document.querySelector("#movement-form");
    const formularioInvestimento = document.querySelector("#investment-form");
    const formularioMeta = document.querySelector("#goal-form");
    const seletorTipoMovimento = document.querySelector("#movement-type");
    const botaoTopo = document.querySelector("#new-movement");

    document.querySelectorAll(".btn-abrir-nova-conta, #new-account").forEach((botao) => {
        botao.addEventListener("click", () => abrirDialogoConta());
    });
    document.querySelectorAll(".btn-abrir-nova-movimentacao").forEach((botao) => {
        botao.addEventListener("click", abrirDialogoMovimentacao);
    });
    botaoTopo?.addEventListener("click", () => {
        if (botaoTopo.dataset.action === "investment") {
            abrirDialogoInvestimento();
        } else {
            abrirDialogoMovimentacao();
        }
    });
    document.querySelectorAll(".btn-abrir-novo-investimento, #new-investment-btn").forEach((botao) => {
        botao.addEventListener("click", abrirDialogoInvestimento);
    });
    document.querySelector("#new-goal")?.addEventListener("click", () => abrirDialogoMeta());

    // Abas de classificação: Conta Fixa vs Conta Variável
    const botoesNatureza = document.querySelectorAll(".nature-tab");
    const inputNatureza = document.querySelector("#movement-nature");
    botoesNatureza.forEach((aba) => {
        aba.addEventListener("click", () => {
            const valor = aba.getAttribute("data-nature-value") || "fixa";
            if (inputNatureza) inputNatureza.value = valor;
            botoesNatureza.forEach((outra) => {
                const ativa = outra === aba;
                outra.classList.toggle("active", ativa);
                outra.setAttribute("aria-checked", String(ativa));
            });
            atualizarCamposTipoMovimentacao();
        });
    });

    document.querySelectorAll("[data-close-dialog]").forEach((botao) => {
        botao.addEventListener("click", () => {
            const dialogo = document.querySelector(`#${botao.dataset.closeDialog}`);
            if (dialogo instanceof HTMLDialogElement) dialogo.close();
        });
    });

    seletorTipoMovimento?.addEventListener("change", atualizarCamposTipoMovimentacao);

    const inputDiaRepeticao = document.querySelector("#movement-repeat-day");
    inputDiaRepeticao?.addEventListener("input", atualizarAjudaDiaRepeticao);
    inputDiaRepeticao?.addEventListener("change", atualizarAjudaDiaRepeticao);

    formularioConta?.addEventListener("submit", salvarConta);
    formularioMovimentacao?.addEventListener("submit", salvarMovimentacao);
    formularioInvestimento?.addEventListener("submit", salvarInvestimento);
    formularioMeta?.addEventListener("submit", salvarMeta);

    document.querySelector("#account-dialog")?.addEventListener("close", () => {
        limparMensagem("#account-message");
        aplicarScrollLock(false);
    });
    document.querySelector("#movement-dialog")?.addEventListener("close", () => {
        limparMensagem("#movement-message");
        aplicarScrollLock(false);
    });
    document.querySelector("#investment-dialog")?.addEventListener("close", () => {
        limparMensagem("#investment-message");
        aplicarScrollLock(false);
    });
    document.querySelector("#goal-dialog")?.addEventListener("close", () => {
        limparMensagem("#goal-message");
        aplicarScrollLock(false);
    });
}

const OPCOES_CATEGORIA_ENTRADA_FIXA = [
    { value: "salario", label: "Salário (Ganhos Fixos)" },
    { value: "outros", label: "Outros ganhos fixos" }
];

const OPCOES_CATEGORIA_ENTRADA_VARIAVEL = [
    { value: "pix", label: "Pix recebido" },
    { value: "venda_objeto", label: "Venda de objeto" },
    { value: "freela", label: "Freela / Serviço extra" },
    { value: "ganhos_variaveis", label: "Outros ganhos variáveis" }
];

const OPCOES_CATEGORIA_SAIDA = [
    { value: "contas", label: "Contas (água, luz, internet)" },
    { value: "moradia", label: "Moradia (aluguel, condomínio)" },
    { value: "alimentacao", label: "Alimentação" },
    { value: "transporte", label: "Transporte" },
    { value: "saude", label: "Saúde" },
    { value: "educacao", label: "Educação" },
    { value: "lazer", label: "Lazer" },
    { value: "compras", label: "Compras" },
    { value: "impostos", label: "Impostos" },
    { value: "investimento", label: "Investimento" },
    { value: "salario", label: "Salário" },
    { value: "freelance", label: "Freelance" },
    { value: "vendas", label: "Vendas" },
    { value: "outros", label: "Outros" }
];

function popularSelectOpcoesMovimentacao(selectEl, listaOpcoes) {
    if (!selectEl) return;
    const valorAnterior = selectEl.value;
    selectEl.replaceChildren();
    listaOpcoes.forEach((item) => {
        const opt = document.createElement("option");
        opt.value = item.value;
        opt.textContent = item.label;
        selectEl.append(opt);
    });
    const existeAnterior = listaOpcoes.some((item) => item.value === valorAnterior);
    selectEl.value = existeAnterior ? valorAnterior : listaOpcoes[0]?.value || "";
}

function atualizarAjudaDiaRepeticao() {
    const input = document.querySelector("#movement-repeat-day");
    const help = document.querySelector("#movement-repeat-day-help");
    const tipo = document.querySelector("#movement-type")?.value || "entrada";
    if (!input || !help) return;
    const dia = parseInt(input.value, 10);
    const termo = tipo === "entrada" ? "este ganho fixo" : "esta conta fixa";
    if (isNaN(dia) || dia < 1 || dia > 31) {
        help.textContent = `Dia do mês (1 a 31) em que ${termo} se repetirá automaticamente.`;
        return;
    }
    const hoje = new Date();
    const diaAtual = hoje.getDate();
    const meses = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ];
    if (dia < diaAtual) {
        const prox = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 1);
        const mesNome = meses[prox.getMonth()];
        const ano = prox.getFullYear();
        help.textContent = `Como o dia ${dia} já passou no mês atual (hoje é dia ${diaAtual}), a recorrência iniciará no próximo mês em ${dia} de ${mesNome} de ${ano}.`;
    } else {
        const mesNome = meses[hoje.getMonth()];
        const ano = hoje.getFullYear();
        help.textContent = `Como o dia ${dia} é hoje ou posterior (hoje é dia ${diaAtual}), a movimentação será processada neste mês em ${dia} de ${mesNome} de ${ano} e repetirá nos meses seguintes.`;
    }
}

function atualizarCamposTipoMovimentacao() {
    const tipo = document.querySelector("#movement-type")?.value || "entrada";
    const natureza = document.querySelector("#movement-nature")?.value || "fixa";
    const campoDestino = document.querySelector("#movement-destination-field");
    const grupoClassificacao = document.querySelector("#movement-expense-classification-group");
    const labelNatureza = document.querySelector("#movement-nature-label");
    const abaFixa = document.querySelector("#nature-tab-fixa");
    const abaVariavel = document.querySelector("#nature-tab-variavel");
    const campoDiaRepeticao = document.querySelector("#movement-repeat-day-field");
    const inputDiaRepeticao = document.querySelector("#movement-repeat-day");
    const helpDiaRepeticao = document.querySelector("#movement-repeat-day-help");
    const labelCategoria = document.querySelector("#movement-category-label");
    const selectCategoria = document.querySelector("#movement-category");
    const inputValor = document.querySelector("#movement-amount");

    const ehEntrada = tipo === "entrada";
    const ehSaida = tipo === "saida";
    const ehInvestimento = tipo === "investimento";
    const possuiClassificacao = ehEntrada || ehSaida;
    const ehFixa = possuiClassificacao && natureza === "fixa";

    if (campoDestino) {
        campoDestino.hidden = tipo !== "transferencia";
    }

    // O grupo de classificação (fixa/variável) aparece apenas para Entrada e Saída
    if (grupoClassificacao) {
        grupoClassificacao.hidden = !possuiClassificacao;
    }

    // Os campos de tipo de ativo de investimento aparecem apenas para Investimento
    const campoInvestimento = document.querySelector("#movement-investment-fields");
    if (campoInvestimento) {
        campoInvestimento.hidden = !ehInvestimento;
    }

    if (ehEntrada) {
        if (labelNatureza) labelNatureza.textContent = "Classificação da entrada";
        if (abaFixa) abaFixa.textContent = "Ganhos Fixos";
        if (abaVariavel) abaVariavel.textContent = "Ganhos Variáveis";
        if (labelCategoria) {
            labelCategoria.textContent =
                natureza === "fixa"
                    ? "Origem do ganho fixo"
                    : "Origem do ganho variável";
        }
        if (helpDiaRepeticao) {
            helpDiaRepeticao.textContent =
                "Dia do mês (1 a 31) em que este ganho fixo se repetirá automaticamente.";
        }
        popularSelectOpcoesMovimentacao(
            selectCategoria,
            natureza === "fixa"
                ? OPCOES_CATEGORIA_ENTRADA_FIXA
                : OPCOES_CATEGORIA_ENTRADA_VARIAVEL
        );
    } else if (ehSaida) {
        if (labelNatureza) labelNatureza.textContent = "Classificação da conta";
        if (abaFixa) abaFixa.textContent = "Conta Fixa";
        if (abaVariavel) abaVariavel.textContent = "Conta Variável";
        if (labelCategoria) labelCategoria.textContent = "Categoria";
        if (helpDiaRepeticao) {
            helpDiaRepeticao.textContent =
                "Dia do mês (1 a 31) em que esta conta fixa se repetirá automaticamente.";
        }
        popularSelectOpcoesMovimentacao(selectCategoria, OPCOES_CATEGORIA_SAIDA);
    }

    if (campoDiaRepeticao) {
        campoDiaRepeticao.hidden = !ehFixa;
    }

    if (inputDiaRepeticao) {
        inputDiaRepeticao.required = ehFixa;
        if (ehFixa && !inputDiaRepeticao.value) {
            inputDiaRepeticao.value = String(new Date().getDate());
        }
    }

    if (inputValor) {
        inputValor.setAttribute("min", "0.01");
    }

    const labelConta = document.querySelector("#movement-account-label");
    const btnSubmit = document.querySelector("#movement-form button[type='submit']");
    if (ehInvestimento) {
        if (labelConta) labelConta.textContent = "Conta bancária para débito do aporte";
        if (btnSubmit) btnSubmit.textContent = "Registrar investimento";
    } else {
        if (labelConta) labelConta.textContent = tipo === "transferencia" ? "Conta de origem" : "Conta bancária";
        if (btnSubmit) btnSubmit.textContent = "Salvar movimentação";
    }

    if (ehFixa) {
        atualizarAjudaDiaRepeticao();
    }
}

function abrirDialogoConta(contaParaEditar = null) {
    const dialogo = document.querySelector("#account-dialog");
    const inputId = document.querySelector("#account-edit-id");
    const inputNome = document.querySelector("#account-name");
    const selectTipo = document.querySelector("#account-type");
    const campoSaldo = document.querySelector("#account-balance-field");
    const inputSaldo = document.querySelector("#account-balance");
    const campoAtiva = document.querySelector("#account-active-field");
    const selectAtiva = document.querySelector("#account-active");

    if (contaParaEditar) {
        definirTexto("#account-dialog-title", "Editar conta bancária");
        definirTexto("#account-dialog-subtitle", "Atualize o nome, tipo ou status da conta.");
        if (inputId) inputId.value = String(contaParaEditar.id);
        if (inputNome) inputNome.value = contaParaEditar.nome_banco;
        if (selectTipo) selectTipo.value = contaParaEditar.tipo_conta;
        if (campoSaldo) campoSaldo.hidden = true;
        if (campoAtiva) campoAtiva.hidden = false;
        if (selectAtiva) selectAtiva.value = String(Boolean(contaParaEditar.ativa));
    } else {
        definirTexto("#account-dialog-title", "Cadastrar conta bancária");
        definirTexto("#account-dialog-subtitle", "Adicione uma conta para organizar seu saldo e movimentações.");
        document.querySelector("#account-form")?.reset();
        if (inputId) inputId.value = "";
        if (inputSaldo) inputSaldo.value = "0.00";
        if (campoSaldo) campoSaldo.hidden = false;
        if (campoAtiva) campoAtiva.hidden = true;
    }

    if (dialogo instanceof HTMLDialogElement) {
        aplicarScrollLock(true);
        dialogo.showModal();
    }
}

function abrirDialogoMovimentacao() {
    if (contasCarregadas.length === 0) {
        abrirDialogoConta();
        definirMensagem(
            "#account-message",
            "Cadastre uma conta ativa antes de registrar movimentações.",
            "info"
        );
        return;
    }

    const seletor = document.querySelector("#movement-account");
    const seletorDestino = document.querySelector("#movement-destination-account");
    const ajuda = document.querySelector("#movement-account-help");

    if (seletor) {
        seletor.replaceChildren();
        contasCarregadas.forEach((conta) => {
            const opcao = document.createElement("option");
            opcao.value = String(conta.id);
            opcao.textContent = `${conta.nome_banco} (${conta.tipo_conta}) — ${formatarMoeda(conta.valor_conta_atual)}`;
            seletor.append(opcao);
        });
    }

    if (seletorDestino) {
        seletorDestino.replaceChildren();
        contasCarregadas.forEach((conta) => {
            const opcao = document.createElement("option");
            opcao.value = String(conta.id);
            opcao.textContent = `${conta.nome_banco} (${conta.tipo_conta})`;
            seletorDestino.append(opcao);
        });
        if (contasCarregadas.length > 1) {
            seletorDestino.value = String(contasCarregadas[1].id);
        }
    }

    const atualizarAjudaConta = () => {
        if (!seletor) return;
        const idSelecionado = Number(seletor.value);
        const conta = contasCarregadas.find((c) => c.id === idSelecionado);
        if (ajuda && conta) {
            ajuda.textContent = `Saldo atual: ${formatarMoeda(conta.valor_conta_atual)} (${conta.tipo_conta})`;
        }
    };

    if (seletor) {
        seletor.onchange = atualizarAjudaConta;
        atualizarAjudaConta();
    }

    const inputData = document.querySelector("#movement-date");
    if (inputData && !inputData.value) {
        inputData.value = formatarIso(new Date());
    }

    atualizarCamposTipoMovimentacao();

    const dialogo = document.querySelector("#movement-dialog");
    if (dialogo instanceof HTMLDialogElement) {
        aplicarScrollLock(true);
        dialogo.showModal();
    }
}

function abrirDialogoInvestimento() {
    if (contasCarregadas.length === 0) {
        abrirDialogoConta();
        definirMensagem(
            "#account-message",
            "Cadastre uma conta bancária ativa antes de registrar um investimento.",
            "info"
        );
        return;
    }

    const seletorConta = document.querySelector("#investment-account");
    const ajudaConta = document.querySelector("#investment-account-help");

    if (seletorConta) {
        seletorConta.replaceChildren();
        contasCarregadas.forEach((conta) => {
            const opcao = document.createElement("option");
            opcao.value = String(conta.id);
            opcao.textContent = `${conta.nome_banco} (${conta.tipo_conta}) — ${formatarMoeda(conta.valor_conta_atual)}`;
            seletorConta.append(opcao);
        });
    }

    const atualizarAjudaInvestimento = () => {
        if (!seletorConta) return;
        const idSelecionado = Number(seletorConta.value);
        const conta = contasCarregadas.find((c) => c.id === idSelecionado);
        if (ajudaConta && conta) {
            ajudaConta.textContent = `Saldo disponível para débito: ${formatarMoeda(conta.valor_conta_atual)} (${conta.tipo_conta})`;
        }
    };

    if (seletorConta) {
        seletorConta.onchange = atualizarAjudaInvestimento;
        atualizarAjudaInvestimento();
    }

    const dialogo = document.querySelector("#investment-dialog");
    if (dialogo instanceof HTMLDialogElement) {
        aplicarScrollLock(true);
        dialogo.showModal();
    }
}

function abrirDialogoMeta(metaParaEditar = null) {
    const dialogo = document.querySelector("#goal-dialog");
    const form = document.querySelector("#goal-form");
    const inputId = document.querySelector("#goal-edit-id");
    const inputNome = document.querySelector("#goal-name");
    const inputValorMeta = document.querySelector("#goal-target-amount");
    const inputValorAtual = document.querySelector("#goal-current-amount");
    const inputInicio = document.querySelector("#goal-start-date");
    const inputLimite = document.querySelector("#goal-deadline-date");
    const selectStatus = document.querySelector("#goal-status");
    const inputDescricao = document.querySelector("#goal-description");

    if (metaParaEditar) {
        definirTexto("#goal-dialog-title", "Atualizar meta financeira");
        if (inputId) inputId.value = String(metaParaEditar.id);
        if (inputNome) inputNome.value = metaParaEditar.nome;
        if (inputValorMeta) inputValorMeta.value = metaParaEditar.valor_meta;
        if (inputValorAtual) inputValorAtual.value = metaParaEditar.valor_atual;
        if (inputInicio) inputInicio.value = metaParaEditar.data_inicio;
        if (inputLimite) inputLimite.value = metaParaEditar.data_limite || "";
        if (selectStatus) selectStatus.value = metaParaEditar.status;
        if (inputDescricao) inputDescricao.value = metaParaEditar.descricao || "";
    } else {
        definirTexto("#goal-dialog-title", "Nova meta financeira");
        form?.reset();
        if (inputId) inputId.value = "";
        if (inputValorAtual) inputValorAtual.value = "0.00";
        if (inputInicio) inputInicio.value = formatarIso(new Date());
    }

    if (dialogo instanceof HTMLDialogElement) {
        aplicarScrollLock(true);
        dialogo.showModal();
    }
}

async function salvarConta(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);
    const contaId = (dados.get("conta_id") || "").toString().trim();

    definirMensagem("#account-message", "Salvando conta...", "info");
    botao.disabled = true;

    try {
        if (contaId) {
            await api.put(`/contas-bancarias/${contaId}`, {
                nome_banco: dados.get("nome_banco").toString().trim(),
                tipo_conta: dados.get("tipo_conta"),
                ativa: dados.get("ativa") !== "false"
            });
            mostrarToast("Conta bancária atualizada com sucesso!");
        } else {
            await api.post("/contas-bancarias/", {
                nome_banco: dados.get("nome_banco").toString().trim(),
                tipo_conta: dados.get("tipo_conta"),
                valor_conta_atual: dados.get("valor_conta_atual"),
                ativa: true
            });
            mostrarToast("Conta bancária cadastrada! Enviamos uma confirmação para o seu e-mail.");
        }

        formulario.reset();
        document.querySelector("#account-balance").value = "0.00";
        document.querySelector("#account-dialog").close();
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#account-message", error.message, "error");
        mostrarToast(error.message, "error");
    } finally {
        botao.disabled = false;
    }
}

async function excluirConta(conta) {
    if (!window.confirm(`Deseja realmente excluir a conta "${conta.nome_banco}"?`)) {
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        await api.delete(`/contas-bancarias/${conta.id}`);
        mostrarToast("Conta bancária excluída com sucesso!");
        await carregarDashboard();
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

async function salvarMovimentacao(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);
    const tipo = (dados.get("tipo") || "entrada").toString();
    const naturezaConta = (dados.get("natureza_conta") || "fixa").toString();
    const categoriaSelecionada = (dados.get("categoria") || "").toString().trim();
    const diaRepeticaoRaw = (dados.get("dia_repeticao") || "").toString().trim();
    const observacao = (dados.get("observacao") || "").toString().trim();

    const ehInvestimento = tipo === "investimento";
    const possuiClassificacao = tipo === "entrada" || tipo === "saida";

    if (possuiClassificacao && naturezaConta === "fixa") {
        const diaNum = Number(diaRepeticaoRaw);
        if (!Number.isInteger(diaNum) || diaNum < 1 || diaNum > 31) {
            definirMensagem(
                "#movement-message",
                "Informe o dia do mês (de 1 a 31) para repetição automática.",
                "error"
            );
            return;
        }
    }

    if (ehInvestimento) {
        const tipoInvestimento = (dados.get("tipo_investimento") || "").toString().trim();
        if (!tipoInvestimento) {
            definirMensagem(
                "#movement-message",
                "Selecione o tipo de ativo para o investimento.",
                "error"
            );
            return;
        }
    }

    definirMensagem("#movement-message", "Salvando movimentação...", "info");
    botao.disabled = true;

    const payload = {
        conta_bancaria_id: Number(dados.get("conta_bancaria_id")),
        valor: dados.get("valor"),
        tipo,
        observacao: observacao || null
    };

    if (ehInvestimento) {
        payload.tipo_investimento = (dados.get("tipo_investimento") || "").toString().trim();
        payload.categoria = "investimento";
    }

    if (possuiClassificacao) {
        payload.natureza_conta = naturezaConta;
        if (categoriaSelecionada) {
            payload.categoria = categoriaSelecionada;
        }
        if (naturezaConta === "fixa" && diaRepeticaoRaw) {
            payload.dia_repeticao = Number(diaRepeticaoRaw);
        }
        if (tipo === "entrada") {
            const descricoesEntrada = {
                salario: `Entrada - Salário (Ganhos Fixos${diaRepeticaoRaw ? ` · Dia ${diaRepeticaoRaw}` : ""})`,
                pix: "Entrada - Pix recebido (Ganhos Variáveis)",
                venda_objeto: "Entrada - Venda de objeto (Ganhos Variáveis)",
                freela: "Entrada - Freela (Ganhos Variáveis)",
                ganhos_variaveis: "Entrada - Outros ganhos variáveis (Ganhos Variáveis)"
            };
            if (descricoesEntrada[categoriaSelecionada]) {
                payload.descricao = descricoesEntrada[categoriaSelecionada];
            }
        }
    }

    if (tipo === "transferencia") {
        payload.conta_destino_id = Number(dados.get("conta_destino_id"));
    }

    try {
        await api.post("/fluxo-dinheiro/", payload);
        formulario.reset();
        const inputNatureza = document.querySelector("#movement-nature");
        if (inputNatureza) inputNatureza.value = "fixa";
        document.querySelectorAll(".nature-tab").forEach((aba) => {
            const fixa = aba.getAttribute("data-nature-value") === "fixa";
            aba.classList.toggle("active", fixa);
            aba.setAttribute("aria-checked", String(fixa));
        });
        atualizarCamposTipoMovimentacao();
        document.querySelector("#movement-dialog").close();
        mostrarToast(ehInvestimento ? `Investimento em ${payload.tipo_investimento} registrado com sucesso!` : "Movimentação registrada com sucesso!");
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#movement-message", error.message, "error");
        mostrarToast(error.message, "error");
    } finally {
        botao.disabled = false;
    }
}

async function salvarInvestimento(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);
    const tipoInvestimento = (dados.get("tipo_investimento") || "CDB").toString();
    const observacao = (dados.get("observacao") || "").toString().trim();

    definirMensagem("#investment-message", "Registrando investimento e debitando da conta...", "info");
    if (botao) botao.disabled = true;

    const payload = {
        conta_bancaria_id: Number(dados.get("conta_bancaria_id")),
        tipo: "investimento",
        tipo_investimento: tipoInvestimento,
        categoria: "investimento",
        valor: dados.get("valor"),
        observacao: observacao || null
    };

    try {
        await api.post("/fluxo-dinheiro/", payload);
        formulario.reset();
        document.querySelector("#investment-dialog")?.close();
        mostrarToast(`Investimento em ${tipoInvestimento} registrado com sucesso!`);
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#investment-message", error.message, "error");
        mostrarToast(error.message, "error");
    } finally {
        if (botao) botao.disabled = false;
    }
}

async function excluirMovimentacao(movimento) {
    if (!window.confirm(`Excluir a movimentação "${movimento.descricao}"?`)) {
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        await api.delete(`/fluxo-dinheiro/${movimento.id}`);
        mostrarToast("Movimentação excluída e saldo atualizado!");
        await carregarDashboard();
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

async function salvarMeta(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);
    const metaId = (dados.get("meta_id") || "").toString().trim();

    definirMensagem("#goal-message", "Salvando meta...", "info");
    botao.disabled = true;

    const payload = {
        nome: dados.get("nome").toString().trim(),
        valor_meta: dados.get("valor_meta"),
        valor_atual: dados.get("valor_atual") || "0.00",
        data_inicio: dados.get("data_inicio"),
        data_limite: dados.get("data_limite") || null,
        status: dados.get("status") || "em_andamento",
        descricao: dados.get("descricao")?.toString().trim() || null
    };

    try {
        if (metaId) {
            await api.put(`/metas-financeiras/${metaId}`, payload);
            mostrarToast("Meta financeira atualizada!");
        } else {
            await api.post("/metas-financeiras/", payload);
            mostrarToast("Meta financeira criada com sucesso!");
        }
        formulario.reset();
        document.querySelector("#goal-dialog").close();
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#goal-message", error.message, "error");
        mostrarToast(error.message, "error");
    } finally {
        botao.disabled = false;
    }
}

async function excluirMeta(meta) {
    if (!window.confirm(`Deseja excluir a meta "${meta.nome}"?`)) {
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        await api.delete(`/metas-financeiras/${meta.id}`);
        mostrarToast("Meta financeira excluída!");
        await carregarDashboard();
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

async function excluirCalculoSalvo(calculo) {
    if (!window.confirm("Deseja excluir este cálculo consolidado do histórico?")) {
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        await api.delete(`/calculos-financeiros/${calculo.id}`);
        mostrarToast("Cálculo excluído do histórico!");
        await carregarDashboard();
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

/* =========================================================
   BUSCA DE DADOS E ATUALIZAÇÃO DO DASHBOARD
========================================================= */

async function buscarTodasAsPaginas(path, parametros = {}) {
    const limit = 100;
    const resultados = [];
    let offset = 0;

    while (true) {
        const query = new URLSearchParams();
        Object.entries(parametros).forEach(([chave, valor]) => {
            if (valor !== undefined && valor !== null && valor !== "") {
                query.set(chave, String(valor));
            }
        });
        query.set("limit", String(limit));
        query.set("offset", String(offset));

        const pagina = await api.get(`${path}?${query.toString()}`);
        if (!Array.isArray(pagina)) {
            throw new Error("A API retornou uma lista em formato inesperado.");
        }

        resultados.push(...pagina);
        if (pagina.length < limit) return resultados;
        offset += limit;
    }
}

async function carregarDashboard() {
    if (document.querySelector("#orcamento-mes")?.value) atualizarOrcamentosAlertas();
    const statusElement = document.querySelector(".status-text");
    const statusDot = document.querySelector(".status-dot");
    const ids = [
        "#total-balance",
        "#total-income",
        "#total-expenses",
        "#monthly-result"
    ];

    ids.forEach((id) => {
        const elemento = document.querySelector(id);
        if (elemento) elemento.textContent = "Carregando...";
    });

    definirCarregamentoGlobal(true);

    try {
        const hoje = new Date();
        const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);

        const [
            perfilUsuario,
            contas,
            movimentacoesMes,
            movimentacoesRecentes,
            movimentacoesTodas,
            metas,
            calculos
        ] = await Promise.all([
            api.get("/usuarios/me").catch(() => null),
            buscarTodasAsPaginas("/contas-bancarias/"),
            buscarTodasAsPaginas("/fluxo-dinheiro/", {
                data_inicio: formatarIso(inicioMes),
                data_fim: formatarIso(hoje)
            }),
            api.get("/fluxo-dinheiro/?limit=10&offset=0"),
            buscarTodasAsPaginas("/fluxo-dinheiro/"),
            buscarTodasAsPaginas("/metas-financeiras/").catch(() => []),
            buscarTodasAsPaginas("/calculos-financeiros/").catch(() => [])
        ]);

        if (!Array.isArray(movimentacoesRecentes)) {
            throw new Error("A API retornou movimentações em formato inesperado.");
        }

        usuarioAtual = perfilUsuario;
        todasContas = contas;
        contasCarregadas = contas.filter((conta) => conta.ativa);
        todasMovimentacoesCache = movimentacoesTodas;
        movimentacoesFiltradasCache = movimentacoesTodas;
        metasCarregadas = metas;
        calculosCarregados = calculos;

        atualizarPerfilUsuario(usuarioAtual);
        popularSeletoresContas(todasContas);
        atualizarResumo(contas, movimentacoesMes);
        atualizarContas(contas);
        atualizarMovimentacoes(movimentacoesRecentes, movimentacoesFiltradasCache);
        atualizarMetas(metasCarregadas);
        atualizarEstatisticaCategorias(movimentacoesTodas);
        atualizarGraficosDashboard(contas, movimentacoesMes, movimentacoesTodas, metasCarregadas);
        atualizarRelatorioPeriodoLocal(
            formatarIso(inicioMes),
            formatarIso(hoje),
            ""
        );
        renderizarHistoricoCalculos(calculosCarregados);
        atualizarStatus("Conectado", true);
    } catch (error) {
        if (!api.getToken()) {
            window.location.replace("login.html");
            return;
        }

        ids.forEach((id) => {
            const elemento = document.querySelector(id);
            if (elemento) elemento.textContent = "—";
        });
        atualizarEstadoVazio(
            "#accounts-list",
            "Não foi possível carregar as contas.",
            error.message
        );
        atualizarTabelaVazia(
            "#transactions-list",
            "Não foi possível carregar as movimentações.",
            5
        );
        atualizarStatus(error.message, false);
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }

    function atualizarStatus(texto, conectado) {
        if (statusElement) statusElement.textContent = texto;
        if (statusDot) {
            statusDot.style.backgroundColor = conectado ? "#16a34a" : "#dc2626";
        }
    }
}

function atualizarPerfilUsuario(usuario) {
    if (!usuario) return;

    const nomeUsuario = (usuario.nome_completo || "").trim();
    if (nomeUsuario) {
        sessionStorage.setItem("fluxo_caixa_nome_usuario", nomeUsuario);
    }

    const saudacao = obterSaudacaoUsuario(usuario);
    titulosViews.dashboard.eyebrow = saudacao;

    const greetingElement = document.getElementById("user-greeting");
    const hashAtual = (window.location.hash || "#dashboard")
        .replace("#", "")
        .trim()
        .toLowerCase();
    if (greetingElement && (!hashAtual || hashAtual === "dashboard" || !titulosViews[hashAtual])) {
        greetingElement.textContent = saudacao;
    }

    const badge = document.querySelector("#user-profile-badge");
    if (badge) {
        badge.hidden = false;
    }
    const iniciais = (nomeUsuario || "U")
        .split(/\s+/)
        .slice(0, 2)
        .map((parte) => parte[0]?.toUpperCase() || "")
        .join("");

    definirTexto("#user-avatar", iniciais || "U");
    definirTexto("#user-name", usuario.nome_completo);
    definirTexto("#user-email", usuario.email);

    const inputNome = document.querySelector("#settings-name");
    const inputEmail = document.querySelector("#settings-email");
    const inputTelefone = document.querySelector("#settings-phone");

    if (inputNome) inputNome.value = usuario.nome_completo || "";
    if (inputEmail) inputEmail.value = usuario.email || "";
    if (inputTelefone) inputTelefone.value = usuario.telefone || "";
}

function popularSeletoresContas(contas) {
    const seletorFiltro = document.querySelector("#filter-account");
    const seletorRelatorio = document.querySelector("#report-account");

    if (seletorFiltro) {
        const valorAtual = seletorFiltro.value;
        seletorFiltro.replaceChildren(
            criarElemento("option", "Todas as contas")
        );
        seletorFiltro.firstChild.value = "";
        contas.forEach((conta) => {
            const opt = document.createElement("option");
            opt.value = String(conta.id);
            opt.textContent = `${conta.nome_banco} (${conta.tipo_conta})`;
            seletorFiltro.append(opt);
        });
        seletorFiltro.value = valorAtual;
    }

    if (seletorRelatorio) {
        const valorAtual = seletorRelatorio.value;
        seletorRelatorio.replaceChildren(
            criarElemento("option", "Todas as contas (Consolidado)")
        );
        seletorRelatorio.firstChild.value = "";
        contas.forEach((conta) => {
            const opt = document.createElement("option");
            opt.value = String(conta.id);
            opt.textContent = `${conta.nome_banco} (${conta.tipo_conta})`;
            seletorRelatorio.append(opt);
        });
        seletorRelatorio.value = valorAtual;
    }
}

function aplicarClasseCorIndicador(seletor, tipoOuValor) {
    const el = document.querySelector(seletor);
    if (!el) return;
    el.classList.remove("value-positive", "value-negative", "value-expense");
    if (tipoOuValor === "income") {
        el.classList.add("value-positive");
    } else if (tipoOuValor === "expense") {
        el.classList.add("value-expense");
    } else if (typeof tipoOuValor === "number") {
        if (tipoOuValor >= 0) {
            el.classList.add("value-positive");
        } else {
            el.classList.add("value-negative");
        }
    }
}

function atualizarResumo(contas, movimentacoes) {
    const saldo = contas.reduce(
        (total, conta) => total + Number(conta.valor_conta_atual),
        0
    );
    const receitas = movimentacoes.reduce(
        (total, movimento) =>
            movimento.tipo === "entrada"
                ? total + Number(movimento.valor)
                : total,
        0
    );
    const despesas = movimentacoes.reduce(
        (total, movimento) =>
            movimento.tipo === "saida"
                ? total + Number(movimento.valor)
                : total,
        0
    );
    const resultadoMes = receitas - despesas;

    definirTexto("#total-balance", formatarMoeda(saldo));
    definirTexto("#topbar-total-balance", formatarMoeda(saldo));
    definirTexto("#total-income", formatarMoeda(receitas));
    definirTexto("#total-expenses", formatarMoeda(despesas));
    definirTexto("#monthly-result", formatarMoeda(resultadoMes));

    aplicarClasseCorIndicador("#total-balance", saldo);
    aplicarClasseCorIndicador("#topbar-total-balance", saldo);
    aplicarClasseCorIndicador("#total-income", "income");
    aplicarClasseCorIndicador("#total-expenses", "expense");
    aplicarClasseCorIndicador("#monthly-result", resultadoMes);
}

function atualizarEstadoVazio(seletor, titulo, descricao) {
    const elemento = document.querySelector(seletor);
    if (!elemento) return;

    elemento.className = "empty-state";
    elemento.replaceChildren(
        criarElemento("p", titulo),
        criarElemento("span", descricao)
    );
}

function atualizarContas(contas) {
    const elemento = document.querySelector("#accounts-list");
    const elementoView = document.querySelector("#view-accounts-list");

    if (contas.length === 0) {
        if (elemento) {
            atualizarEstadoVazio(
                "#accounts-list",
                "Nenhuma conta cadastrada.",
                "As contas registradas na API aparecerão aqui."
            );
        }
        if (elementoView) {
            atualizarEstadoVazio(
                "#view-accounts-list",
                "Nenhuma conta cadastrada.",
                "Clique em '+ Nova conta' para cadastrar sua primeira conta."
            );
        }
        definirTexto("#investments-total", "R$ 0,00");
        definirTexto("#topbar-total-invested", "R$ 0,00");
        definirTexto("#dashboard-invested-indicator", "R$ 0,00");
        definirTexto("#savings-total", "R$ 0,00");
        return;
    }

    // Resumo compacto no Dashboard principal
    if (elemento) {
        elemento.replaceChildren();
        elemento.className = "accounts-list";

        contas.forEach((conta) => {
            const linha = document.createElement("div");
            linha.className = "account-summary";
            linha.append(
                criarElemento("strong", conta.nome_banco),
                criarElemento(
                    "span",
                    `${conta.tipo_conta} · ${formatarMoeda(conta.valor_conta_atual)}`
                )
            );
            elemento.append(linha);
        });
    }

    // Lista gerenciável na aba Contas Bancárias
    if (elementoView) {
        elementoView.replaceChildren();
        elementoView.className = "accounts-list";

        contas.forEach((conta) => {
            const linha = document.createElement("div");
            linha.className = "account-summary";
            linha.style.padding = "16px";
            linha.style.marginBottom = "8px";

            const info = document.createElement("div");
            const statusTexto = conta.ativa ? "Ativa" : "Inativa";
            info.append(
                criarElemento("strong", `${conta.nome_banco} (${conta.tipo_conta})`),
                document.createElement("br"),
                criarElemento(
                    "span",
                    `Saldo: ${formatarMoeda(conta.valor_conta_atual)} · Status: ${statusTexto}`
                )
            );

            const acoes = document.createElement("div");
            acoes.className = "account-actions";

            const btnEditar = criarElemento("button", "Editar", "button-small");
            btnEditar.type = "button";
            btnEditar.addEventListener("click", () => abrirDialogoConta(conta));

            const btnExcluir = criarElemento(
                "button",
                "Excluir",
                "button-small button-danger"
            );
            btnExcluir.type = "button";
            btnExcluir.addEventListener("click", () => excluirConta(conta));

            acoes.append(btnEditar, btnExcluir);
            linha.append(info, acoes);
            elementoView.append(linha);
        });
    }

    const totalContasInvestimento = contas
        .filter((c) => c.tipo_conta === "investimento")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);
    const totalAportesAtivos = todasMovimentacoesCache
        .filter((m) => m.categoria === "investimento" && m.tipo === "saida")
        .reduce((acc, m) => acc + Math.abs(Number(m.valor || 0)), 0);
    const totalInvestimentos = totalContasInvestimento + totalAportesAtivos;
    const totalPoupanca = contas
        .filter((c) => c.tipo_conta === "poupanca")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);

    definirTexto("#investments-total", formatarMoeda(totalInvestimentos));
    definirTexto("#topbar-total-invested", formatarMoeda(totalInvestimentos));
    definirTexto("#dashboard-invested-indicator", formatarMoeda(totalInvestimentos));
    definirTexto("#savings-total", formatarMoeda(totalPoupanca));
}

function atualizarMetas(metas) {
    const container = document.querySelector("#goals-list");
    const metasAtivas = metas.filter((m) => m.status === "em_andamento");
    const totalAcumuladoMetas = metas.reduce(
        (acc, m) => acc + Number(m.valor_atual || 0),
        0
    );

    definirTexto("#goals-active-count", String(metasAtivas.length));
    definirTexto("#goals-saved-total", formatarMoeda(totalAcumuladoMetas));

    if (!container) return;

    if (metas.length === 0) {
        atualizarEstadoVazio(
            "#goals-list",
            "Nenhuma meta financeira cadastrada.",
            "Clique em '+ Nova meta' para criar seu primeiro objetivo."
        );
        return;
    }

    container.replaceChildren();
    container.className = "goals-list";

    metas.forEach((meta) => {
        const card = document.createElement("div");
        card.className = "goal-card";

        const percentual = Math.min(
            100,
            Math.max(0, Number(meta.progresso_percentual || 0))
        );

        const header = document.createElement("div");
        header.className = "goal-header";

        const tituloBloco = document.createElement("div");
        tituloBloco.append(
            criarElemento("p", meta.nome, "goal-title"),
            criarElemento(
                "span",
                `${formatarMoeda(meta.valor_atual)} de ${formatarMoeda(meta.valor_meta)} (${Number(meta.progresso_percentual || 0).toFixed(1)}%)`,
                "goal-meta"
            )
        );

        const acoes = document.createElement("div");
        acoes.className = "account-actions";

        const btnEditar = criarElemento("button", "Atualizar", "button-small");
        btnEditar.type = "button";
        btnEditar.addEventListener("click", () => abrirDialogoMeta(meta));

        const btnExcluir = criarElemento(
            "button",
            "Excluir",
            "button-small button-danger"
        );
        btnExcluir.type = "button";
        btnExcluir.addEventListener("click", () => excluirMeta(meta));

        acoes.append(btnEditar, btnExcluir);
        header.append(tituloBloco, acoes);

        const barraExterna = document.createElement("div");
        barraExterna.className = "goal-progress-bar";
        const barraInterna = document.createElement("div");
        barraInterna.className = "goal-progress-fill";
        barraInterna.style.width = `${percentual}%`;
        barraExterna.append(barraInterna);

        const rodape = document.createElement("div");
        rodape.className = "goal-footer";
        const textoRestante =
            meta.status === "concluida"
                ? "Meta concluída!"
                : `Faltam ${formatarMoeda(meta.valor_restante)}`;
        const textoPrazo = meta.data_limite
            ? `Prazo: ${formatarData(meta.data_limite)}`
            : `Início: ${formatarData(meta.data_inicio)}`;

        rodape.append(
            criarElemento("span", textoRestante),
            criarElemento("span", textoPrazo)
        );

        card.append(header, barraExterna, rodape);
        container.append(card);
    });
}

function atualizarEstatisticaCategorias(movimentacoes) {
    const totaisPorCategoria = {};

    movimentacoes.forEach((mov) => {
        const cat = (mov.categoria || "outros").toLowerCase();
        if (!totaisPorCategoria[cat]) {
            totaisPorCategoria[cat] = { total: 0, quantidade: 0 };
        }
        totaisPorCategoria[cat].total += Math.abs(Number(mov.valor || 0));
        totaisPorCategoria[cat].quantidade += 1;
    });

    document.querySelectorAll("[data-category-total]").forEach((el) => {
        const slug = el.getAttribute("data-category-total");
        const dados = totaisPorCategoria[slug];
        if (dados && dados.quantidade > 0) {
            el.textContent = `${formatarMoeda(dados.total)} (${dados.quantidade} lanç.)`;
        } else {
            el.textContent = "Sem lançamentos";
        }
    });
}

function atualizarTabelaVazia(seletorTabela, mensagem, colunas = 5) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    const celula = criarElemento("td", mensagem, "table-empty");
    celula.colSpan = colunas;
    const linha = document.createElement("tr");
    linha.append(celula);
    tabela.replaceChildren(linha);
}

function obterRotuloCategoriaMovimento(movimento) {
    if (movimento.tipo === "investimento" || movimento.categoria === "investimento") {
        return movimento.tipo_investimento ? `Investimento · ${movimento.tipo_investimento}` : "Investimento";
    }
    const baseCat = formatarCategoria(movimento.categoria);
    if (movimento.tipo_investimento) {
        return `${baseCat} · ${movimento.tipo_investimento}`;
    }
    const ehEntrada = movimento.tipo === "entrada";
    if (movimento.natureza_conta === "fixa") {
        const rotuloFixo = ehEntrada ? "Ganhos Fixos" : "Conta Fixa";
        if (movimento.dia_repeticao) {
            return `${baseCat} · ${rotuloFixo} (Dia ${movimento.dia_repeticao})`;
        }
        return `${baseCat} · ${rotuloFixo}`;
    }
    if (movimento.natureza_conta === "variavel") {
        const rotuloVariavel = ehEntrada ? "Ganhos Variáveis" : "Conta Variável";
        return `${baseCat} · ${rotuloVariavel}`;
    }
    return baseCat;
}

function renderizarTabelaCompacta(seletorTabela, lista) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    if (!lista || lista.length === 0) {
        atualizarTabelaVazia(seletorTabela, "Nenhuma movimentação cadastrada.", 5);
        return;
    }

    const fragmento = document.createDocumentFragment();

    lista.forEach((movimento) => {
        const linha = document.createElement("tr");
        const celulaDesc = criarElemento("td", movimento.descricao);
        const celulaCat = criarElemento("td", obterRotuloCategoriaMovimento(movimento));
        const celulaData = criarElemento("td", formatarData(movimento.data_movimentacao));

        const celulaTipo = document.createElement("td");
        celulaTipo.append(
            criarElemento(
                "span",
                movimento.tipo,
                `badge-type badge-${movimento.tipo}`
            )
        );

        const classeValor =
            movimento.tipo === "entrada"
                ? "align-right transaction-income"
                : movimento.tipo === "saida"
                ? "align-right transaction-expense"
                : movimento.tipo === "investimento"
                ? "align-right transaction-investimento"
                : "align-right";
        const celulaValor = criarElemento(
            "td",
            formatarMoeda(movimento.valor),
            classeValor
        );

        linha.append(celulaDesc, celulaCat, celulaData, celulaTipo, celulaValor);
        fragmento.append(linha);
    });

    tabela.replaceChildren(fragmento);
}

function renderizarTabelaDetalhada(seletorTabela, lista) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    if (!lista || lista.length === 0) {
        atualizarTabelaVazia(seletorTabela, "Nenhuma movimentação encontrada para os filtros selecionados.", 7);
        return;
    }

    const fragmento = document.createDocumentFragment();

    lista.forEach((movimento) => {
        const linha = document.createElement("tr");
        const celulaDesc = criarElemento("td", movimento.descricao);
        const celulaConta = criarElemento("td", obterNomeConta(movimento.conta_bancaria_id));
        const celulaCat = criarElemento("td", obterRotuloCategoriaMovimento(movimento));
        const celulaData = criarElemento("td", formatarData(movimento.data_movimentacao));

        const celulaTipo = document.createElement("td");
        celulaTipo.append(
            criarElemento(
                "span",
                movimento.tipo,
                `badge-type badge-${movimento.tipo}`
            )
        );

        const classeValor =
            movimento.tipo === "entrada"
                ? "align-right transaction-income"
                : movimento.tipo === "saida"
                ? "align-right transaction-expense"
                : movimento.tipo === "investimento"
                ? "align-right transaction-investimento"
                : "align-right";
        const celulaValor = criarElemento(
            "td",
            formatarMoeda(movimento.valor),
            classeValor
        );

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "align-right";
        const btnExcluir = criarElemento(
            "button",
            "Excluir",
            "button-small button-danger"
        );
        btnExcluir.type = "button";
        btnExcluir.addEventListener("click", () => excluirMovimentacao(movimento));
        celulaAcoes.append(btnExcluir);

        linha.append(
            celulaDesc,
            celulaConta,
            celulaCat,
            celulaData,
            celulaTipo,
            celulaValor,
            celulaAcoes
        );
        fragmento.append(linha);
    });

    tabela.replaceChildren(fragmento);
}

function renderizarTabelaInvestimentos(seletorTabela, lista) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    const investimentos = (lista || []).filter(
        (m) => m.categoria === "investimento" || Boolean(m.tipo_investimento)
    );

    if (investimentos.length === 0) {
        atualizarTabelaVazia(
            seletorTabela,
            'Nenhum investimento registrado ainda. Clique em "+ Novo investimento" para aplicar.',
            6
        );
        return;
    }

    const fragmento = document.createDocumentFragment();

    investimentos.forEach((movimento) => {
        const linha = document.createElement("tr");
        const ativoNome = movimento.tipo_investimento || "Investimento";
        const celulaAtivo = criarElemento("td", ativoNome);
        const celulaConta = criarElemento("td", obterNomeConta(movimento.conta_bancaria_id));
        const celulaObs = criarElemento("td", movimento.descricao || "—");
        const celulaData = criarElemento("td", formatarData(movimento.data_movimentacao));
        const celulaValor = criarElemento(
            "td",
            formatarMoeda(movimento.valor),
            "align-right transaction-income"
        );

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "align-right";
        const btnExcluir = criarElemento(
            "button",
            "Excluir",
            "button-small button-danger"
        );
        btnExcluir.type = "button";
        btnExcluir.addEventListener("click", () => excluirMovimentacao(movimento));
        celulaAcoes.append(btnExcluir);

        linha.append(
            celulaAtivo,
            celulaConta,
            celulaObs,
            celulaData,
            celulaValor,
            celulaAcoes
        );
        fragmento.append(linha);
    });

    tabela.replaceChildren(fragmento);
}

function atualizarMovimentacoes(movimentacoesRecentes, todasMovimentacoes = null) {
    const baseCompleta = todasMovimentacoes || movimentacoesRecentes;
    renderizarTabelaCompacta("#transactions-list", movimentacoesRecentes);
    renderizarTabelaDetalhada("#view-transactions-list", baseCompleta);
    renderizarTabelaInvestimentos("#investments-assets-list", baseCompleta);
}

/* =========================================================
   TAREFA 2: GRÁFICOS REAIS COM CHART.JS
========================================================= */

function destruirGrafico(chave) {
    if (graficosAtivos[chave]) {
        graficosAtivos[chave].destroy();
        graficosAtivos[chave] = null;
    }
}

function alternarVisibilidadeGrafico(seletorContainer, seletorVazio, possuiDados) {
    const container = document.querySelector(seletorContainer);
    const vazio = document.querySelector(seletorVazio);
    if (container) container.hidden = !possuiDados;
    if (vazio) vazio.hidden = possuiDados;
}

function atualizarGraficosDashboard(contas, movimentacoesMes, todasMovimentacoes, metas) {
    if (typeof window.Chart === "undefined") {
        return;
    }

    const baseDashboard =
        movimentacoesMes.length > 0 ? movimentacoesMes : todasMovimentacoes;

    renderizarGraficosVisaoGeral(baseDashboard);
    renderizarGraficoCategorias(todasMovimentacoes);
    renderizarGraficoInvestimentos(contas, todasMovimentacoes, metas);
}

function renderizarGraficosVisaoGeral(movimentacoes) {
    const possuiDados = Array.isArray(movimentacoes) && movimentacoes.length > 0;
    alternarVisibilidadeGrafico(
        "#dashboard-charts-container",
        "#dashboard-chart-empty",
        possuiDados
    );

    destruirGrafico("dashboardEvolucao");
    destruirGrafico("dashboardCategoria");

    if (!possuiDados) return;

    // 1. Gráfico de Linha: Evolução diária de Receitas, Despesas e Saldo Acumulado
    const porData = {};
    movimentacoes.forEach((mov) => {
        const data = mov.data_movimentacao;
        if (!porData[data]) {
            porData[data] = { entradas: 0, saidas: 0, variacao: 0 };
        }
        const valor = Number(mov.valor || 0);
        if (mov.tipo === "entrada") {
            porData[data].entradas += valor;
            porData[data].variacao += valor;
        } else if (mov.tipo === "saida") {
            porData[data].saidas += valor;
            porData[data].variacao -= valor;
        } else if (mov.tipo === "ajuste") {
            porData[data].variacao += valor;
        }
    });

    const datasOrdenadas = Object.keys(porData).sort();
    let acumulado = 0;
    const labelsData = [];
    const serieSaldo = [];
    const serieEntradas = [];
    const serieSaidas = [];

    datasOrdenadas.forEach((dataIso) => {
        acumulado += porData[dataIso].variacao;
        labelsData.push(formatarData(dataIso));
        serieSaldo.push(Number(acumulado.toFixed(2)));
        serieEntradas.push(Number(porData[dataIso].entradas.toFixed(2)));
        serieSaidas.push(Number(porData[dataIso].saidas.toFixed(2)));
    });

    const canvasEvolucao = document.querySelector("#chart-dashboard-evolution");
    if (canvasEvolucao) {
        graficosAtivos.dashboardEvolucao = new window.Chart(canvasEvolucao, {
            type: "line",
            data: {
                labels: labelsData,
                datasets: [
                    {
                        label: "Saldo acumulado no período",
                        data: serieSaldo,
                        borderColor: "#0ea5e9",
                        backgroundColor: "rgba(14, 165, 233, 0.12)",
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2.5
                    },
                    {
                        label: "Receitas",
                        data: serieEntradas,
                        borderColor: "#16a34a",
                        backgroundColor: "#16a34a",
                        tension: 0.25,
                        borderWidth: 2
                    },
                    {
                        label: "Despesas",
                        data: serieSaidas,
                        borderColor: "#dc2626",
                        backgroundColor: "#dc2626",
                        tension: 0.25,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, font: { size: 11 } }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: (val) => formatarMoeda(val)
                        }
                    }
                }
            }
        });
    }

    // 2. Gráfico de Rosca: Despesas (ou movimentações) por Categoria
    const despesasPorCat = {};
    movimentacoes.forEach((mov) => {
        if (mov.tipo === "saida") {
            const cat = formatarCategoria(mov.categoria);
            despesasPorCat[cat] = (despesasPorCat[cat] || 0) + Number(mov.valor || 0);
        }
    });

    // Se não houver saídas ainda, exibe distribuição geral por categoria
    if (Object.keys(despesasPorCat).length === 0) {
        movimentacoes.forEach((mov) => {
            const cat = formatarCategoria(mov.categoria);
            despesasPorCat[cat] =
                (despesasPorCat[cat] || 0) + Math.abs(Number(mov.valor || 0));
        });
    }

    const categoriasLabels = Object.keys(despesasPorCat);
    const categoriasValores = categoriasLabels.map((c) =>
        Number(despesasPorCat[c].toFixed(2))
    );

    const canvasCategoria = document.querySelector("#chart-dashboard-category");
    if (canvasCategoria && categoriasLabels.length > 0) {
        graficosAtivos.dashboardCategoria = new window.Chart(canvasCategoria, {
            type: "doughnut",
            data: {
                labels: categoriasLabels,
                datasets: [
                    {
                        data: categoriasValores,
                        backgroundColor: CORES_GRAFICOS.slice(0, categoriasLabels.length),
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, font: { size: 11 } }
                    }
                }
            }
        });
    }
}

function renderizarGraficoCategorias(movimentacoes) {
    const possuiDados = Array.isArray(movimentacoes) && movimentacoes.length > 0;
    alternarVisibilidadeGrafico(
        "#categories-chart-container",
        "#categories-chart-empty",
        possuiDados
    );

    destruirGrafico("categoriasDistribuicao");
    if (!possuiDados) return;

    const mapa = {};
    movimentacoes.forEach((mov) => {
        const cat = formatarCategoria(mov.categoria);
        if (!mapa[cat]) {
            mapa[cat] = { receitas: 0, despesas: 0 };
        }
        const valor = Math.abs(Number(mov.valor || 0));
        if (mov.tipo === "entrada") {
            mapa[cat].receitas += valor;
        } else if (mov.tipo === "saida") {
            mapa[cat].despesas += valor;
        }
    });

    const labels = Object.keys(mapa);
    const receitas = labels.map((c) => Number(mapa[c].receitas.toFixed(2)));
    const despesas = labels.map((c) => Number(mapa[c].despesas.toFixed(2)));

    const canvas = document.querySelector("#chart-categories-distribution");
    if (canvas && labels.length > 0) {
        graficosAtivos.categoriasDistribuicao = new window.Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Receitas por categoria",
                        data: receitas,
                        backgroundColor: "#16a34a",
                        borderRadius: 6
                    },
                    {
                        label: "Despesas por categoria",
                        data: despesas,
                        backgroundColor: "#dc2626",
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: (v) => formatarMoeda(v) }
                    }
                }
            }
        });
    }
}

function renderizarGraficoInvestimentos(contas, movimentacoes, metas) {
    const investimentosAtivos = (movimentacoes || []).filter(
        (m) => m.categoria === "investimento" || Boolean(m.tipo_investimento)
    );
    const contasPatrimonio = contas.filter(
        (c) =>
            c.tipo_conta === "investimento" ||
            c.tipo_conta === "poupanca" ||
            Number(c.valor_conta_atual) > 0
    );
    const possuiDados =
        contasPatrimonio.length > 0 ||
        metas.length > 0 ||
        investimentosAtivos.length > 0;

    alternarVisibilidadeGrafico(
        "#investments-chart-container",
        "#investments-chart-empty",
        possuiDados
    );

    destruirGrafico("investimentosEvolucao");
    if (!possuiDados) return;

    const saldoCorrente = contas
        .filter((c) => c.tipo_conta === "corrente")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);
    const saldoPoupanca = contas
        .filter((c) => c.tipo_conta === "poupanca")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);
    const saldoInvestimento = contas
        .filter((c) => c.tipo_conta === "investimento")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);
    const acumuladoMetas = metas.reduce(
        (acc, m) => acc + Number(m.valor_atual || 0),
        0
    );

    const labels = [
        "Conta Corrente",
        "Reserva em Poupança",
        "Contas de Investimento",
        "Acumulado em Metas"
    ];
    const valores = [
        Number(saldoCorrente.toFixed(2)),
        Number(saldoPoupanca.toFixed(2)),
        Number(saldoInvestimento.toFixed(2)),
        Number(acumuladoMetas.toFixed(2))
    ];
    const cores = ["#0ea5e9", "#f59e0b", "#16a34a", "#14b8a6"];

    const porAtivo = {};
    investimentosAtivos.forEach((m) => {
        const chave = m.tipo_investimento || "Outros Investimentos";
        porAtivo[chave] = (porAtivo[chave] || 0) + Math.abs(Number(m.valor || 0));
    });
    Object.entries(porAtivo).forEach(([ativo, total], idx) => {
        labels.push(ativo);
        valores.push(Number(total.toFixed(2)));
        cores.push(CORES_GRAFICOS[(idx + 4) % CORES_GRAFICOS.length]);
    });

    const canvas = document.querySelector("#chart-investments-evolution");
    if (canvas) {
        graficosAtivos.investimentosEvolucao = new window.Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Composição Patrimonial e Ativos (R$)",
                        data: valores,
                        backgroundColor: cores,
                        borderRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: (v) => formatarMoeda(v) }
                    }
                }
            }
        });
    }
}

function renderizarGraficoRelatorioConsolidado(resumo) {
    const possuiDados =
        resumo &&
        (Number(resumo.total_entradas) > 0 ||
            Number(resumo.total_saidas) > 0 ||
            Number(resumo.saldo_inicial) !== 0 ||
            Number(resumo.saldo_final) !== 0);

    alternarVisibilidadeGrafico(
        "#reports-chart-container",
        "#reports-chart-empty",
        Boolean(possuiDados)
    );

    destruirGrafico("relatoriosConsolidado");
    if (!possuiDados || typeof window.Chart === "undefined") return;

    const canvas = document.querySelector("#chart-reports-consolidated");
    if (!canvas) return;

    graficosAtivos.relatoriosConsolidado = new window.Chart(canvas, {
        type: "bar",
        data: {
            labels: [
                "Saldo Inicial",
                "Entradas",
                "Saídas",
                "Investimentos",
                "Transf. Recebidas",
                "Transf. Enviadas",
                "Saldo Final"
            ],
            datasets: [
                {
                    label: "Valores Consolidados do Período (R$)",
                    data: [
                        Number(resumo.saldo_inicial || 0),
                        Number(resumo.total_entradas || 0),
                        Number(resumo.total_saidas || 0),
                        Number(resumo.total_investimentos || 0),
                        Number(resumo.total_transferencias_recebidas || 0),
                        Number(resumo.total_transferencias_enviadas || 0),
                        Number(resumo.saldo_final || 0)
                    ],
                    backgroundColor: [
                        "#64748b",
                        "#16a34a",
                        "#dc2626",
                        "#8b5cf6",
                        "#0ea5e9",
                        "#f97316",
                        "#15803d"
                    ],
                    borderRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom" }
            },
            scales: {
                y: {
                    ticks: { callback: (v) => formatarMoeda(v) }
                }
            }
        }
    });
}

/* =========================================================
   TAREFA 3 & 4: FILTROS, RELATÓRIO DE PERÍODO E EXPORTAÇÃO CSV
========================================================= */

function configurarFiltrosEExportacao() {
    const formFiltroMov = document.querySelector("#movements-filter-form");
    const btnLimparFiltro = document.querySelector("#clear-movements-filter");
    const formRelatorio = document.querySelector("#custom-report-form");

    formFiltroMov?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await aplicarFiltroMovimentacoes();
    });

    btnLimparFiltro?.addEventListener("click", async () => {
        formFiltroMov?.reset();
        movimentacoesFiltradasCache = todasMovimentacoesCache;
        renderizarTabelaDetalhada("#view-transactions-list", movimentacoesFiltradasCache);
        mostrarToast("Filtros limpos.", "info");
    });

    formRelatorio?.addEventListener("submit", async (event) => {
        event.preventDefault();
        await gerarRelatorioCustomizado();
    });

    document.querySelectorAll(".btn-exportar-csv").forEach((botao) => {
        botao.addEventListener("click", () => {
            exportarMovimentacoesCsv(movimentacoesFiltradasCache);
        });
    });
}

async function aplicarFiltroMovimentacoes() {
    const contaId = document.querySelector("#filter-account")?.value || "";
    const categoria = document.querySelector("#filter-category")?.value || "";
    const dataInicio = document.querySelector("#filter-start-date")?.value || "";
    const dataFim = document.querySelector("#filter-end-date")?.value || "";

    if (dataInicio && dataFim && dataFim < dataInicio) {
        mostrarToast("A data final não pode ser anterior à data inicial.", "error");
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        const filtradas = await buscarTodasAsPaginas("/fluxo-dinheiro/", {
            conta_bancaria_id: contaId,
            categoria,
            data_inicio: dataInicio,
            data_fim: dataFim
        });
        movimentacoesFiltradasCache = filtradas;
        renderizarTabelaDetalhada("#view-transactions-list", filtradas);
        mostrarToast(`${filtradas.length} movimentação(ões) encontrada(s).`, "info");
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

function calcularResumoLocal(dataInicio, dataFim, contaId = "") {
    const contasAlvo = contaId
        ? todasContas.filter((c) => c.id === Number(contaId))
        : todasContas;

    const saldoAtualTotal = contasAlvo.reduce(
        (acc, c) => acc + Number(c.valor_conta_atual || 0),
        0
    );

    const movsConta = contaId
        ? todasMovimentacoesCache.filter((m) => m.conta_bancaria_id === Number(contaId))
        : todasMovimentacoesCache;

    // Variação após dataInicio para deduzir o saldo inicial
    let variacaoAposInicio = 0;
    movsConta.forEach((m) => {
        if (m.data_movimentacao >= dataInicio) {
            const v = Number(m.valor || 0);
            if (m.tipo === "entrada") variacaoAposInicio += v;
            else if (m.tipo === "saida") variacaoAposInicio -= v;
            else if (m.tipo === "transferencia") {
                if (m.transferencia_direcao === "destino") variacaoAposInicio += v;
                else if (m.transferencia_direcao === "origem") variacaoAposInicio -= v;
            } else if (m.tipo === "ajuste") {
                variacaoAposInicio += v;
            }
        }
    });

    const saldoInicial = saldoAtualTotal - variacaoAposInicio;

    let totalEntradas = 0;
    let totalSaidas = 0;
    let totalInvestimentos = 0;
    let totalTransfRecebidas = 0;
    let totalTransfEnviadas = 0;
    let totalAjustes = 0;

    movsConta.forEach((m) => {
        if (m.data_movimentacao >= dataInicio && m.data_movimentacao <= dataFim) {
            const v = Number(m.valor || 0);
            if (m.tipo === "entrada") totalEntradas += v;
            else if (m.tipo === "saida") {
                totalSaidas += v;
                if (m.categoria === "investimento") totalInvestimentos += v;
            } else if (m.tipo === "transferencia") {
                if (m.transferencia_direcao === "destino") totalTransfRecebidas += v;
                else if (m.transferencia_direcao === "origem") totalTransfEnviadas += v;
            } else if (m.tipo === "ajuste") {
                totalAjustes += v;
            }
        }
    });

    const saldoFinal =
        saldoInicial +
        totalEntradas -
        totalSaidas +
        totalTransfRecebidas -
        totalTransfEnviadas +
        totalAjustes;

    return {
        saldo_inicial: saldoInicial,
        total_entradas: totalEntradas,
        total_saidas: totalSaidas,
        total_investimentos: totalInvestimentos,
        total_transferencias_recebidas: totalTransfRecebidas,
        total_transferencias_enviadas: totalTransfEnviadas,
        total_ajustes: totalAjustes,
        saldo_final: saldoFinal
    };
}

function exibirCardsRelatorio(resumo, dataInicio, dataFim) {
    const resultadoLiquido =
        Number(resumo.total_entradas || 0) - Number(resumo.total_saidas || 0);

    definirTexto("#report-initial-balance", formatarMoeda(resumo.saldo_inicial));
    definirTexto(
        "#report-period-description",
        `${formatarData(dataInicio)} até ${formatarData(dataFim)}`
    );
    definirTexto("#report-total-income", formatarMoeda(resumo.total_entradas));
    definirTexto(
        "#report-transfers-in",
        `Transferências recebidas: ${formatarMoeda(resumo.total_transferencias_recebidas)}`
    );
    definirTexto("#report-total-expenses", formatarMoeda(resumo.total_saidas));
    definirTexto(
        "#report-investments-out",
        `Aportes em investimento: ${formatarMoeda(resumo.total_investimentos)}`
    );
    definirTexto("#report-final-balance", formatarMoeda(resumo.saldo_final));
    definirTexto(
        "#report-net-result",
        `Resultado líquido: ${formatarMoeda(resultadoLiquido)}`
    );
    definirTexto(
        "#reports-period-label",
        `${formatarData(dataInicio)} — ${formatarData(dataFim)}`
    );

    renderizarGraficoRelatorioConsolidado(resumo);
}

function atualizarRelatorioPeriodoLocal(dataInicio, dataFim, contaId = "") {
    const resumo = calcularResumoLocal(dataInicio, dataFim, contaId);
    exibirCardsRelatorio(resumo, dataInicio, dataFim);
}

async function gerarRelatorioCustomizado() {
    const contaId = document.querySelector("#report-account")?.value || "";
    const dataInicio = document.querySelector("#report-start-date")?.value || "";
    const dataFim = document.querySelector("#report-end-date")?.value || "";
    const tipoSalvar = document.querySelector("#report-save-type")?.value || "";

    if (!dataInicio || !dataFim) {
        mostrarToast("Informe a data inicial e a data final.", "error");
        return;
    }
    if (dataFim < dataInicio) {
        mostrarToast("A data final não pode ser anterior à data inicial.", "error");
        return;
    }

    definirCarregamentoGlobal(true);
    try {
        const query = new URLSearchParams({
            data_inicio: dataInicio,
            data_fim: dataFim
        });
        if (contaId) {
            query.set("conta_bancaria_id", contaId);
        }

        // Busca o resumo consolidado na API (com fallback local caso necessário)
        let resumo;
        try {
            resumo = await api.get(`/calculos-financeiros/resumo?${query.toString()}`);
        } catch {
            resumo = calcularResumoLocal(dataInicio, dataFim, contaId);
        }

        exibirCardsRelatorio(resumo, dataInicio, dataFim);

        // Atualiza também a lista filtrada para exportação CSV do período
        const movsPeriodo = await buscarTodasAsPaginas("/fluxo-dinheiro/", {
            conta_bancaria_id: contaId,
            data_inicio: dataInicio,
            data_fim: dataFim
        });
        movimentacoesFiltradasCache = movsPeriodo;

        if (tipoSalvar) {
            if (!contaId) {
                mostrarToast(
                    "Selecione uma conta bancária específica para salvar um cálculo oficial.",
                    "info"
                );
                return;
            }
            await api.post("/calculos-financeiros/", {
                conta_bancaria_id: Number(contaId),
                tipo_calculo: tipoSalvar,
                data_inicio: dataInicio,
                data_fim: dataFim
            });
            calculosCarregados = await buscarTodasAsPaginas("/calculos-financeiros/");
            renderizarHistoricoCalculos(calculosCarregados);
            mostrarToast("Relatório gerado e salvo no histórico da API!");
        } else {
            mostrarToast("Relatório do período atualizado!");
        }
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        definirCarregamentoGlobal(false);
    }
}

function renderizarHistoricoCalculos(calculos) {
    const tbody = document.querySelector("#saved-calculations-list");
    if (!tbody) return;

    if (!calculos || calculos.length === 0) {
        atualizarTabelaVazia(
            "#saved-calculations-list",
            "Nenhum cálculo consolidado salvo ainda.",
            8
        );
        return;
    }

    const fragmento = document.createDocumentFragment();
    calculos.forEach((calc) => {
        const linha = document.createElement("tr");
        linha.append(
            criarElemento("td", obterNomeConta(calc.conta_bancaria_id)),
            criarElemento("td", calc.tipo_calculo),
            criarElemento(
                "td",
                `${formatarData(calc.data_inicio)} a ${formatarData(calc.data_fim)}`
            ),
            criarElemento("td", formatarMoeda(calc.valor_original), "align-right"),
            criarElemento(
                "td",
                formatarMoeda(calc.total_entradas),
                "align-right transaction-income"
            ),
            criarElemento(
                "td",
                formatarMoeda(calc.total_saidas),
                "align-right transaction-expense"
            ),
            criarElemento("td", formatarMoeda(calc.valor_final), "align-right")
        );

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "align-right";
        const btnExcluir = criarElemento(
            "button",
            "Excluir",
            "button-small button-danger"
        );
        btnExcluir.type = "button";
        btnExcluir.addEventListener("click", () => excluirCalculoSalvo(calc));
        celulaAcoes.append(btnExcluir);
        linha.append(celulaAcoes);

        fragmento.append(linha);
    });

    tbody.replaceChildren(fragmento);
}

function escaparValorCsv(valor) {
    const texto = valor === null || valor === undefined ? "" : String(valor);
    if (
        texto.includes(";") ||
        texto.includes(",") ||
        texto.includes('"') ||
        texto.includes("\n")
    ) {
        return `"${texto.replace(/"/g, '""')}"`;
    }
    return texto;
}

function exportarMovimentacoesCsv(listaMovimentacoes) {
    const dados =
        Array.isArray(listaMovimentacoes) && listaMovimentacoes.length > 0
            ? listaMovimentacoes
            : todasMovimentacoesCache;

    if (!dados || dados.length === 0) {
        mostrarToast("Não há movimentações disponíveis para exportar.", "info");
        return;
    }

    const cabecalho = [
        "ID",
        "Data",
        "Conta Bancaria",
        "Tipo",
        "Categoria",
        "Descricao",
        "Valor (R$)",
        "Observacao"
    ];

    const linhas = dados.map((mov) => [
        mov.id,
        mov.data_movimentacao,
        obterNomeConta(mov.conta_bancaria_id),
        mov.tipo,
        formatarCategoria(mov.categoria),
        mov.descricao,
        Number(mov.valor || 0).toFixed(2).replace(".", ","),
        mov.observacao || ""
    ]);

    const conteudoCsv =
        "\uFEFF" +
        [cabecalho, ...linhas]
            .map((linha) => linha.map(escaparValorCsv).join(";"))
            .join("\r\n");

    const blob = new Blob([conteudoCsv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `movimentacoes_fluxo_caixa_${formatarIso(new Date())}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    mostrarToast(`Arquivo CSV exportado com ${dados.length} registro(s)!`);
}

/* =========================================================
   CONFIGURAÇÕES: TEMA, DADOS CADASTRAIS E ZONA DE PERIGO
========================================================= */

function inicializarBotoesVerSenhaDashboard(root = document) {
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

function atualizarInterfaceTema(tema) {
    const escuro = tema === "dark";
    const botao = document.querySelector("#theme-toggle-button");
    const icone = document.querySelector("#theme-toggle-icon");
    const rotulo = document.querySelector("#theme-toggle-label");
    const statusTexto = document.querySelector("#theme-status-text");

    document.documentElement.setAttribute("data-theme", escuro ? "dark" : "light");
    document.body.classList.toggle("dark-theme", escuro);

    if (botao) {
        botao.setAttribute("aria-pressed", String(escuro));
    }
    if (icone) {
        if (escuro) {
            icone.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
        } else {
            icone.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
        }
    }
    if (rotulo) {
        rotulo.textContent = escuro ? "Ativar tema claro" : "Ativar tema escuro";
    }
    if (statusTexto) {
        statusTexto.textContent = "";
        statusTexto.append("Tema atual: ");
        const destaque = document.createElement("strong");
        destaque.textContent = escuro ? "Modo Escuro" : "Modo Claro";
        statusTexto.append(destaque);
    }
}

function configurarConfiguracoes() {
    inicializarBotoesVerSenhaDashboard();

    const temaInicial = localStorage.getItem("fluxo_caixa_tema") || "light";
    atualizarInterfaceTema(temaInicial);

    const botaoTema = document.querySelector("#theme-toggle-button");
    botaoTema?.addEventListener("click", () => {
        const atual = localStorage.getItem("fluxo_caixa_tema") === "dark" ? "dark" : "light";
        const proximo = atual === "dark" ? "light" : "dark";
        localStorage.setItem("fluxo_caixa_tema", proximo);
        atualizarInterfaceTema(proximo);
        mostrarToast(
            proximo === "dark" ? "Tema escuro ativado!" : "Tema claro ativado!",
            "info"
        );
    });

    const formPerfil = document.querySelector("#settings-profile-form");
    formPerfil?.addEventListener("submit", salvarAlteracoesPerfil);

    const btnAbrirExclusao = document.querySelector("#open-delete-account-dialog");
    const dialogoExclusao = document.querySelector("#delete-account-dialog");
    const formExclusao = document.querySelector("#delete-account-form");

    btnAbrirExclusao?.addEventListener("click", () => {
        formExclusao?.reset();
        limparMensagem("#delete-account-message");
        if (dialogoExclusao instanceof HTMLDialogElement) {
            aplicarScrollLock(true);
            dialogoExclusao.showModal();
        }
    });

    dialogoExclusao?.addEventListener("close", () => {
        limparMensagem("#delete-account-message");
        aplicarScrollLock(false);
    });

    formExclusao?.addEventListener("submit", confirmarExclusaoConta);
}

async function salvarAlteracoesPerfil(event) {
    event.preventDefault();
    limparMensagem("#settings-profile-message");

    const inputNome = document.querySelector("#settings-name");
    const inputEmail = document.querySelector("#settings-email");
    const inputTelefone = document.querySelector("#settings-phone");
    const inputSenhaAtual = document.querySelector("#settings-current-password");
    const inputNovaSenha = document.querySelector("#settings-new-password");
    const inputConfirmarSenha = document.querySelector("#settings-confirm-password");
    const btnSalvar = document.querySelector("#settings-save-btn");

    const nomeCompleto = inputNome?.value.trim() || "";
    const email = inputEmail?.value.trim() || "";
    const telefone = inputTelefone?.value.trim() || "";
    const senhaAtual = inputSenhaAtual?.value || "";
    const novaSenha = inputNovaSenha?.value || "";
    const confirmarSenha = inputConfirmarSenha?.value || "";

    if (!nomeCompleto || !email) {
        definirMensagem(
            "#settings-profile-message",
            "Nome completo e e-mail são obrigatórios.",
            "error"
        );
        return;
    }

    if (novaSenha || confirmarSenha) {
        if (!senhaAtual) {
            definirMensagem(
                "#settings-profile-message",
                "Informe sua senha atual para definir uma nova senha.",
                "error"
            );
            inputSenhaAtual?.focus();
            return;
        }
        if (novaSenha !== confirmarSenha) {
            definirMensagem(
                "#settings-profile-message",
                "A nova senha e a confirmação não conferem.",
                "error"
            );
            inputConfirmarSenha?.focus();
            return;
        }
    }

    const payload = {
        nome_completo: nomeCompleto,
        email,
        telefone: telefone || null
    };

    if (senhaAtual) {
        payload.senha_atual = senhaAtual;
    }
    if (novaSenha) {
        payload.nova_senha = novaSenha;
    }

    if (btnSalvar) btnSalvar.disabled = true;
    definirMensagem("#settings-profile-message", "Salvando alterações...", "info");

    try {
        const atualizado = await api.put("/usuarios/me", payload);
        usuarioAtual = atualizado;
        atualizarPerfilUsuario(atualizado);

        if (inputSenhaAtual) inputSenhaAtual.value = "";
        if (inputNovaSenha) inputNovaSenha.value = "";
        if (inputConfirmarSenha) inputConfirmarSenha.value = "";

        definirMensagem(
            "#settings-profile-message",
            "Dados cadastrais atualizados com sucesso!",
            "info"
        );
        mostrarToast("Configurações salvas com sucesso!");
    } catch (error) {
        definirMensagem("#settings-profile-message", error.message, "error");
    } finally {
        if (btnSalvar) btnSalvar.disabled = false;
    }
}

async function confirmarExclusaoConta(event) {
    event.preventDefault();
    limparMensagem("#delete-account-message");

    const inputSenha = document.querySelector("#delete-account-password");
    const btnExcluir = document.querySelector("#delete-account-submit-btn");
    const senhaAtual = inputSenha?.value || "";

    if (!senhaAtual) {
        definirMensagem(
            "#delete-account-message",
            "Digite sua senha atual para confirmar a exclusão da conta.",
            "error"
        );
        inputSenha?.focus();
        return;
    }

    if (btnExcluir) btnExcluir.disabled = true;
    definirMensagem(
        "#delete-account-message",
        "Excluindo sua conta permanentemente...",
        "info"
    );

    try {
        await api.delete("/usuarios/me", { senha_atual: senhaAtual });
        api.clearToken();
        localStorage.removeItem("fluxo_caixa_tema");
        window.location.replace("login.html");
    } catch (error) {
        definirMensagem("#delete-account-message", error.message, "error");
    } finally {
        if (btnExcluir) btnExcluir.disabled = false;
    }
}

/* =========================================================
   SELECTS CUSTOMIZADOS COM MENU SUSPENSO ARREDONDADO
========================================================= */

function inicializarSelectsArredondados(root = document) {
    const selects = root.querySelectorAll("select");
    const wrappersAtivos = new Set();

    function fecharTodosMenus(excetoWrapper = null) {
        wrappersAtivos.forEach((wrapper) => {
            if (wrapper !== excetoWrapper) {
                wrapper.classList.remove("is-open");
                const menu = wrapper.querySelector(".custom-select-menu");
                const trigger = wrapper.querySelector(".custom-select-trigger");
                if (menu) menu.hidden = true;
                if (trigger) trigger.setAttribute("aria-expanded", "false");
            }
        });
    }

    selects.forEach((select) => {
        if (select.dataset.customSelectReady === "true") return;
        select.dataset.customSelectReady = "true";
        select.classList.add("custom-select-native");

        const wrapper = document.createElement("div");
        wrapper.className = "custom-select-wrapper";
        select.parentNode.insertBefore(wrapper, select);
        wrapper.append(select);
        wrappersAtivos.add(wrapper);

        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "custom-select-trigger";
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");

        const labelSpan = document.createElement("span");
        labelSpan.className = "custom-select-label";

        const arrowSpan = document.createElement("span");
        arrowSpan.className = "custom-select-arrow";
        arrowSpan.setAttribute("aria-hidden", "true");
        arrowSpan.innerHTML =
            '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>';

        trigger.append(labelSpan, arrowSpan);

        const menu = document.createElement("ul");
        menu.className = "custom-select-menu";
        menu.setAttribute("role", "listbox");
        menu.hidden = true;

        wrapper.append(trigger, menu);

        function sincronizarOpcoes() {
            const opcoes = Array.from(select.options);
            const selecionada =
                opcoes.find((opt) => opt.value === select.value) ||
                opcoes[select.selectedIndex] ||
                opcoes[0];

            labelSpan.textContent = selecionada ? selecionada.textContent : "Selecione...";
            menu.replaceChildren();

            opcoes.forEach((opt) => {
                const item = document.createElement("li");
                item.className = "custom-select-option";
                item.setAttribute("role", "option");
                const ativo = opt.value === select.value;
                item.classList.toggle("is-selected", ativo);
                item.setAttribute("aria-selected", String(ativo));
                item.textContent = opt.textContent;

                item.addEventListener("click", (event) => {
                    event.stopPropagation();
                    if (select.value !== opt.value) {
                        select.value = opt.value;
                        select.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                    sincronizarOpcoes();
                    fecharTodosMenus();
                });

                menu.append(item);
            });
        }

        trigger.addEventListener("click", (event) => {
            event.stopPropagation();
            const abrindo = menu.hidden;
            fecharTodosMenus(wrapper);
            sincronizarOpcoes();
            menu.hidden = !abrindo;
            wrapper.classList.toggle("is-open", abrindo);
            trigger.setAttribute("aria-expanded", String(abrindo));
        });

        select.addEventListener("change", sincronizarOpcoes);
        select.form?.addEventListener("reset", () => {
            setTimeout(sincronizarOpcoes, 0);
        });

        // Intercepta atribuições diretas a select.value (ex: abrirDialogoConta / atualizarCamposTipoMovimentacao)
        const descritorNativo = Object.getOwnPropertyDescriptor(
            HTMLSelectElement.prototype,
            "value"
        );
        if (descritorNativo && descritorNativo.get && descritorNativo.set) {
            Object.defineProperty(select, "value", {
                get() {
                    return descritorNativo.get.call(this);
                },
                set(novoValor) {
                    descritorNativo.set.call(this, novoValor);
                    sincronizarOpcoes();
                },
                configurable: true
            });
        }

        const observer = new MutationObserver(() => {
            sincronizarOpcoes();
        });
        observer.observe(select, { childList: true, subtree: true, attributes: true });

        sincronizarOpcoes();
    });

    document.addEventListener("click", () => fecharTodosMenus());
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            fecharTodosMenus();
        }
    });
}


function inicializarOrcamentosAlertas() {
    const mes = document.querySelector('#orcamento-mes');
    const agora = new Date();
    mes.value = `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, '0')}`;
    const select = document.querySelector('#orcamento-categoria');
    document.querySelectorAll('#categories-cards-grid [data-category]').forEach(card => {
        const option = document.createElement('option');
        option.value = card.dataset.category;
        option.textContent = card.querySelector('strong').textContent;
        select.append(option);
    });
    mes.addEventListener('change', atualizarOrcamentos);
    document.querySelector('#orcamento-form').addEventListener('submit', async event => {
        event.preventDefault();
        const msg = document.querySelector('#orcamento-mensagem');
        try {
            const lista = await api.get(`/orcamentos?mes=${mes.value}-01`);
            const existente = lista.find(o => o.categoria === select.value);
            const dados = {mes: `${mes.value}-01`, categoria: select.value, limite: document.querySelector('#orcamento-limite').value};
            if (existente) await api.put(`/orcamentos/${existente.id}`, dados);
            else await api.post('/orcamentos', dados);
            msg.textContent = 'Orçamento salvo.';
            await atualizarOrcamentosAlertas();
        } catch (e) { msg.textContent = e.message; }
    });
    ['orcamento', 'vencimento'].forEach(tipo => document.querySelector(`#alerta-${tipo}`).addEventListener('change', async () => {
        try {
            await api.put('/alertas/preferencias', {orcamento: document.querySelector('#alerta-orcamento').checked, vencimento: document.querySelector('#alerta-vencimento').checked});
            await atualizarAlertas();
        } catch (e) { document.querySelector('#alertas-mensagem').textContent = e.message; }
    }));
    atualizarOrcamentosAlertas();
}

async function atualizarOrcamentosAlertas() {
    await Promise.all([atualizarOrcamentos(), atualizarAlertas()]);
}

async function atualizarOrcamentos() {
    const msg = document.querySelector('#orcamento-mensagem');
    const lista = document.querySelector('#orcamento-lista');
    try {
        const mes = document.querySelector('#orcamento-mes').value;
        if (!mes) return;
        const dados = await api.get(`/orcamentos?mes=${mes}-01`);
        lista.replaceChildren();
        dados.forEach(o => {
            const li = document.createElement('li');
            const texto = document.createElement('span');
            texto.textContent = `${formatarCategoria(o.categoria)}: gasto ${formatarMoeda(Number(o.gasto))} / ${formatarMoeda(Number(o.limite))} · restante ${formatarMoeda(Number(o.restante))} `;
            const editar = document.createElement('button');
            editar.type = 'button'; editar.textContent = 'Editar';
            editar.addEventListener('click', () => {
                document.querySelector('#orcamento-categoria').value = o.categoria;
                document.querySelector('#orcamento-limite').value = o.limite;
                document.querySelector('#orcamento-limite').focus();
            });
            const excluir = document.createElement('button');
            excluir.type = 'button'; excluir.textContent = 'Excluir';
            excluir.addEventListener('click', async () => {
                if (!window.confirm('Excluir este orçamento?')) return;
                try { await api.delete(`/orcamentos/${o.id}`); await atualizarOrcamentosAlertas(); }
                catch (e) { msg.textContent = e.message; }
            });
            li.append(texto, editar, excluir); lista.append(li);
        });
        if (!dados.length) msg.textContent = 'Nenhum orçamento neste mês.';
        else msg.textContent = '';
    } catch (e) { msg.textContent = e.message; }
}

async function atualizarAlertas() {
    const msg = document.querySelector('#alertas-mensagem');
    const lista = document.querySelector('#alertas-lista');
    try {
        const [prefs, dados] = await Promise.all([api.get('/alertas/preferencias'), api.get('/alertas')]);
        document.querySelector('#alerta-orcamento').checked = prefs.orcamento;
        document.querySelector('#alerta-vencimento').checked = prefs.vencimento;
        lista.replaceChildren();
        dados.forEach(a => {
            const li = document.createElement('li');
            const texto = document.createElement('span');
            texto.textContent = `${a.mensagem} ${a.lido ? '(lido)' : ''} `;
            li.append(texto);
            if (!a.lido) {
                const botao = document.createElement('button');
                botao.type = 'button'; botao.textContent = 'Marcar como lido';
                botao.addEventListener('click', async () => {
                    try { await api.put(`/alertas/lido?chave=${encodeURIComponent(a.chave)}`, {}); await atualizarAlertas(); }
                    catch (e) { msg.textContent = e.message; }
                });
                li.append(botao);
            }
            lista.append(li);
        });
        msg.textContent = dados.length ? '' : 'Nenhum alerta no momento.';
    } catch (e) { msg.textContent = e.message; }
}
