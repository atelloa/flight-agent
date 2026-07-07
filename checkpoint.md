# Checkpoint: Flight Agent MVP

**Fecha:** 2026-07-06  
**Proyecto:** `flight-agent`  
**Repo GitHub:** `atelloa/flight-agent`  
**Archivo de continuidad:** `checkpoint.md` en la raíz del repo.

Este archivo existe para retomar el laboratorio en otro chat sin volver a explicar todo el contexto.

---

## Objetivo del laboratorio

Aprender **arquitectura y diseño de agentes IA** usando un proyecto real y pequeño como laboratorio.

El objetivo no es agregar features sin control. El objetivo es entender, paso a paso, cómo se diseñan piezas como:

```text
state
nodes
tools
persistence
routing
observability
resilience
auditability
backend API
frontend / UI
human-in-the-loop
jobs
scheduler
worker
operación
```

Reglas de trabajo:

```text
Un paso por vez.
Explicar qué hacer, por qué se hace y cómo validar.
No avanzar hasta que el usuario diga "siguiente".
Evitar sobrearquitectura.
No quedarse afinando infinitamente un punto si el concepto arquitectónico ya quedó claro.
Separar claramente arquitectura de implementación.
Primero entender la decisión de diseño; después escribir código.
```

---

## Arquitectura actual

El proyecto es un agente de monitoreo de vuelos con Python, LangGraph y un patrón híbrido:

```text
Pipeline determinístico + intervención agentic acotada
```

No es un agente totalmente autónomo.

Flujo principal del agente:

```text
load_config
  -> fetch_flights
  -> store_snapshot
  -> evaluate_rules
  -> decision_router
  -> claude_analysis
  -> store_decisions
  -> send_alert
  -> END
```

Arquitectura actual de la app:

```text
Usuario -> Frontend estático -> API FastAPI -> SQLite

main.py -> agente LangGraph -> SQLite
```

Regla principal:

```text
El frontend no lee SQLite.
El frontend consume API HTTP.
La API consulta SQLite.
La API no ejecuta el agente todavía.
```

---

## Configuración segura actual

En `config/routes.yaml`, el modo seguro de laboratorio es:

```yaml
global:
  review_mode: true
  fetch_mode: "cached"
  claude_mode: "mock"
  telegram_enabled: false
```

Significado:

| Config | Modo real | Modo seguro |
|---|---|---|
| `fetch_mode` | `live` llama SerpAPI | `cached` lee SQLite |
| `claude_mode` | `live` llama Claude | `mock` simula Claude |
| `telegram_enabled` | `true` envía Telegram | `false` no envía |

Regla actual:

```text
Para aprender y probar arquitectura, usar cached + mock + Telegram apagado.
```

---

## Estado del laboratorio

| Fase | Estado | Resultado |
|---|---|---|
| Phase 1 | COMPLETA | MVP local con consola |
| Phase 2 | COMPLETA | Persistencia SQLite |
| Phase 3 | COMPLETA | Alertas por Telegram |
| Phase 4 | COMPLETA | Review queue manual |
| Phase 5 | COMPLETA | Claude analiza casos ambiguos |
| Phase 6 | COMPLETA / SUFICIENTE | Observabilidad, auditoría y resiliencia básica |
| Phase 7 | COMPLETA / SUFICIENTE | Backend API read-only con FastAPI |
| Phase 8 | COMPLETA / SUFICIENTE | Frontend mínimo consumiendo API |
| Phase 9 | PLANIFICADA / OPCIONAL | Human-in-the-loop operativo |
| Phase 10 | SIGUIENTE RECOMENDADA | Ejecución del agente por API |
| Phase 11 | PLANIFICADA | Jobs, scheduler y worker |
| Phase 12 | PLANIFICADA | Seguridad, despliegue y operación |

Decisión actual:

```text
Phase 8 se cierra como suficiente.
No se implementa review_queue en la UI por ahora porque no suma funcionalmente ni aporta un concepto arquitectónico nuevo en este momento.
La siguiente fase recomendada es Phase 10, antes que Phase 9, porque aporta más a convertir el laboratorio en una app operable.
```

---

## Archivos principales

```text
checkpoint.md
main.py
api.py
frontend/index.html
frontend/run.html
config/routes.yaml
src/flight_agent/state.py
src/flight_agent/graph.py
src/flight_agent/nodes/load_config.py
src/flight_agent/nodes/fetch_flights.py
src/flight_agent/nodes/claude_analysis.py
src/flight_agent/nodes/nodes.py
src/flight_agent/tools/claude_tool.py
src/flight_agent/tools/telegram_tool.py
src/flight_agent/persistence/db.py
src/flight_agent/observability/logging.py
src/flight_agent/catalogs/airlines.py
data/flight_agent.sqlite
```

Nota: `api.py` quedó en la raíz por simplicidad didáctica del laboratorio. Si crece, se puede mover a:

```text
src/flight_agent/api/main.py
src/flight_agent/api/routes.py
```

No mover todavía si no hay necesidad.

---

# Conceptos arquitectónicos consolidados

## State

`FlightMonitorState` es el expediente vivo de una corrida.

Vive en RAM mientras corre:

```bash
python main.py
```

Cuando termina la ejecución, el `state` desaparece.

Ejemplos de datos en state:

```text
routes_config
global_config
latest_offers
rule_matches
suspicious_cases
alerts_to_send
run_id
errors
```

## Persistence

SQLite es la memoria permanente del sistema.

Guarda datos que deben sobrevivir entre ejecuciones:

```text
flights
decisions
review_queue
agent_runs
```

`db.py` no es una tool agentic. Es un adapter simple de persistencia SQLite.

## Nodes

Regla mental:

```text
Node = recibe state, hace una responsabilidad, devuelve state
```

Ejemplos:

```text
load_config
fetch_flights
store_snapshot
evaluate_rules
decision_router
claude_analysis
store_decisions
send_alert
```

## Tools vs Persistence

Separación conceptual:

```text
tools/
  capacidades externas del agente
  ejemplo: Claude, SerpAPI, Telegram

persistence/
  memoria permanente del sistema
  ejemplo: SQLite, snapshots, historial, review queue
```

## Observability

Observabilidad es una preocupación transversal.

Por eso vive en:

```text
src/flight_agent/observability/
```

No debe mezclarse innecesariamente dentro de tools ni persistence.

## Catalogs

Los catálogos son metadata referencial del dominio.

Ejemplo actual:

```text
src/flight_agent/catalogs/airlines.py
```

Responsabilidad:

```text
Clasificar aerolíneas de manera referencial.
No consulta internet en runtime.
No modifica SQLite.
No ejecuta lógica del agente.
```

---

# Phase 6 — Observabilidad, auditoría y resiliencia básica

**Estado general:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Implementado y validado:

```text
run_id único por ejecución.
Logs básicos por node.
Tabla agent_runs en SQLite.
Resumen de ejecución en agent_runs.
Errores no fatales en state.errors.
Conteo recoverable_errors_count en agent_runs.
decisions.run_id.
review_queue.run_id.
review_queue se guarda aunque Telegram esté apagado.
```

Decisión:

```text
Node Events queda diferido.
Implementarlo ahora sería sobrearquitectura.
```

---

# Phase 7 — Arquitectura de Backend APIs

**Estado:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Objetivo aprendido:

```text
La API es una frontera limpia entre el agente y otros consumidores.
```

Arquitectura final de esta fase:

```text
main.py -> agente -> SQLite <- API <- cliente
```

Regla principal aprendida:

```text
Primero API read-only.
La API consulta SQLite.
El agente se sigue ejecutando por main.py.
```

Endpoints implementados:

```text
GET /health
GET /runs
GET /runs/{run_id}
GET /review-queue
GET /routes/{route_id}/cheapest-offers?window=1d|7d&limit=3
GET /offers/cheapest?window=1d|7d&limit=3
```

Después se extendió `/offers/cheapest` con:

```text
limit=X
unique_airline=true|false
```

Ejemplo:

```text
GET /offers/cheapest?window=7d&limit=5&unique_airline=true
```

Validación arquitectónica:

```text
La API no ejecuta main.py.
La API no ejecuta LangGraph.
La API no llama Claude.
La API no llama SerpAPI.
La API no envía Telegram.
La API consulta SQLite y enriquece respuestas.
```

---

# Phase 8 — Frontend / UI mínima consumiendo API

**Estado:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Objetivo de Phase 8:

```text
Entender frontend como capa consumidora de API, no como acceso directo a la base de datos.
```

Arquitectura validada:

```text
Usuario -> Frontend estático -> API FastAPI -> SQLite

main.py -> agente -> SQLite
```

Decisión importante:

```text
Aunque el checkpoint original proponía HTML servido por FastAPI,
se decidió usar frontend estático con Live Server para visualizar mejor la separación de capas.
```

Resultado:

```text
frontend/index.html
frontend/run.html
```

La UI actual permite:

```text
Ver estado de la API.
Ver últimas corridas.
Abrir detalle de una corrida.
Ver ofertas más baratas por tramo.
Elegir cantidad de ofertas por tramo.
Activar modo máximo 1 oferta por aerolínea.
Ver si la aerolínea es low-cost de forma referencial.
```

La UI no hace esto:

```text
No lee SQLite.
No ejecuta LangGraph.
No llama Claude.
No llama SerpAPI.
No envía Telegram.
No aprueba/rechaza review_queue.
No contiene lógica del agente.
```

La API hace esto:

```text
Valida parámetros.
Lee SQLite.
Aplica filtros de consulta.
Enriquece ofertas con catálogo de aerolíneas.
Devuelve JSON al frontend.
```

## Phase 8.8 — Review queue en UI

**Estado:** OMITIDA / DIFERIDA POR AHORA.

Decisión:

```text
No se agrega review_queue a la UI en este momento.
Funcionalmente no suma ahora y arquitectónicamente no aporta un concepto nuevo.
```

Importante:

```text
review_queue sigue existiendo en backend y SQLite.
GET /review-queue sigue existiendo.
Solo se decidió no mostrarlo en la UI por ahora.
```

## Catálogo de aerolíneas

Se agregó catálogo referencial en:

```text
src/flight_agent/catalogs/airlines.py
```

Responsabilidad:

```text
AIRLINE_CATALOG
normalize_airline_name()
get_airline_metadata()
enrich_offer_with_airline_metadata()
```

La API devuelve por oferta:

```text
is_low_cost
airline_type
airline_type_source
```

Limitación aceptada:

```text
Es referencial.
No garantiza equipaje incluido.
No consulta una fuente externa automáticamente.
No es una verdad absoluta.
```

Regla aprendida:

```text
Low-cost no significa necesariamente que no incluya maleta.
Tipo de aerolínea y condiciones tarifarias son conceptos diferentes.
```

## CORS

Se agregó CORS para permitir que Live Server consuma la API:

```text
http://127.0.0.1:5500
http://localhost:5500
```

Concepto aprendido:

```text
Origin = protocolo + host + puerto.
http://127.0.0.1:5500 y http://127.0.0.1:8000 son orígenes distintos.
El navegador exige CORS.
```

## Validación final de Phase 8

Frontera validada:

```text
Frontend:
  consumidor de API

API:
  capa de lectura y exposición HTTP

SQLite:
  persistencia

main.py / LangGraph:
  ejecución del agente

catalogs:
  conocimiento referencial del dominio
```

Con esto, Phase 8 queda cerrada como suficiente.

---

# Phase 9 — Human-in-the-loop operativo

**Estado:** PLANIFICADA / OPCIONAL.

Objetivo:

```text
Entender cómo una persona interviene decisiones del agente mediante API + UI.
```

Concepto:

```text
El agente genera casos ambiguos.
Los casos entran a review_queue.
Un humano revisa y decide.
La decisión queda auditada.
```

Puntos posibles:

```text
GET /review-queue
POST /review-queue/{id}/approve
POST /review-queue/{id}/reject
Estados: pending, approved, rejected
Auditoría: quién revisó, cuándo, qué decidió
UI con botones de aprobar / rechazar
```

Nota:

```text
Esta fase ya no es read-only.
Aquí empieza el diseño de Command API.
```

Decisión actual:

```text
No avanzar a Phase 9 todavía si no suma funcionalmente.
```

---

# Phase 10 — Ejecución del agente por API

**Estado:** SIGUIENTE RECOMENDADA.

Objetivo:

```text
Entender cómo reemplazar parcialmente main.py sin meter lógica sucia dentro del endpoint.
```

Regla arquitectónica:

```text
No copiar todo main.py dentro de un endpoint FastAPI.
```

Arquitectura correcta:

```text
main.py -> AgentRunner -> LangGraph -> SQLite

API -> AgentRunner -> LangGraph -> SQLite
```

Arquitectura mala:

```text
API endpoint gigante -> toda la lógica de main.py pegada ahí
```

Puntos internos recomendados:

```text
10.1 Por qué no meter todo main.py dentro de FastAPI
10.2 Qué es un AgentRunner
10.3 Separar entrada CLI de entrada API
10.4 main.py usa AgentRunner
10.5 API usa AgentRunner
10.6 POST /runs para pedir una ejecución
10.7 Por qué una corrida debería ser un job
10.8 Estados: queued, running, completed, failed
10.9 GET /runs/{run_id} para consultar estado
10.10 Riesgos: doble ejecución, costos, duplicidad de alertas
```

Siguiente paso concreto recomendado:

```text
Phase 10.1 — Conceptualmente, qué significa ejecutar el agente desde API y por qué no se debe meter main.py dentro del endpoint.
```

---

# Phase 11 — Jobs, scheduler y worker

**Estado:** PLANIFICADA.

Objetivo:

```text
Entender ejecución automática y desacoplada.
```

Arquitectura conceptual:

```text
Scheduler -> Queue -> Worker -> AgentRunner -> SQLite
                         ^
API -> crea job ----------|
UI -> consulta API -> SQLite
```

No implementar todavía.

---

# Phase 12 — Seguridad, despliegue y operación

**Estado:** PLANIFICADA.

Objetivo:

```text
Entender qué cambia cuando el sistema deja de ser laboratorio local.
```

Temas futuros:

```text
Autenticación
Autorización
API keys / tokens
Rate limiting
API Gateway
Logs de API
Manejo de errores consistente
Variables de entorno
Docker
Deploy local vs cloud
Monitoreo básico
Nginx / reverse proxy
```

No implementar todavía.

---

## Mejoras futuras fuera del flujo inmediato

### Subgrafo condicional real

Actualmente `claude_analysis` está conectado después de `decision_router`, aunque internamente solo procesa ambiguos.

Más adelante se puede convertir en routing condicional real:

```text
si hay ambiguous -> claude_analysis
si no hay ambiguous -> store_decisions
```

No hacerlo todavía.

### Repositories

Si el proyecto crece, dividir `persistence/db.py` en:

```text
flight_repository.py
decision_repository.py
review_queue_repository.py
run_repository.py
sqlite.py
```

Por ahora se mantiene simple.

### Renombrar recoverable_errors_count

El nombre actual puede confundir.

Nombre conceptual más claro:

```text
non_fatal_errors_count
```

No cambiar ahora.

### Mover API a paquete interno

Posible estructura futura:

```text
src/flight_agent/api/main.py
src/flight_agent/api/routes.py
```

No mover todavía si no hay necesidad.

### Actualización automática del catálogo de aerolíneas

Posible fase futura:

```text
scripts/update_airline_catalog.py
GitHub Actions mensual
fuente pública o comercial
actualización referencial del catálogo
```

No hacerlo ahora.

---

## Reglas para el próximo chat

Cuando se retome este proyecto:

1. Leer primero este `checkpoint.md` desde GitHub.
2. Recordar que el objetivo es aprendizaje de arquitectura y diseño de agentes IA.
3. Mantener pasos pequeños.
4. No saltar a soluciones empresariales complejas antes de que el concepto esté claro.
5. No quedarse horas afinando una fase si el concepto ya quedó aprendido.
6. Phase 6 está cerrada.
7. Phase 7 está cerrada.
8. Phase 8 está cerrada como suficiente.
9. `review_queue` en UI quedó omitido/diferido por decisión consciente.
10. Continuar recomendado desde `Phase 10.1`.
11. Antes de programar Phase 10, explicar conceptualmente AgentRunner y por qué no copiar `main.py` dentro de FastAPI.
12. Mantener la dinámica: qué hacer, por qué se hace y cómo validar.
13. Para laboratorios técnicos, avanzar un paso por vez y esperar `siguiente`.
14. No implementar React, autenticación, scheduler, workers ni dashboard empresarial todavía.
