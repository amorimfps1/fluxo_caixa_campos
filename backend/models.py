from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    UniqueConstraint,
    text,
)
from decimal import Decimal

from database import Base


# =========================================================
# 1. USUÁRIOS
# =========================================================
# Tabela: usuarios
#
# Armazena os dados dos usuários do sistema.
# =========================================================

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("cpf_indice", name="uq_usuarios_cpf_indice"),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    nome_completo = Column(
        String(150),
        nullable=False
    )

    cpf = Column(
        String(255),
        unique=True,
        nullable=False
    )

    cpf_indice = Column(
        String(64),
        nullable=False,
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False
    )

    telefone = Column(
        String(255),
        nullable=True,
    )

    email_verificado = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    codigo_verificacao_hash = Column(
        String(64),
        nullable=True,
    )

    codigo_expira_em = Column(
        DateTime,
        nullable=True,
    )

    senha_hash = Column(
        String(255),
        nullable=False
    )

    criado_em = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )


class TentativaLogin(Base):
    __tablename__ = "tentativas_login"
    __table_args__ = (
        Index("idx_tentativas_login_janela", "inicio_janela"),
    )

    chave_cliente = Column(
        String(64),
        primary_key=True,
    )

    tentativas = Column(
        Integer,
        nullable=False,
        default=0,
    )

    inicio_janela = Column(
        DateTime,
        nullable=False,
    )

    bloqueado_ate = Column(
        DateTime,
        nullable=True,
    )


# =========================================================
# 2. CONTAS BANCÁRIAS
# =========================================================
# Tabela: contas_bancarias
#
# Armazena as contas bancárias pertencentes aos usuários.
# =========================================================

class ContaBancaria(Base):
    __tablename__ = "contas_bancarias"
    __table_args__ = (
        Index("idx_contas_usuario", "usuario_id"),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    nome_banco = Column(
        String(100),
        nullable=False
    )

    tipo_conta = Column(
        Enum(
            "corrente",
            "poupanca",
            "investimento"
        ),
        nullable=False
    )

    valor_conta_atual = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    ativa = Column(
        Boolean,
        nullable=False,
        default=True
    )

    criado_em = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )


# =========================================================
# 3. FLUXO DE DINHEIRO
# =========================================================
# Tabela: fluxo_dinheiro
#
# Registra todas as movimentações financeiras:
# - entrada
# - saída
# - transferência
# =========================================================

class CategoriaMovimentacao(Base):
    __tablename__ = "categorias_movimentacao"

    nome = Column(
        String(100),
        primary_key=True,
    )


class FluxoDinheiro(Base):
    __tablename__ = "fluxo_dinheiro"
    __table_args__ = (
        Index("idx_fluxo_conta", "conta_bancaria_id"),
        Index("idx_fluxo_data", "data_movimentacao"),
        Index("idx_fluxo_tipo", "tipo"),
        Index("ix_fluxo_dinheiro_transferencia_id", "transferencia_id"),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    conta_bancaria_id = Column(
        Integer,
        ForeignKey(
            "contas_bancarias.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    descricao = Column(
        String(200),
        nullable=False
    )

    valor = Column(
        Numeric(12, 2),
        nullable=False
    )

    tipo = Column(
        Enum(
            "entrada",
            "saida",
            "transferencia",
            "ajuste",
            "investimento",
        ),
        nullable=False
    )

    categoria = Column(
        String(100),
        ForeignKey(
            "categorias_movimentacao.nome",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False
    )

    data_movimentacao = Column(
        Date,
        nullable=False
    )

    observacao = Column(
        String(255),
        nullable=True
    )

    transferencia_id = Column(
        String(36),
        nullable=True
    )

    transferencia_direcao = Column(
        Enum("origem", "destino"),
        nullable=True
    )

    natureza_conta = Column(
        Enum("fixa", "variavel"),
        nullable=True,
    )

    dia_repeticao = Column(
        Integer,
        nullable=True,
    )

    tipo_investimento = Column(
        String(60),
        nullable=True,
    )

    conta_destino_id = Column(
        Integer,
        ForeignKey(
            "contas_bancarias.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=True,
    )


# =========================================================
# 4. CÁLCULOS FINANCEIROS
# =========================================================
# Tabela: calculos_financeiros
#
# Armazena os resultados dos cálculos financeiros
# realizados para uma determinada conta e período.
# =========================================================

class CalculoFinanceiro(Base):
    __tablename__ = "calculos_financeiros"
    __table_args__ = (
        Index("idx_calculo_conta", "conta_bancaria_id"),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    conta_bancaria_id = Column(
        Integer,
        ForeignKey(
            "contas_bancarias.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    tipo_calculo = Column(
        Enum(
            "diario",
            "semanal",
            "mensal",
            "anual"
        ),
        nullable=False
    )

    data_inicio = Column(
        Date,
        nullable=False
    )

    data_fim = Column(
        Date,
        nullable=False
    )

    valor_original = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_entradas = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_saidas = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_investimentos = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_transferencias_recebidas = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_transferencias_enviadas = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_ajustes = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    valor_final = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    criado_em = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )


# =========================================================
# 5. METAS FINANCEIRAS
# =========================================================
# Tabela: metas_financeiras
#
# Armazena os objetivos financeiros dos usuários.
# =========================================================

class MetaFinanceira(Base):
    __tablename__ = "metas_financeiras"
    __table_args__ = (
        Index("idx_metas_usuario", "usuario_id"),
    )

    id = Column(
        Integer,
        primary_key=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        nullable=False
    )

    nome = Column(
        String(150),
        nullable=False
    )

    valor_meta = Column(
        Numeric(12, 2),
        nullable=False
    )

    valor_atual = Column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    data_inicio = Column(
        Date,
        nullable=False
    )

    data_limite = Column(
        Date,
        nullable=True
    )

    status = Column(
        Enum(
            "em_andamento",
            "concluida",
            "cancelada"
        ),
        nullable=False,
        default="em_andamento"
    )

    descricao = Column(
        String(255),
        nullable=True
    )

    criado_em = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )