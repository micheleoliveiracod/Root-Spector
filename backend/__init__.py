"""Camada web (FastAPI) do Root-Spector.

Depende de `root_cause_agent` como biblioteca (nunca o contrário) -- o
motor do agente não tem nenhuma dependência de FastAPI, permitindo reusá-lo
sem este pacote (ver `root_cause_agent/main.py`, o harness de teste).
"""
