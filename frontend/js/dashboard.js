/*
 * FLUXO DE CAIXA
 * Inicialização e dados reais do dashboard.
 */

let contasCarregadas = [];

const titulosViews = {
    dashboard: {
        eyebrow: "VISÃO GERAL",
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
        subtitle: "Histórico completo de entradas, saídas e transferências."
    },
    categorias: {
        eyebrow: "CLASSIFICAÇÃO",
        title: "Categorias financeiras",
        subtitle: "Distribuição e controle de gastos e receitas por categoria."
    },
    investimentos: {
        eyebrow: "PATRIMÔNIO",
        title: "Investimentos",
        subtitle: "Acompanhe seus aportes, poupanças e patrimônio investido."
    },
    relatorios: {
        eyebrow: "CONSOLIDAÇÃO",
        title: "Relatórios financeiros",
        subtitle: "Balanços comparativos e evolução periódica das finanças."
    }
};

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
            const linkTarget = (link.getAttribute("href") || "").replace("#", "").toLowerCase();
            const ativo = linkTarget === viewName;
            link.classList.toggle("active", ativo);
            if (ativo) {
                link.setAttribute("aria-current", "page");
            } else {
                link.removeAttribute("aria-current");
            }
        });

        const info = titulosViews[viewName] || titulosViews.dashboard;
        const eyebrow = document.querySelector("#view-eyebrow");
        const title = document.querySelector("#view-title");
        const subtitle = document.querySelector("#view-subtitle");

        if (eyebrow) eyebrow.textContent = info.eyebrow;
        if (title) title.textContent = info.title;
        if (subtitle) subtitle.textContent = info.subtitle;

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

function verificarSessao() {
    if (!api.getToken()) {
        window.location.replace("login.html");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.addEventListener("pageshow", verificarSessao);
    if (!api.getToken()) return;

    atualizarData();
    configurarNavegacao();
    configurarDialogos();
    configurarBotaoSair();
    carregarDashboard();
});

function configurarBotaoSair() {
    const botao = document.querySelector("#logout");
    if (!botao) return;

    botao.addEventListener("click", () => {
        api.clearToken();
        window.location.replace("login.html");
    });
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

function configurarDialogos() {
    const formularioConta = document.querySelector("#account-form");
    const formularioMovimentacao = document.querySelector("#movement-form");

    document.querySelectorAll(".btn-abrir-nova-conta, #new-account").forEach((botao) => {
        botao.addEventListener("click", abrirDialogoConta);
    });
    document.querySelectorAll(".btn-abrir-nova-movimentacao, #new-movement").forEach((botao) => {
        botao.addEventListener("click", abrirDialogoMovimentacao);
    });

    document.querySelectorAll("[data-close-dialog]").forEach((botao) => {
        botao.addEventListener("click", () => {
            const dialogo = document.querySelector(
                `#${botao.dataset.closeDialog}`
            );
            if (dialogo instanceof HTMLDialogElement) dialogo.close();
        });
    });

    formularioConta?.addEventListener("submit", salvarConta);
    formularioMovimentacao?.addEventListener(
        "submit",
        salvarMovimentacao
    );

    document.querySelector("#account-dialog")?.addEventListener(
        "close",
        () => limparMensagem("#account-message")
    );
    document.querySelector("#movement-dialog")?.addEventListener(
        "close",
        () => limparMensagem("#movement-message")
    );
}

function abrirDialogoConta() {
    const dialogo = document.querySelector("#account-dialog");
    if (dialogo instanceof HTMLDialogElement) dialogo.showModal();
}

function abrirDialogoMovimentacao() {
    if (contasCarregadas.length === 0) {
        abrirDialogoConta();
        definirMensagem(
            "#account-message",
            "Cadastre uma conta antes de registrar movimentações.",
            "info"
        );
        return;
    }

    const seletor = document.querySelector("#movement-account");
    const ajuda = document.querySelector("#movement-account-help");
    if (seletor) {
        seletor.replaceChildren();
        contasCarregadas.forEach((conta) => {
            const opcao = document.createElement("option");
            opcao.value = String(conta.id);
            opcao.textContent = `${conta.nome_banco} (${conta.tipo_conta}) — ${formatarMoeda(conta.valor_conta_atual)}`;
            seletor.append(opcao);
        });

        const atualizarAjudaConta = () => {
            const idSelecionado = Number(seletor.value);
            const conta = contasCarregadas.find((c) => c.id === idSelecionado);
            if (ajuda && conta) {
                ajuda.textContent = `Saldo atual: ${formatarMoeda(conta.valor_conta_atual)} (${conta.tipo_conta})`;
            }
        };

        seletor.onchange = atualizarAjudaConta;
        atualizarAjudaConta();
    }

    const inputData = document.querySelector("#movement-date");
    if (inputData && !inputData.value) {
        const agora = new Date();
        const ano = agora.getFullYear();
        const mes = String(agora.getMonth() + 1).padStart(2, "0");
        const dia = String(agora.getDate()).padStart(2, "0");
        inputData.value = `${ano}-${mes}-${dia}`;
    }

    const dialogo = document.querySelector("#movement-dialog");
    if (dialogo instanceof HTMLDialogElement) dialogo.showModal();
}

async function salvarConta(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);

    definirMensagem("#account-message", "Salvando conta...", "info");
    botao.disabled = true;

    try {
        await api.post("/contas-bancarias/", {
            nome_banco: dados.get("nome_banco").trim(),
            tipo_conta: dados.get("tipo_conta"),
            valor_conta_atual: dados.get("valor_conta_atual"),
            ativa: true
        });
        formulario.reset();
        document.querySelector("#account-balance").value = "0.00";
        document.querySelector("#account-dialog").close();
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#account-message", error.message, "error");
    } finally {
        botao.disabled = false;
    }
}

async function salvarMovimentacao(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const botao = formulario.querySelector('[type="submit"]');
    const dados = new FormData(formulario);

    definirMensagem("#movement-message", "Salvando movimentação...", "info");
    botao.disabled = true;

    try {
        await api.post("/fluxo-dinheiro/", {
            conta_bancaria_id: Number(dados.get("conta_bancaria_id")),
            descricao: dados.get("descricao").trim(),
            valor: dados.get("valor"),
            tipo: dados.get("tipo"),
            categoria: dados.get("categoria"),
            data_movimentacao: dados.get("data_movimentacao"),
            observacao: dados.get("observacao").trim() || null
        });
        formulario.reset();
        document.querySelector("#movement-dialog").close();
        await carregarDashboard();
    } catch (error) {
        definirMensagem("#movement-message", error.message, "error");
    } finally {
        botao.disabled = false;
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
    return Number(valor).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function formatarData(valor) {
    const [ano, mes, dia] = valor.split("-");
    return `${dia}/${mes}/${ano}`;
}

function criarElemento(tag, texto, classe) {
    const elemento = document.createElement(tag);
    elemento.textContent = texto;
    if (classe) elemento.className = classe;
    return elemento;
}

async function buscarTodasAsPaginas(path, parametros = {}) {
    const limit = 100;
    const resultados = [];
    let offset = 0;

    while (true) {
        const query = new URLSearchParams({
            ...parametros,
            limit: String(limit),
            offset: String(offset)
        });
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

    try {
        const hoje = new Date();
        const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const formatarIso = (data) => {
            const ano = data.getFullYear();
            const mes = String(data.getMonth() + 1).padStart(2, "0");
            const dia = String(data.getDate()).padStart(2, "0");
            return `${ano}-${mes}-${dia}`;
        };

        const [contas, movimentacoesMes, movimentacoesRecentes, movimentacoesTodas] =
            await Promise.all([
                buscarTodasAsPaginas("/contas-bancarias/"),
                buscarTodasAsPaginas("/fluxo-dinheiro/", {
                    data_inicio: formatarIso(inicioMes),
                    data_fim: formatarIso(hoje)
                }),
                api.get("/fluxo-dinheiro/?limit=10&offset=0"),
                buscarTodasAsPaginas("/fluxo-dinheiro/")
            ]);

        if (!Array.isArray(movimentacoesRecentes)) {
            throw new Error("A API retornou movimentações em formato inesperado.");
        }

        contasCarregadas = contas.filter((conta) => conta.ativa);
        atualizarResumo(contas, movimentacoesMes);
        atualizarContas(contas);
        atualizarMovimentacoes(movimentacoesRecentes, movimentacoesTodas);
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
            "Não foi possível carregar as movimentações."
        );
        atualizarStatus(error.message, false);
    }

    function atualizarStatus(texto, conectado) {
        if (statusElement) statusElement.textContent = texto;
        if (statusDot) {
            statusDot.style.backgroundColor = conectado ? "#16a34a" : "#dc2626";
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

    definirTexto("#total-balance", formatarMoeda(saldo));
    definirTexto("#total-income", formatarMoeda(receitas));
    definirTexto("#total-expenses", formatarMoeda(despesas));
    definirTexto("#monthly-result", formatarMoeda(receitas - despesas));
}

function definirTexto(seletor, texto) {
    const elemento = document.querySelector(seletor);
    if (elemento) elemento.textContent = texto;
}

function atualizarEstadoVazio(seletor, titulo, descricao) {
    const elemento = document.querySelector(seletor);
    if (!elemento) return;

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
        definirTexto("#savings-total", "R$ 0,00");
        return;
    }

    // Atualiza resumo no dashboard
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

    // Atualiza lista na view de contas
    if (elementoView) {
        elementoView.replaceChildren();
        elementoView.className = "accounts-list";

        contas.forEach((conta) => {
            const linha = document.createElement("div");
            linha.className = "account-summary";
            linha.style.padding = "16px";
            linha.style.marginBottom = "8px";
            linha.append(
                criarElemento("strong", `${conta.nome_banco} (${conta.tipo_conta})`),
                criarElemento("span", formatarMoeda(conta.valor_conta_atual))
            );
            elementoView.append(linha);
        });
    }

    // Atualiza totais na view de investimentos
    const totalInvestimentos = contas
        .filter((c) => c.tipo_conta === "investimento")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);
    const totalPoupanca = contas
        .filter((c) => c.tipo_conta === "poupanca")
        .reduce((acc, c) => acc + Number(c.valor_conta_atual), 0);

    definirTexto("#investments-total", formatarMoeda(totalInvestimentos));
    definirTexto("#savings-total", formatarMoeda(totalPoupanca));
}

function atualizarTabelaVazia(seletorTabela, mensagem) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    const celula = criarElemento("td", mensagem, "table-empty");
    celula.colSpan = 5;
    const linha = document.createElement("tr");
    linha.append(celula);
    tabela.replaceChildren(linha);
}

function renderizarTabela(seletorTabela, lista) {
    const tabela = document.querySelector(seletorTabela);
    if (!tabela) return;

    if (!lista || lista.length === 0) {
        atualizarTabelaVazia(seletorTabela, "Nenhuma movimentação cadastrada.");
        return;
    }

    const fragmento = document.createDocumentFragment();

    lista.forEach((movimento) => {
        const linha = document.createElement("tr");
        const valores = [
            movimento.descricao,
            movimento.categoria,
            formatarData(movimento.data_movimentacao),
            movimento.tipo,
            formatarMoeda(movimento.valor)
        ];

        valores.forEach((valor, indice) => {
            const celula = criarElemento("td", valor);
            if (indice === 4) celula.className = "align-right";
            linha.append(celula);
        });

        fragmento.append(linha);
    });

    tabela.replaceChildren(fragmento);
}

function atualizarMovimentacoes(movimentacoesRecentes, todasMovimentacoes = null) {
    renderizarTabela("#transactions-list", movimentacoesRecentes);
    renderizarTabela(
        "#view-transactions-list",
        todasMovimentacoes || movimentacoesRecentes
    );
}
