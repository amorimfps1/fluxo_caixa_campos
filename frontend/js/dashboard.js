/*
 * FLUXO DE CAIXA
 * Inicialização e dados reais do dashboard.
 */

document.addEventListener("DOMContentLoaded", () => {
    if (!api.getToken()) {
        window.location.replace("login.html");
        return;
    }

    atualizarData();
    configurarBotaoNovaMovimentacao();
    carregarDashboard();
});

function atualizarData() {
    const dateElement = document.querySelector("#current-date");
    if (!dateElement) return;

    dateElement.textContent = new Date().toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}

function configurarBotaoNovaMovimentacao() {
    const button = document.querySelector("#new-movement");
    if (!button) return;

    button.addEventListener("click", () => {
        alert("O formulário de nova movimentação será implementado em breve.");
    });
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

        const [contas, movimentacoesMes, movimentacoesRecentes] =
            await Promise.all([
                buscarTodasAsPaginas("/contas-bancarias/"),
                buscarTodasAsPaginas("/fluxo-dinheiro/", {
                    data_inicio: formatarIso(inicioMes),
                    data_fim: formatarIso(hoje)
                }),
                api.get("/fluxo-dinheiro/?limit=10&offset=0")
            ]);

        if (!Array.isArray(movimentacoesRecentes)) {
            throw new Error("A API retornou movimentações em formato inesperado.");
        }

        atualizarResumo(contas, movimentacoesMes);
        atualizarContas(contas);
        atualizarMovimentacoes(movimentacoesRecentes);
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
    if (!elemento) return;

    if (contas.length === 0) {
        atualizarEstadoVazio(
            "#accounts-list",
            "Nenhuma conta cadastrada.",
            "As contas registradas na API aparecerão aqui."
        );
        return;
    }

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

function atualizarTabelaVazia(mensagem) {
    const tabela = document.querySelector("#transactions-list");
    if (!tabela) return;

    const celula = criarElemento("td", mensagem, "table-empty");
    celula.colSpan = 5;
    const linha = document.createElement("tr");
    linha.append(celula);
    tabela.replaceChildren(linha);
}

function atualizarMovimentacoes(movimentacoes) {
    const tabela = document.querySelector("#transactions-list");
    if (!tabela) return;

    if (movimentacoes.length === 0) {
        atualizarTabelaVazia("Nenhuma movimentação cadastrada.");
        return;
    }

    const fragmento = document.createDocumentFragment();

    movimentacoes.forEach((movimento) => {
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
