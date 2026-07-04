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
UI mínima
```

Reglas de trabajo:

```text
Un paso por vez.
Explicar qué hacer, por qué se hace y cómo validar.
No avanzar hasta que el usuario diga "siguiente".
Evitar sobrearquitectura.
No quedarse afinando infinitamente un punto si el concepto arquitectónico ya quedó claro.
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
| Phase 7 | SIGUIENTE | Backend API + interfaz de usuario mínima |

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

# Phase 7 — Backend API + interfaz de usuario mínima

**Estado:** SIGUIENTE.

Objetivo de Phase 7:

```text
Exponer la información del agente mediante una API simple para consultar corridas, decisiones y casos de revisión.
```

No empezar con frontend completo.

Orden recomendado:

```text
Phase 7.1 — Definir frontera de la API
Phase 7.2 — Crear API mínima con FastAPI
Phase 7.3 — Endpoint GET /runs
Phase 7.4 — Endpoint GET /runs/{run_id}
Phase 7.5 — Endpoint GET /review-queue
Phase 7.6 — UI mínima solo si aporta al aprendizaje
```

Reglas para Phase 7:

```text
No rediseñar todo el agente.
No meter autenticación todavía.
No meter Docker todavía.
No meter React todavía.
No crear microservicios.
No convertir esto en plataforma.
Primero API read-only para entender la frontera entre agente y backend.
```

Primer paso exacto recomendado:

```text
Phase 7.1 — Definir qué debe exponer la API y qué NO debe exponer.
```

Pregunta arquitectónica inicial:

```text
¿La API debe ejecutar el agente o solo consultar resultados guardados?
```

Recomendación inicial:

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
7. Continuar desde `Phase 7.1 — Definir frontera de la API`.
8. Mantener la dinámica: qué hacer, por qué se hace y cómo validar.
