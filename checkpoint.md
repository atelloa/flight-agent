# Checkpoint: Flight Agent MVP

**Fecha:** 2026-07-03  
**Proyecto:** `flight-agent`  
**Repo GitHub:** `atelloa/flight-agent`  
**Archivo de continuidad:** `checkpoint.md` en la raíz del repo.

Este archivo existe para poder retomar el laboratorio en un nuevo chat sin volver a explicar todo el contexto.

---

## Objetivo del laboratorio

Aprender **arquitectura y diseño de agentes IA** usando un proyecto real y pequeño como laboratorio.

El objetivo principal no es hacer el sistema más complejo rápido. El objetivo es entender, paso a paso, cómo se diseñan las piezas de un agente:

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
```

Regla de trabajo:

```text
Un paso por vez.
Explicar qué hacer, por qué se hace y cómo validar.
No avanzar hasta que el usuario diga "siguiente".
Evitar sobrearquitectura.
```

---

## Arquitectura actual

El proyecto es un agente de monitoreo de vuelos con Python, LangGraph y un patrón híbrido:

```text
Pipeline determinístico + intervención agentic acotada
```

No es un agente totalmente autónomo.

El flujo principal está predeterminado:

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

Nota importante:

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

En `config/routes.yaml` el modo seguro de laboratorio es:

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
| Phase 6 | EN CURSO | Observabilidad y resiliencia básica |
| Phase 7 | PENDIENTE | Backend API + interfaz de usuario |

---

## Conceptos arquitectónicos aprendidos

### 1. State

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

### 2. Persistence

SQLite es la memoria permanente del sistema.

Guarda datos que deben sobrevivir entre ejecuciones:

```text
flights
decisions
review_queue
agent_runs
```

`db.py` no es una tool agentic. Es un adapter simple de persistencia SQLite.

### 3. Nodes

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

### 4. Tools vs Persistence

Separación conceptual:

```text
tools/
  capacidades externas del agente
  ejemplo: Claude, SerpAPI, Telegram

persistence/
  memoria permanente del sistema
  ejemplo: SQLite, snapshots, historial, review queue
```

### 5. Observability

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

## Phase 6 — Observabilidad

Phase 6 está enfocada en aprender arquitectura de observabilidad y resiliencia, no en llenar el proyecto de logs.

Regla importante:

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
3. `create_tables()` fue movido al inicio de `main.py`.
4. Se creó tabla `agent_runs` en SQLite.
5. Se creó función `save_agent_run()` en `src/flight_agent/persistence/db.py`.
6. `main.py` guarda una fila en `agent_runs` desde `finally`.
7. Se validó en SQLite Viewer que `agent_runs` ya tiene registros.

Diseño actual de `main.py`:

```text
create_tables()
crear FlightMonitorState
generar state.run_id
guardar started_at
medir duración con perf_counter()
ejecutar compiled_graph.invoke(state)
si éxito -> run_status = success
si falla -> run_status = failed + error_message
usar raise para no ocultar errores
en finally -> save_agent_run(...)
```

Responsabilidad de `agent_runs`:

```text
Historial auditable de corridas del agente.
```

No debe guardar vuelos individuales ni decisiones detalladas.

Campos actuales:

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
```

---

## Phase 6.2 — Errores básicos / resiliencia

**Estado:** EN CURSO.

Objetivo:

```text
Preparar al agente para registrar errores internos recuperables.
```

Ejemplos de errores recuperables:

```text
error en Telegram
error en Claude
error en SerpAPI
error parcial de persistencia
```

Importante:

```text
No avanzar todavía a retries.
No avanzar todavía a circuit breakers.
No crear tablas nuevas todavía.
No meter logging complejo todavía.
```

### Phase 6.2.1 — Campo errors en State

**Estado:** COMPLETA.

Se agregó en `src/flight_agent/state.py`:

```python
errors: List[Dict] = field(default_factory=list)
```

Import necesario:

```python
from typing import List, Dict
```

Concepto:

```text
state.errors = lista temporal de errores recuperables durante una corrida.
```

Esto todavía no maneja errores. Solo prepara el contenedor.

Ejemplo conceptual futuro:

```python
state.errors.append({
    "node": "send_alert",
    "error": "Telegram timeout"
})
```

Validación realizada:

```text
python main.py corre sin error de imports ni error por field/List/Dict.
```

---

## Siguiente paso exacto

Continuar con:

```text
Phase 6.2.2 — Registrar un error recuperable en state.errors
```

Primer caso recomendado:

```text
send_alert / Telegram
```

Motivo:

```text
Telegram es una dependencia externa.
Si Telegram falla, no necesariamente debe caer todo el agente.
El sistema puede registrar el error y continuar.
```

Pero avanzar solo con un cambio pequeño:

```text
Agregar try/except local en el node de envío de alerta.
Si falla Telegram, hacer append a state.errors.
No persistir todavía en SQLite.
No hacer retry todavía.
No crear tabla agent_errors todavía.
```

---

## Pendientes de Phase 6

Orden recomendado:

```text
1. Run History / Audit Trail          COMPLETO
2. Errores básicos en state.errors    EN CURSO
3. Persistir resumen de errores       PENDIENTE
4. Decision Audit                     PENDIENTE
5. Review Queue Observability         PENDIENTE
6. Node Events                        SOLO SI HACE FALTA
```

### Decision Audit futuro

Objetivo:

```text
Auditar qué decidió el agente, por qué y en qué ejecución ocurrió.
```

Ejemplo:

```text
run_id
flight_id
decision: alert / ignore / recheck / needs_review
source: rules / claude / mock
reason
created_at
```

### Review Queue Observability futuro

Objetivo:

```text
Conectar decisiones dudosas con revisión humana.
```

Patrón:

```text
human-in-the-loop
```

### Node Events futuro

No implementarlo todavía.

Sería tracing detallado por node:

```text
run_id
node_name
event_type: start / end / error
timestamp
duration_seconds
message
```

Esto puede ser útil después, pero no es urgente para el laboratorio.

---

## Mejoras futuras fuera de Phase 6 inmediata

### Subgrafo condicional real

Actualmente `claude_analysis` está siempre conectado después de `decision_router`, aunque internamente solo procesa ambiguos.

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

Por ahora se mantiene simple para el laboratorio.

---

## Reglas para el próximo chat

Cuando se retome este proyecto:

1. Leer primero este `checkpoint.md`.
2. Recordar que el objetivo es aprendizaje de arquitectura y diseño de agentes IA.
3. Mantener pasos pequeños.
4. No saltar a soluciones empresariales complejas antes de que el concepto esté claro.
5. No proponer retries, circuit breakers, colas, OpenTelemetry o dashboards antes de cerrar errores básicos.
6. Continuar desde `Phase 6.2.2`.
