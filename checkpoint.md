# Checkpoint: Flight Agent MVP

**Fecha:** 2026-07-05  
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
En Phase 8, aprender conceptos mientras se construye laboratorio, no teoría pura aislada.
```

---

## Arquitectura actual

El proyecto es un agente de monitoreo de vuelos con Python, LangGraph y un patrón híbrido:

```text
Pipeline determinístico + intervención agentic acotada
```

No es un agente totalmente autónomo.

Flujo principal:

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

Notas de diseño:

```text
claude_analysis está en el grafo, pero solo procesa casos ambiguous.
Si no hay ambiguos, no debería gastar Claude.
```

Esto se entiende como un **Bounded Agentic Workflow**:

```text
reglas determinísticas primero
Claude solo para ambigüedad
humano si hace falta revisión
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
| Phase 8 | SIGUIENTE | Frontend / UI mínima consumiendo API, con laboratorio práctico |
| Phase 9 | PLANIFICADA | Human-in-the-loop operativo |
| Phase 10 | PLANIFICADA | Ejecución del agente por API |
| Phase 11 | PLANIFICADA | Jobs, scheduler y worker |
| Phase 12 | PLANIFICADA | Seguridad, despliegue y operación |

---

## Archivos principales

```text
checkpoint.md
main.py
api.py
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
data/flight_agent.sqlite
```

Nota: `api.py` quedó en la raíz por simplicidad didáctica del laboratorio. No es necesariamente la estructura final ideal. Si crece, se puede mover a `src/flight_agent/api/main.py`.

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

---

# Phase 6 — Observabilidad, auditoría y resiliencia básica

**Estado general:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Regla aprendida:

```text
No todo print debe guardarse en SQLite.
La base no debe convertirse en un basurero de logs.
```

## Phase 6.1 — Run History / Audit Trail

**Estado:** COMPLETA.

Implementado y validado:

1. `run_id` único por ejecución en `main.py`.
2. Logs básicos por node con `src/flight_agent/observability/logging.py`.
3. `create_tables()` movido al inicio de `main.py`.
4. Tabla `agent_runs` en SQLite.
5. Función `save_agent_run()` en `src/flight_agent/persistence/db.py`.
6. `main.py` guarda una fila en `agent_runs` desde `finally`.
7. Se validó en SQLite Viewer que `agent_runs` tiene registros.

Campos relevantes de `agent_runs`:

```text
run_id
started_at
finished_at
status
duration_seconds
fetch_mode
claude_mode
telegram_enabled
flights_found
alerts_generated
error_message
recoverable_errors_count
```

## Phase 6.2 — Errores básicos / resiliencia

**Estado:** COMPLETA / SUFICIENTE.

Concepto aprendido:

```text
Error fatal
  -> rompe la ejecución
  -> main.py lo captura como failed
  -> se guarda en agent_runs.error_message

Error no fatal
  -> ocurre dentro de un node
  -> el node lo captura localmente
  -> se agrega a state.errors
  -> el agente puede continuar
```

Implementado y validado:

1. Se agregó en `FlightMonitorState`:

```python
errors: List[Dict] = field(default_factory=list)
```

2. En `send_alert`, un fallo de Telegram se captura localmente con `try/except`.
3. El error se agrega a `state.errors`.
4. `main.py` muestra el conteo de errores al final.
5. Se validó con simulación controlada de Telegram caído.
6. La simulación fue retirada después de la prueba.

## Phase 6.3 — Resumen mínimo de errores no fatales

**Estado:** COMPLETA / SUFICIENTE.

Implementado y validado:

1. Se agregó columna en `agent_runs`:

```text
recoverable_errors_count
```

2. Se agregó helper en `db.py`:

```python
column_exists(conn, table_name, column_name)
```

3. `save_agent_run()` recibe `recoverable_errors_count`.
4. `main.py` calcula el conteo desde `result["errors"]` si hay resultado final.
5. Se decidió dejar lógica defensiva para fallback con `state.errors` si no hay `result`.
6. Se validó que SQLite guarda el conteo.

Limitación aceptada:

```text
No se guarda el detalle de cada error no fatal.
Solo se guarda el conteo.
Eso es suficiente para este nivel del laboratorio.
```

## Phase 6.4 — Decision Audit

**Estado:** COMPLETA / SUFICIENTE.

Implementado y validado:

1. Se agregó columna en `decisions`:

```text
run_id
```

2. Se actualizó `save_decisions()` para recibir `run_id`.
3. Se corrigió `INSERT INTO decisions` para usar columnas explícitas.
4. `store_decisions()` llama a:

```python
save_decisions(state.alerts_to_send, now, state.run_id)
```

5. Se validó que las nuevas filas de `decisions` tienen `run_id`.

Buena práctica aprendida:

```text
Evitar INSERT INTO tabla VALUES (...)
Preferir INSERT INTO tabla (col1, col2, ...) VALUES (...)
```

## Phase 6.5 — Review Queue Observability

**Estado:** COMPLETA / SUFICIENTE.

Implementado y validado:

1. Se agregó columna en `review_queue`:

```text
run_id
```

2. Se actualizó `save_review_queue()` para recibir `run_id`.
3. Se actualizó `send_alert()` para llamar:

```python
save_review_queue(reviews, datetime.now(), state.run_id)
```

4. Se validó que las nuevas filas de `review_queue` tienen `run_id`.

Corrección arquitectónica importante:

```text
Antes:
telegram_enabled = false
  -> send_alert retornaba temprano
  -> no se guardaba review_queue

Ahora:
review_queue se guarda aunque Telegram esté apagado.
Telegram solo controla el envío externo.
```

Regla aprendida:

```text
review_mode controla revisión humana.
telegram_enabled controla notificación externa.
No deben estar acoplados.
```

## Phase 6.6 — Node Events

**Estado:** DIFERIDO.

No implementarlo ahora.

Decisión:

```text
No hace falta para el objetivo actual.
Ya se entendieron las piezas principales de observabilidad.
Implementarlo ahora sería sobrearquitectura.
```

Con esto, Phase 6 queda cerrada para el laboratorio.

---

# Phase 7 — Arquitectura de Backend APIs

**Estado:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Objetivo de Phase 7:

```text
Entender cómo una API se vuelve una frontera limpia entre el agente y otros consumidores.
```

Resultado final de Phase 7:

```text
main.py ejecuta el agente.
SQLite guarda resultados.
FastAPI consulta SQLite.
La API no ejecuta el agente todavía.
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

Motivo:

```text
Separar ejecución del agente de consulta de resultados.
Eso mantiene simple el diseño y evita mezclar orquestación con visualización.
```

## Conceptos aprendidos en Phase 7

```text
7.1 API como frontera arquitectónica / boundary
7.2 Request, response, endpoint, recurso y contrato
7.3 Métodos HTTP: GET, POST, PUT/PATCH, DELETE
7.4 Status codes: 200, 201, 400, 404, 500
7.5 Query API vs Command API
7.6 API síncrona vs API asíncrona / Job API
7.7 API interna vs API externa
7.8 API Gateway: qué es, cuándo aparece y por qué NO implementarlo ahora
7.9 Qué debe exponer flight-agent
7.10 Qué NO debe exponer flight-agent
7.11 Diseño de endpoints read-only
7.12 Qué es FastAPI y por qué usarlo como herramienta
7.13 Implementación mínima con FastAPI
7.14 Validación con navegador, Swagger y errores HTTP
```

## Endpoints implementados en Phase 7

```text
GET /health
GET /runs
GET /runs/{run_id}
GET /review-queue
GET /routes/{route_id}/cheapest-offers?window=1d|7d&limit=3
GET /offers/cheapest?window=1d|7d&limit=3
```

## Funciones de persistencia agregadas en `db.py`

```text
get_agent_runs()
get_agent_run(run_id)
get_cheapest_offers(route, window_days, limit)
get_cheapest_offers_for_all_routes(window_days, limit)
```

Ya existía y se reutilizó:

```text
get_review_queue()
```

## Archivo `api.py`

Se creó `api.py` en la raíz del proyecto para exponer la API FastAPI.

Responsabilidad:

```text
api.py
  -> recibe requests HTTP
  -> llama funciones de lectura en db.py
  -> devuelve JSON
```

No debe hacer esto en Phase 7:

```text
ejecutar main.py
ejecutar LangGraph
llamar Claude
llamar SerpAPI
enviar Telegram
modificar configuración
aprobar/rechazar review_queue
```

## Comando usado para levantar API en desarrollo

```bash
uvicorn api:app --reload
```

Significado:

```text
api
  -> archivo api.py

app
  -> variable app = FastAPI(...)

--reload
  -> reinicia automáticamente cuando cambian archivos Python
```

Uvicorn es el servidor ASGI que escucha HTTP y ejecuta la app FastAPI.

## Decisiones importantes de diseño

### `api.py` en raíz

Decisión actual:

```text
Dejar api.py en la raíz por simplicidad didáctica.
```

No es necesariamente la estructura final más limpia.

Posible estructura futura:

```text
src/flight_agent/api/main.py
src/flight_agent/api/routes.py
```

No mover todavía si no hay necesidad.

### API read-only

La API inicial solo consulta.

Sí expone:

```text
GET /health
GET /runs
GET /runs/{run_id}
GET /review-queue
GET /routes/{route_id}/cheapest-offers
GET /offers/cheapest
```

No expone todavía:

```text
POST /runs
POST /fetch-flights
POST /send-alert
POST /claude-analysis
POST /review-queue/{id}/approve
POST /review-queue/{id}/reject
PUT /config
```

Motivo:

```text
Eso ya introduce comandos, ejecución, efectos secundarios o cambios de configuración.
Primero aprender API como capa de consulta.
```

### Endpoint por ruta vs endpoint general

Se dejaron dos tipos de consulta:

```text
GET /routes/{route_id}/cheapest-offers
```

Para consultar una ruta específica.

```text
GET /offers/cheapest
```

Para consultar los top N vuelos más baratos por todos los tramos.

Regla aprendida:

```text
La URL debe expresar la pregunta que el cliente quiere hacerle al sistema.
```

## Validación Phase 7.14

Validado localmente por el usuario:

```text
GET /health funcionó.
GET /runs funcionó.
GET /runs/{run_id} funcionó.
GET /review-queue funcionó.
GET /routes/{route_id}/cheapest-offers funcionó.
GET /offers/cheapest funcionó para todos los tramos.
```

Checklist de validación final:

```text
/health responde 200 y {"status": "ok"}.
/runs responde lista de corridas.
/runs/{run_id} responde una corrida si existe.
/runs/{run_id} responde 404 si no existe.
/review-queue responde lista de casos pendientes o [].
/routes/{route_id}/cheapest-offers responde top por ruta.
/offers/cheapest responde top por todos los tramos.
window inválido debe responder 400.
limit inválido debe responder 400.
```

Validación arquitectónica final:

```text
La API no ejecuta main.py.
La API no ejecuta LangGraph.
La API no llama Claude.
La API no llama SerpAPI.
La API no envía Telegram.
La API solo consulta SQLite.
```

Con esto, Phase 7 queda cerrada para el laboratorio.

---

# Phase 8 — Frontend / UI mínima consumiendo API

**Estado:** SIGUIENTE.

Objetivo de Phase 8:

```text
Entender frontend como capa consumidora de API, no como acceso directo a la base de datos.
```

Arquitectura objetivo:

```text
Usuario -> Frontend -> API -> SQLite

main.py -> agente -> SQLite
```

Regla principal:

```text
El frontend no debe leer SQLite directamente.
Debe consumir la API.
```

Motivo:

```text
La API protege al frontend de los detalles internos.
Si mañana SQLite cambia por Postgres, la UI no debería romperse por eso.
```

## Enfoque didáctico de Phase 8

No hacer teoría pura aislada.

Cada punto debe trabajarse así:

```text
concepto mínimo
cambio pequeño en laboratorio
validación visible en navegador
```

No construir un dashboard empresarial.

No meter React todavía salvo decisión explícita posterior.

Usar una opción mínima local y didáctica.

Opción recomendada inicial:

```text
HTML simple servido por FastAPI
```

Motivo:

```text
Permite aprender frontend como consumidor de API sin meter toolchain de React, build, npm, estados complejos ni autenticación.
```

## Puntos internos de Phase 8 como laboratorio

```text
8.1 Diseñar la UI mínima: qué pantallas necesita flight-agent
    Laboratorio: dibujar/definir 3 secciones visibles.

8.2 Crear una página HTML mínima servida desde FastAPI
    Laboratorio: GET /dashboard devuelve HTML simple.

8.3 Entender frontend vs backend vs API con algo visible
    Laboratorio: el HTML carga en navegador, pero todavía sin datos.

8.4 Consumir GET /health desde la UI
    Laboratorio: mostrar "API OK" o "API error".

8.5 Consumir GET /runs desde la UI
    Laboratorio: renderizar tabla de corridas.

8.6 Manejar estados loading, empty, error y success
    Laboratorio: mostrar mensajes simples para cada estado.

8.7 Consumir GET /runs/{run_id}
    Laboratorio: al seleccionar una corrida, mostrar detalle.

8.8 Consumir GET /review-queue
    Laboratorio: renderizar tabla de casos pendientes.

8.9 Consumir GET /offers/cheapest
    Laboratorio: mostrar top 3 por tramo.

8.10 Orden visual mínimo
    Laboratorio: separar secciones: Runs, Review Queue, Cheapest Offers.

8.11 Validar frontera arquitectónica
    Laboratorio: confirmar que la UI llama endpoints HTTP y no SQLite.

8.12 Cierre de Phase 8
    Laboratorio: checklist final y actualización de checkpoint.md.
```

## Qué NO hacer en Phase 8

```text
No React todavía.
No autenticación todavía.
No frontend público.
No dashboard empresarial.
No diseño visual complejo.
No leer SQLite desde JavaScript.
No meter lógica del agente en frontend.
No aprobar/rechazar review_queue todavía.
```

Eso queda para Phase 9.

---

# Phase 9 — Human-in-the-loop operativo

**Estado:** PLANIFICADA.

Objetivo de Phase 9:

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

Puntos internos:

```text
9.1 Qué significa human-in-the-loop
9.2 Qué es una review queue
9.3 Diferencia entre consultar casos y resolver casos
9.4 GET /review-queue
9.5 POST /review-queue/{id}/approve
9.6 POST /review-queue/{id}/reject
9.7 Estados de revisión: pending, approved, rejected
9.8 Auditoría: quién revisó, cuándo, qué decidió
9.9 UI con botones de aprobar / rechazar
9.10 Validar que una acción humana cambia estado
```

Nota:

```text
Esta fase ya no es read-only.
Aquí empieza el diseño de Command API.
```

---

# Phase 10 — Ejecución del agente por API

**Estado:** PLANIFICADA.

Objetivo de Phase 10:

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

Puntos internos:

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

---

# Phase 11 — Jobs, scheduler y worker

**Estado:** PLANIFICADA.

Objetivo de Phase 11:

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

Puntos internos:

```text
11.1 Qué es un scheduler
11.2 Qué es un worker
11.3 Qué es una cola
11.4 Diferencia entre request web y proceso largo
11.5 Por qué no ejecutar procesos largos dentro del request
11.6 Scheduler dispara jobs
11.7 Worker ejecuta jobs
11.8 API consulta estado
11.9 UI muestra progreso
11.10 Cuándo esto sí vale la pena y cuándo es sobrearquitectura
```

---

# Phase 12 — Seguridad, despliegue y operación

**Estado:** PLANIFICADA.

Objetivo de Phase 12:

```text
Entender qué cambia cuando el sistema deja de ser laboratorio local.
```

Puntos internos:

```text
12.1 Autenticación
12.2 Autorización
12.3 API keys / tokens
12.4 Rate limiting
12.5 API Gateway en arquitectura real
12.6 Logs de API
12.7 Manejo de errores consistente
12.8 Variables de entorno
12.9 Docker
12.10 Deploy local vs cloud
12.11 Monitoreo básico
```

Nota:

```text
Seguridad se menciona porque aparece al hablar de APIs internas/externas.
Pero no es parte inmediata de Phase 8.
Queda como fase futura.
```

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

No cambiar ahora para no perder tiempo en refactorización.
Solo tenerlo en cuenta para una limpieza futura.

### Mover API a paquete interno

Posible estructura futura:

```text
src/flight_agent/api/main.py
src/flight_agent/api/routes.py
```

No mover todavía si el objetivo es aprender Phase 8 con el menor ruido posible.

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
8. Continuar desde `Phase 8.1 — Diseñar la UI mínima: qué pantallas necesita flight-agent`.
9. En Phase 8, no hacer teoría pura: cada concepto debe venir con laboratorio visible.
10. Mantener la dinámica: qué hacer, por qué se hace y cómo validar.
11. Para laboratorios técnicos, avanzar un paso por vez y esperar `siguiente`.
12. No implementar React, autenticación ni dashboard empresarial todavía.
