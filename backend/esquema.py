from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator
)
from pydantic import model_validator
from dados_sensiveis import descriptografar_telefone

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from typing import Optional, Literal
import calendar
import unicodedata


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# MODELOS DE ENTRADA
# =========================================================

CategoriaMovimentacaoInput = Literal[
    "alimentacao",
    "ajuste",
    "compras",
    "contas",
    "educacao",
    "freelance",
    "impostos",
    "investimento",
    "lazer",
    "moradia",
    "outros",
    "salario",
    "saude",
    "transporte",
    "transferencia",
    "vendas",
]


def _normalizar_categoria(valor: str) -> str:
    decomposicao = unicodedata.normalize("NFKD", valor.strip().casefold())
    sem_acentos = "".join(
        caractere
        for caractere in decomposicao
        if not unicodedata.combining(caractere)
    )
    return "investimento" if sem_acentos == "investimentos" else sem_acentos


class UsuarioCreate(InputModel):
    nome_completo: str = Field(
        min_length=3,
        max_length=150
    )

    cpf: str
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=32)

    senha: str = Field(
        min_length=8,
        max_length=100
    )

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str | None) -> str | None:
        if valor is None or not valor.strip():
            return None

        telefone = valor.strip()
        caracteres_permitidos = set("+0123456789 ().-")
        if any(caractere not in caracteres_permitidos for caractere in telefone):
            raise ValueError("O telefone contém caracteres inválidos.")
        if telefone.count("+") > 1 or (
            "+" in telefone and not telefone.startswith("+")
        ):
            raise ValueError("O código do país deve aparecer no início.")

        digitos = "".join(
            caractere for caractere in telefone if caractere.isdigit()
        )
        if not 10 <= len(digitos) <= 15:
            raise ValueError(
                "O telefone deve conter entre 10 e 15 dígitos."
            )
        return telefone

    # -----------------------------------------------------
    # VALIDAR NOME
    # -----------------------------------------------------

    @field_validator("nome_completo")
    @classmethod
    def validar_nome(cls, valor):
        valor = valor.strip()

        if not valor:
            raise ValueError(
                "O nome não pode ficar vazio."
            )

        return valor

    # -----------------------------------------------------
    # VALIDAR CPF
    # -----------------------------------------------------

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:

        # Remove pontos e hífen
        valor = (
            valor
            .replace(".", "")
            .replace("-", "")
            .strip()
        )

        if len(valor) != 11:
            raise ValueError(
                "O CPF deve possuir 11 números."
            )

        if not valor.isascii() or not valor.isdigit():
            raise ValueError(
                "O CPF deve conter apenas números."
            )

        if len(set(valor)) == 1:
            raise ValueError("O CPF informado é inválido.")

        primeiro_digito = (
            sum(
                int(digito) * peso
                for digito, peso in zip(valor[:9], range(10, 1, -1))
            )
            * 10
        ) % 11
        if primeiro_digito == 10:
            primeiro_digito = 0

        segundo_digito = (
            sum(
                int(digito) * peso
                for digito, peso in zip(valor[:10], range(11, 1, -1))
            )
            * 10
        ) % 11
        if segundo_digito == 10:
            segundo_digito = 0

        if valor[-2:] != f"{primeiro_digito}{segundo_digito}":
            raise ValueError("O CPF informado é inválido.")

        return valor

    # -----------------------------------------------------
    # VALIDAR SENHA
    # -----------------------------------------------------

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor):

        if not any(c.isupper() for c in valor):
            raise ValueError(
                "A senha deve possuir pelo menos uma letra maiúscula."
            )

        if not any(c.islower() for c in valor):
            raise ValueError(
                "A senha deve possuir pelo menos uma letra minúscula."
            )

        if not any(c.isdigit() for c in valor):
            raise ValueError(
                "A senha deve possuir pelo menos um número."
            )

        if not any(
            not c.isalnum()
            for c in valor
        ):
            raise ValueError(
                "A senha deve possuir pelo menos um caractere especial."
            )

        return valor


class EsqueciSenhaRequest(InputModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()


class ConfirmarEmailRequest(InputModel):
    email: EmailStr
    codigo_otp: str = Field(min_length=6, max_length=10)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()

    @field_validator("codigo_otp")
    @classmethod
    def validar_codigo_otp(cls, valor: str) -> str:
        codigo = valor.strip()
        if not codigo.isdigit() or len(codigo) != 6:
            raise ValueError("O código de verificação deve conter 6 dígitos numéricos.")
        return codigo


class RedefinirSenhaRequest(InputModel):
    email: EmailStr
    codigo_otp: str | None = Field(default=None, min_length=6, max_length=10)
    cpf: str | None = None
    nova_senha: str = Field(
        min_length=8,
        max_length=100
    )

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()

    @field_validator("codigo_otp")
    @classmethod
    def validar_codigo_otp(cls, valor: str | None) -> str | None:
        if valor is None or not valor.strip():
            return None
        codigo = valor.strip()
        if not codigo.isdigit() or len(codigo) != 6:
            raise ValueError("O código de verificação deve conter 6 dígitos numéricos.")
        return codigo

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str | None) -> str | None:
        if valor is None or not valor.strip():
            return None
        return UsuarioCreate.validar_cpf(valor)

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, valor: str) -> str:
        return UsuarioCreate.validar_senha(valor)

    @model_validator(mode="after")
    def validar_credencial_recuperacao(self):
        if not self.codigo_otp and not self.cpf:
            raise ValueError(
                "Informe o código de verificação enviado por e-mail (codigo_otp) ou o CPF."
            )
        return self


class UsuarioUpdateMe(InputModel):
    nome_completo: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
    )
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, max_length=32)
    senha_atual: str | None = Field(default=None, min_length=1, max_length=100)
    nova_senha: str | None = Field(default=None, min_length=8, max_length=100)

    @field_validator("nome_completo")
    @classmethod
    def validar_nome(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return UsuarioCreate.validar_nome(valor)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr | None) -> str | None:
        if valor is None:
            return None
        return str(valor).strip().lower()

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str | None) -> str | None:
        return UsuarioCreate.validar_telefone(valor)

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, valor: str | None) -> str | None:
        if valor is None or not valor:
            return None
        return UsuarioCreate.validar_senha(valor)

    @model_validator(mode="after")
    def validar_alteracao_senha(self):
        if self.nova_senha and not self.senha_atual:
            raise ValueError("Informe a senha atual para definir uma nova senha.")
        return self


class ExcluirContaRequest(InputModel):
    senha_atual: str = Field(min_length=1, max_length=100)


class UsuarioResponse(BaseModel):
    id: int
    nome_completo: str
    email: EmailStr
    telefone: str | None
    email_verificado: bool = False
    criado_em: datetime

    @field_validator("telefone", mode="before")
    @classmethod
    def descriptografar_telefone_no_retorno(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None
        return descriptografar_telefone(valor)

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# CONTAS BANCÁRIAS
# =========================================================


class ContaBancariaCreate(InputModel):
    nome_banco: str = Field(
        min_length=2,
        max_length=100
    )

    tipo_conta: Literal[
        "corrente",
        "poupanca",
        "investimento"
    ]

    valor_conta_atual: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    ativa: bool = True


class ContaBancariaResponse(BaseModel):
    id: int
    usuario_id: int
    nome_banco: str
    tipo_conta: Literal[
        "corrente",
        "poupanca",
        "investimento"
    ]
    valor_conta_atual: Decimal
    ativa: bool
    criado_em: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ContaBancariaUpdate(InputModel):
    nome_banco: str = Field(min_length=2, max_length=100)
    tipo_conta: Literal["corrente", "poupanca", "investimento"]
    ativa: bool


# =========================================================
# FLUXO DE DINHEIRO
# =========================================================


class FluxoDinheiroCreate(InputModel):
    conta_bancaria_id: int
    conta_destino_id: Optional[int] = None

    descricao: str = Field(
        min_length=1,
        max_length=200
    )

    valor: Decimal = Field(max_digits=12, decimal_places=2)

    tipo: Literal[
        "entrada",
        "saida",
        "transferencia",
        "ajuste",
    ]

    categoria: CategoriaMovimentacaoInput

    data_movimentacao: date

    observacao: Optional[str] = Field(
        default=None,
        max_length=255
    )

    @field_validator("categoria", mode="before")
    @classmethod
    def normalizar_categoria(cls, valor: str) -> str:
        if not isinstance(valor, str):
            return valor
        return _normalizar_categoria(valor)

    @model_validator(mode="after")
    def validar_movimentacao(self):
        if self.tipo == "transferencia":
            if self.categoria != "transferencia":
                raise ValueError(
                    "Transferências devem usar a categoria transferencia."
                )
            if self.conta_destino_id is None:
                raise ValueError(
                    "conta_destino_id é obrigatória para transferências."
                )
            if self.conta_destino_id == self.conta_bancaria_id:
                raise ValueError(
                    "A conta de origem e destino devem ser diferentes."
                )
        elif self.conta_destino_id is not None:
            raise ValueError(
                "conta_destino_id só pode ser usada em transferências."
            )
        elif self.categoria == "transferencia":
            raise ValueError(
                "A categoria transferencia é reservada para transferências."
            )

        if self.tipo == "ajuste":
            if self.categoria != "ajuste":
                raise ValueError("Ajustes devem usar a categoria ajuste.")
            if self.valor == 0:
                raise ValueError("O valor do ajuste não pode ser zero.")
        elif self.valor <= 0:
            raise ValueError("O valor da movimentação deve ser maior que zero.")

        if self.categoria == "ajuste" and self.tipo != "ajuste":
            raise ValueError("A categoria ajuste é reservada para ajustes.")
        return self


class FluxoDinheiroUpdate(InputModel):
    conta_bancaria_id: int
    descricao: str = Field(min_length=1, max_length=200)
    valor: Decimal = Field(max_digits=12, decimal_places=2)
    tipo: Literal["entrada", "saida", "ajuste"]
    categoria: CategoriaMovimentacaoInput
    data_movimentacao: date
    observacao: Optional[str] = Field(default=None, max_length=255)

    @field_validator("categoria", mode="before")
    @classmethod
    def normalizar_categoria(cls, valor: str) -> str:
        if not isinstance(valor, str):
            return valor
        return _normalizar_categoria(valor)

    @model_validator(mode="after")
    def validar_movimentacao(self):
        if self.tipo == "ajuste":
            if self.categoria != "ajuste":
                raise ValueError("Ajustes devem usar a categoria ajuste.")
            if self.valor == 0:
                raise ValueError("O valor do ajuste não pode ser zero.")
        else:
            if self.valor <= 0:
                raise ValueError("O valor da movimentação deve ser maior que zero.")
            if self.categoria in {"transferencia", "ajuste"}:
                raise ValueError(
                    "A categoria informada é reservada para outro tipo "
                    "de movimentação."
                )
        return self


class FluxoDinheiroResponse(BaseModel):
    id: int
    conta_bancaria_id: int
    descricao: str
    valor: Decimal
    tipo: Literal[
        "entrada",
        "saida",
        "transferencia",
        "ajuste",
    ]
    categoria: str
    data_movimentacao: date
    observacao: Optional[str]
    transferencia_id: Optional[str]
    transferencia_direcao: Optional[Literal["origem", "destino"]]
    conta_destino_id: Optional[int]

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# CÁLCULOS FINANCEIROS
# =========================================================


class CalculoFinanceiroCreate(InputModel):
    """
    Dados informados pelo usuário para solicitar
    um cálculo financeiro.

    Os valores financeiros NÃO são informados aqui.
    Eles são calculados automaticamente pelo sistema.
    """

    conta_bancaria_id: int

    tipo_calculo: Literal[
        "diario",
        "semanal",
        "mensal",
        "anual"
    ]

    data_inicio: date
    data_fim: date

    @model_validator(mode="after")
    def validar_periodo_tipo(self):
        if self.data_fim < self.data_inicio:
            raise ValueError("A data final não pode ser anterior à inicial.")

        dias = (self.data_fim - self.data_inicio).days + 1

        if self.tipo_calculo == "diario" and dias != 1:
            raise ValueError("Um cálculo diário deve abranger exatamente um dia.")

        if self.tipo_calculo == "semanal" and dias != 7:
            raise ValueError("Um cálculo semanal deve abranger exatamente sete dias.")

        if self.tipo_calculo == "mensal":
            ultimo_dia = calendar.monthrange(
                self.data_inicio.year,
                self.data_inicio.month
            )[1]
            if (
                self.data_inicio.day != 1
                or self.data_fim.year != self.data_inicio.year
                or self.data_fim.month != self.data_inicio.month
                or self.data_fim.day != ultimo_dia
            ):
                raise ValueError(
                    "Um cálculo mensal deve abranger um mês-calendário completo."
                )

        if self.tipo_calculo == "anual" and (
            self.data_inicio.month != 1
            or self.data_inicio.day != 1
            or self.data_fim.year != self.data_inicio.year
            or self.data_fim.month != 12
            or self.data_fim.day != 31
        ):
            raise ValueError(
                "Um cálculo anual deve abranger um ano-calendário completo."
            )

        return self


class CalculoFinanceiroResponse(BaseModel):
    """
    Resultado calculado automaticamente pelo sistema.
    """

    id: int
    conta_bancaria_id: int

    tipo_calculo: Literal[
        "diario",
        "semanal",
        "mensal",
        "anual"
    ]

    data_inicio: date
    data_fim: date

    # -----------------------------------------------------
    # VALORES CALCULADOS PELO SISTEMA
    # -----------------------------------------------------

    valor_original: Decimal
    total_entradas: Decimal
    total_saidas: Decimal
    total_investimentos: Decimal
    total_transferencias_recebidas: Decimal
    total_transferencias_enviadas: Decimal
    total_ajustes: Decimal
    valor_final: Decimal

    criado_em: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# METAS FINANCEIRAS
# =========================================================


class MetaFinanceiraCreate(InputModel):

    nome: str = Field(
        min_length=1,
        max_length=150
    )

    valor_meta: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    valor_atual: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    data_inicio: date
    data_limite: Optional[date] = None

    status: Literal[
        "em_andamento",
        "concluida",
        "cancelada"
    ] = "em_andamento"

    descricao: Optional[str] = Field(
        default=None,
        max_length=255
    )

    # -----------------------------------------------------
    # VALIDAR DATA LIMITE
    # -----------------------------------------------------

    @field_validator("data_limite")
    @classmethod
    def validar_data_limite(
        cls,
        data_limite,
        info
    ):

        data_inicio = info.data.get(
            "data_inicio"
        )

        if (
            data_limite
            and data_inicio
            and data_limite < data_inicio
        ):
            raise ValueError(
                "A data limite não pode ser anterior à data de início."
            )

        return data_limite


class MetaFinanceiraResponse(BaseModel):
    id: int
    usuario_id: int
    nome: str
    valor_meta: Decimal
    valor_atual: Decimal
    data_inicio: date
    data_limite: Optional[date]

    status: Literal[
        "em_andamento",
        "concluida",
        "cancelada"
    ]

    descricao: Optional[str]
    criado_em: datetime

    @computed_field
    @property
    def progresso_percentual(self) -> Decimal:
        return (
            self.valor_atual
            * Decimal("100")
            / self.valor_meta
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @computed_field
    @property
    def valor_restante(self) -> Decimal:
        return max(Decimal("0.00"), self.valor_meta - self.valor_atual)

    model_config = ConfigDict(
        from_attributes=True
    )



class ResumoPeriodoResponse(BaseModel):
    """
    Resumo financeiro consolidado para qualquer intervalo customizado de datas.
    """

    conta_bancaria_id: Optional[int] = None
    data_inicio: date
    data_fim: date
    saldo_inicial: Decimal
    total_entradas: Decimal
    total_saidas: Decimal
    total_investimentos: Decimal
    total_transferencias_recebidas: Decimal
    total_transferencias_enviadas: Decimal
    total_ajustes: Decimal
    saldo_final: Decimal
