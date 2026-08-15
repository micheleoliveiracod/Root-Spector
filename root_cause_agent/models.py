"""Schemas Pydantic do agente. Ver specs/design.md para o desenho completo."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

__all__ = [
    "Classification",
    "RiskPrediction",
    "MetricaSensor",
    "NaoConformidade",
    "RespostaIshikawa",
    "PorQue",
    "CategoriaAnalise",
    "CategoriaDescartada",
    "CicloAnterior",
    "Diagnostico",
]


class Classification(StrEnum):
    """Derivada de compliance_score em preparar_contexto -- não é uma
    coluna do banco (o BiotecPredict a calcula sob demanda na API), ver
    ComplianceService._classify_score()."""

    ACCEPTABLE = "ACCEPTABLE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RiskPrediction(StrEnum):
    """Persistida em batches.risk_prediction -- saída do modelo de ML do
    BiotecPredict, sinal independente de compliance_score."""

    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"


class MetricaSensor(BaseModel):
    """Estatísticas agregadas de um parâmetro de biosensor para o lote,
    replicando get_sensor_metrics() do BiotecPredict."""

    parametro: str
    media: float
    minimo: float
    maximo: float
    unidade: str
    dentro_da_faixa: bool


class NaoConformidade(BaseModel):
    """Entrada validada do agente: uma linha de `batches` (schema real do
    BiotecPredict) mais o contexto calculado deterministicamente em
    preparar_contexto."""

    batch_id: int
    upload_date: datetime
    compliance_score: float
    classification: Classification
    risk_prediction: RiskPrediction
    sensor_metrics: dict[str, MetricaSensor]
    parametros_fora_da_faixa: list[str]


class RespostaIshikawa(BaseModel):
    """Uma iteração do mapeamento Ishikawa (Fase 1).

    `tentativas` guarda todas as respostas que passaram na validação
    determinística (Camada 1, ver avaliar_informatividade em
    specs/design.md), na ordem dada -- normalmente 1 item, 2 quando a
    1ª tentativa foi julgada não informativa e o operador teve uma
    segunda chance. `resposta` espelha a última tentativa (a aceita como
    final), para código que só lê esse campo. `informativa` é False
    apenas quando as 2 tentativas foram julgadas não informativas e a
    investigação seguiu mesmo assim."""

    categoria: str
    pergunta: str
    resposta: str
    tentativas: list[str] = Field(default_factory=list)
    informativa: bool = True
    evidencia: str | None = None


class PorQue(BaseModel):
    """Uma iteração do método 5 Porquês (Fase 2), ancorada em
    categoria_principal. Ver RespostaIshikawa para o significado de
    `tentativas`/`informativa` -- mesma regra de validação em duas
    camadas, reusada nas duas fases."""

    numero: int = Field(ge=1, le=5)
    pergunta: str
    resposta: str
    tentativas: list[str] = Field(default_factory=list)
    informativa: bool = True
    evidencia: str | None = None


class CategoriaAnalise(BaseModel):
    """Saída de orquestrar_analise: a categoria identificada como mais
    provável, com a justificativa do LLM."""

    categoria: str
    justificativa: str


class CategoriaDescartada(BaseModel):
    categoria: str
    motivo: str


class CicloAnterior(BaseModel):
    """Um ciclo de investigação anterior, arquivado quando o operador pede
    ajuste -- preservado para auditoria, nunca sobrescrito (a mudança de
    respostas entre ciclos pode ser relevante)."""

    numero_ciclo: int
    respostas_ishikawa: list[RespostaIshikawa]
    categoria_principal: CategoriaAnalise
    categorias_descartadas: list[CategoriaDescartada]
    cadeia_de_porques: list[PorQue]
    causa_raiz: str
    encerrado_em: datetime


class Diagnostico(BaseModel):
    """Saída estruturada final -- o que gerar_causa_raiz produz, valida e
    salva (JSON + HTML) em reports/."""

    nc: NaoConformidade
    respostas_ishikawa: list[RespostaIshikawa]
    categoria_principal: CategoriaAnalise
    categorias_descartadas: list[CategoriaDescartada]
    cadeia_de_porques: list[PorQue]
    causa_raiz: str
    narrativa: str
    ciclos_anteriores: list[CicloAnterior] = Field(default_factory=list)
    gerado_em: datetime
