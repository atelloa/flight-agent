# Checkpoint: Flight Agent MVP

**Fecha:** 2026-07-04  
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
human-in-the-loop
backend API
frontend / UI
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
| Phase 7 | SIGUIENTE | Backend API read-only |
| Phase 8 | PLANIFICADA | Frontend / UI mínima consumiendo API |
| Phase 9 | PLANIFICADA | Human-in-the-loop operativo |
| Phase 10 | PLANIFICADA | Ejecución del agente por API |
| Phase 11 | PLANIFICADA | Jobs, scheduler y worker |
| Phase 12 | PLANIFICADA | Seguridad, despliegue y operación |

---

## Conceptos arquitectónicos aprendidos

### State

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

### Persistence

SQLite es la memoria permanente del sistema.

Guarda datos que deben sobrevivir entre ejecuciones:

```text
flights
decisions
review_queue
agent_runs
```

`db.py` no es una tool agentic. Es un adapter simple de persistencia SQLite.

### Nodes

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

### Tools vs Persistence

Separación conceptual:

```text
tools/
  capacidades externas del agente
  ejemplo: Claude, SerpAPI, Telegram

persistence/
  memoria permanente del sistema
  ejemplo: SQLite, snapshots, historial, review queue
```

### Observability

Observabilidad es una preocupación transversal.

Por eso vive en:

```text
src/flight_agent/observability/
```

No debe mezclarse innecesariamente dentro de tools ni persistence.

---

## Archivos principales

```text
checkpoint.md
main.py
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

---

# Phase 6 — Observabilidad, auditoría y resiliencia básica

**Estado general:** COMPLETA / SUFICIENTE PARA EL LABORATORIO.

Regla aprendida:

```text
No todo print debe guardarse en SQLite.
La base no debe convertirse en un basurero de logs.
```

---

## Phase 6.1 — Run History / Audit Trail

**Estado:** COMPLETA.

Objetivo:

```text
Guardar un resumen persistente de cada ejecución del agente.
```

Implementado y validado:

1. `run_id` único por ejecución en `main.py`.
2. Logs básicos por node con `src/flight_agent/observability/logging.py`.
3. `create_tables()` movido al inicio de `main.py`.
4. Tabla `agent_runs` en SQLite.
5. Función `save_agent_run()` en `src/flight_agent/persistence/db.py`.
6. `main.py` guarda una fila en `agent_runs` desde `finally`.
7. Se validó en SQLite Viewer que `agent_runs` tiene registros.

Responsabilidad de `agent_runs`:

```text
Historial auditable de corridas del agente.
```

Campos relevantes:

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

Nota de nomenclatura:

```text
recoverable_errors_count quedó implementado con ese nombre.
Conceptualmente debe entenderse como conteo de errores no fatales.
Mejor nombre futuro si se refactoriza: non_fatal_errors_count.
No renombrar ahora salvo que se decida una refactorización explícita.
```

---

## Phase 6.2 — Errores básicos / resiliencia

**Estado:** COMPLETA / SUFICIENTE.

Objetivo:

```text
Diferenciar error fatal de error no fatal.
```

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

Punto importante:

```text
state.errors nace cuando se crea FlightMonitorState().
No nace cuando falla Telegram.
Telegram solo agrega elementos a esa lista.
```

---

## Phase 6.3 — Resumen mínimo de errores no fatales

**Estado:** COMPLETA / SUFICIENTE.

Objetivo:

```text
Persistir un resumen mínimo de errores no fatales por corrida.
```

Implementado y validado:

1. Se agregó columna en `agent_runs`:

```text
recoverable_errors_count
```

2. Se agregó helper en `db.py`:

```python
column_exists(conn, table_name, column_name)
```

Uso:

```text
Permite agregar columnas con ALTER TABLE sin romper si se ejecuta create_tables() varias veces.
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

---

## Phase 6.4 — Decision Audit

**Estado:** COMPLETA / SUFICIENTE.

Objetivo:

```text
Auditar qué decisiones tomó el agente y en qué ejecución ocurrieron.
```

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

Motivo:

```text
Si la tabla crece, el INSERT no se rompe por cantidad u orden de columnas.
```

---

## Phase 6.5 — Review Queue Observability

**Estado:** COMPLETA / SUFICIENTE.

Objetivo:

```text
Conectar los casos de revisión humana con la corrida que los generó.
```

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

---

## Phase 6.6 — Node Events

**Estado:** DIFERIDO.

No implementarlo ahora.

Node Events sería tracing detallado:

```text
run_id
node_name
event_type: start / end / error
timestamp
duration_seconds
message
```

Decisión:

```text
No hace falta para el objetivo actual.
Ya se entendieron las piezas principales de observabilidad.
Implementarlo ahora sería sobrearquitectura.
```

---

# Estado final de Phase 6

Piezas consolidadas:

```text
agent_runs
  -> historial de corridas

state.errors
  -> errores no fatales temporales dentro de una corrida

agent_runs.recoverable_errors_count
  -> resumen persistente de errores no fatales

decisions.run_id
  -> auditoría de decisiones por corrida

review_queue.run_id
  -> auditoría human-in-the-loop por corrida
```

Con esto, Phase 6 queda cerrada para el laboratorio.

---

# Ruta de aprendizaje desde Phase 7 en adelante

Decisión tomada el 2026-07-04:

```text
Separar Backend API y Frontend en fases distintas.
```

Motivo:

```text
Una API es una frontera contractual backend.
Un frontend es una capa de interacción humana que consume esa API.
Mezclarlas desde el inicio confunde responsabilidades.
```

---

# Phase 7 — Arquitectura de Backend APIs

**Estado:** SIGUIENTE.

Objetivo de Phase 7:

```text
Entender cómo una API se vuelve una frontera limpia entre el agente y otros consumidores.
```

Resultado esperado de Phase 7:

```text
main.py ejecuta el agente.
SQLite guarda resultados.
FastAPI consulta SQLite.
La API no ejecuta el agente todavía.
```

Arquitectura objetivo de esta fase:

```text
main.py -> agente -> SQLite <- API <- cliente
```

Regla principal:

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

## Puntos internos de Phase 7

```text
7.1 Qué es una API como frontera arquitectónica
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
7.14 Validación con navegador, curl o Swagger
```

## Qué debe exponer al inicio

```text
GET /health
GET /runs
GET /runs/{run_id}
GET /review-queue
```

## Qué NO debe exponer todavía

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

## FastAPI

FastAPI es un framework de Python para crear APIs HTTP.

No es la arquitectura.

```text
Arquitectura:
API read-only que consulta SQLite.

Herramienta:
FastAPI.
```

## API Gateway

API Gateway se aprende conceptualmente en Phase 7.8.

No se implementa todavía.

Regla:

```text
Un API Gateway no se agrega porque tienes una API.
Se agrega porque tienes varias APIs, exposición externa, seguridad común,
rate limiting, versionamiento o necesidades operativas.
```

Para el estado actual de `flight-agent`:

```text
API local
read-only
una sola API
SQLite local
sin usuarios externos
sin múltiples servicios
sin cloud
sin tráfico real
```

Conclusión:

```text
Entender API Gateway: sí.
Implementarlo ahora: no.
```

---

# Phase 8 — Arquitectura de Frontend / UI

**Estado:** PLANIFICADA.

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

## Puntos internos de Phase 8

```text
8.1 Qué es frontend en arquitectura
8.2 Frontend vs Backend vs API
8.3 Por qué el frontend no debe leer SQLite directamente
8.4 Tipos de frontend: dashboard, consola interna, admin panel
8.5 Qué pantallas tendría sentido para flight-agent
8.6 Estados de UI: loading, empty, error, success
8.7 Consumo de GET /runs
8.8 Consumo de GET /runs/{run_id}
8.9 Consumo de GET /review-queue
8.10 UI mínima read-only
8.11 Validar que la UI consume la API, no la base
```

## Qué NO hacer todavía

```text
No React todavía.
No frontend público.
No autenticación todavía.
No diseño visual complejo.
No dashboard empresarial.
```

Opciones didácticas futuras:

```text
HTML simple
Jinja
Streamlit
otra UI mínima local
```

La elección de herramienta debe hacerse cuando Phase 8 empiece.

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

Nota:

```text
Esto es más empresarial.
No hacerlo pronto si el concepto de API y frontend aún no está claro.
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
Pero no es parte inmediata de Phase 7.
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

---

## Reglas para el próximo chat

Cuando se retome este proyecto:

1. Leer primero este `checkpoint.md` desde GitHub.
2. Recordar que el objetivo es aprendizaje de arquitectura y diseño de agentes IA.
3. Mantener pasos pequeños.
4. No saltar a soluciones empresariales complejas antes de que el concepto esté claro.
5. No quedarse horas afinando una fase si el concepto ya quedó aprendido.
6. Phase 6 está cerrada.
7. Continuar desde `Phase 7.1 — Qué es una API como frontera arquitectónica`.
8. Mantener la dinámica: qué hacer, por qué se hace y cómo validar.
9. No escribir código antes de cerrar la decisión conceptual de la fase.
10. Para laboratorios técnicos, avanzar un paso por vez y esperar `siguiente`.
