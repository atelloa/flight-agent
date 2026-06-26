# Checkpoint: Flight Agent MVP

**Fecha:** 2026-06-25
**Objetivo principal:** Aprender arquitectura de soluciones de agentes IA usando un proyecto real como laboratorio

---

## Conceptos arquitectónicos aprendidos hasta ahora

1. State (FlightMonitorState)
   El "expediente" compartido del agente. Vive en RAM durante la ejecución.
   No es el "estado" de un objeto (activo/inactivo), es la memoria completa del agente.

2. Nodes (load_config, fetch_flights, evaluate_rules, etc)
   Cada node es un ciclo ReAct: Think -> Act -> Observe.
   Cada node tiene una sola responsabilidad.
   Recibe el state, lo modifica, lo devuelve.

3. Tools (buscar_ruta, parsear_resultado, save_flights, etc)
   Acciones concretas que ejecutan los nodes.
   Regla: Nodes organizan el workflow. Tools hacen el trabajo.

4. LangGraph
   Orquestador del flujo. Conecta nodes con edges.
   No decide si un vuelo es bueno. Eso lo deciden las reglas y Claude.

5. ReAct Pattern
   Reason + Acting. Patrón de pensamiento del agente.
   Introducido por Princeton y Google en 2022.
   Usado por OpenAI, Anthropic, LangChain, etc.

6. Enterprise Agentic Workflow
   Patron elegido para este proyecto.
   Codigo monitorea. Reglas filtran. Claude interpreta. LangGraph orquesta. BD recuerda.

7. Persistencia y observabilidad
   Raw snapshot antes de evaluar (Event Sourcing).
   SQLite guarda vuelos y decisiones con timestamp.
   Permite auditar cada decision del agente.

8. Single source of truth
   Configuracion vive en config/routes.yaml.
   Ni state.py ni main.py tienen configuracion hardcodeada.

9. Bounded agentic subgraph
   Claude NO controla el flujo normal.
   Claude solo razona casos ambiguos (Phase 5).
   Evita costo, latencia y variabilidad innecesaria.

10. Capas del sistema completo
    Agent (nucleo) -> Notifications -> Backend API -> Frontend
    Cada capa aparece en una fase distinta.
    Backend API recien en Phase 7, no antes.

---

## Estado actual

Phase 1: COMPLETA
Phase 2: COMPLETA
Phase 3: COMPLETA
Phase 4: PENDIENTE
Phase 5: PENDIENTE
Phase 6: PENDIENTE
Phase 7: PENDIENTE

---

## Flujo implementado

load_config -> fetch_flights -> store_snapshot -> evaluate_rules -> decision_router -> store_decisions -> END

---

## Archivos creados

config/routes.yaml        fuente unica de configuracion
state.py                  Flight + FlightMonitorState
load_config.py            node 1: lee routes.yaml
fetch_flights.py          node 2: busca en SerpAPI
nodes.py                  nodes 3,4,5,6: evaluate_rules, decision_router, store_snapshot, store_decisions
graph.py                  LangGraph orquesta todo
main.py                   punto de entrada
db.py                     SQLite persistence
data/flight_agent.sqlite  base de datos

---

## Fases

Phase 1: COMPLETA - MVP local con consola
Phase 2: COMPLETA - Persistencia SQLite
Phase 3: COMPLETA - Real alerts (email o Telegram)
Phase 4: PENDIENTE - Manual review queue
Phase 5: PENDIENTE - LLM-assisted explanations (Claude subgraph)
Phase 6: PENDIENTE - Better logging and traces
Phase 7: PENDIENTE - User configuration interface (Frontend + Backend API)

---

## Proximos pasos detallados

Phase 3:
  Agregar node send_alert en nodes.py
  Enviar email o Telegram cuando decision_router encuentre clear_deal
  Registrar en SQLite que la alerta fue enviada

Phase 4:
  Guardar casos review en SQLite para revision humana
  Consultar casos pendientes de revision

Phase 5:
  Agregar subgrafo agentic con Claude
  Solo para casos ambiguos del decision_router
  Claude devuelve decision estructurada: {decision, confidence, reason, risk_flags}

Phase 6:
  Logging completo de cada ejecucion
  Trazabilidad por node
  Migracion a estructura src/flight_agent/

Phase 7:
  Backend API para recibir configuracion del usuario
  Frontend (Telegram Bot o Web App)
  Multi-usuario