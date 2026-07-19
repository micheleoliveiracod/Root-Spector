"""Provedor de LLM fake, determinístico -- ativado só quando
`LLM_PROVIDER=fake` (ver config.py::get_llm()). Usado pela suíte E2E
(tests/e2e/, local e CI) e pelos testes automatizados, pra rodar o fluxo
completo sem depender de rede nem de uma chave de API real -- nunca é o
padrão, só entra em cena se explicitamente configurado.
"""

from __future__ import annotations

from typing import get_origin

from langchain_core.messages import AIMessage
from pydantic import BaseModel

RESPOSTA_FAKE = "Pergunta gerada pelo LLM fake (LLM_PROVIDER=fake)?"


def _valor_dummy(annotation):
    origin = get_origin(annotation)
    if origin is list:
        return []
    if annotation is bool:
        return True
    if annotation is str:
        return "resposta gerada pelo LLM fake (LLM_PROVIDER=fake)"
    if annotation is int:
        return 1
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _instancia_dummy(annotation)
    return None


def _instancia_dummy(schema: type[BaseModel]) -> BaseModel:
    valores = {nome: _valor_dummy(campo.annotation) for nome, campo in schema.model_fields.items()}
    return schema(**valores)


class _FakeBound:
    def invoke(self, mensagens):
        return AIMessage(content=RESPOSTA_FAKE)


class _FakeStructured:
    def __init__(self, schema: type[BaseModel]):
        self.schema = schema

    def invoke(self, mensagens):
        return _instancia_dummy(self.schema)


class FakeChatModel:
    """Substitui um ChatModel real -- suporta a mesma interface usada em
    nodes.py (bind_tools/with_structured_output/invoke), sempre com
    respostas determinísticas e sem nunca chamar rede."""

    def bind_tools(self, tools):
        return _FakeBound()

    def with_structured_output(self, schema: type[BaseModel]):
        return _FakeStructured(schema)

    def invoke(self, mensagens):
        return AIMessage(content=RESPOSTA_FAKE)

    def with_fallbacks(self, fallbacks):
        return self
