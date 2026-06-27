# Checkpoint: Flight Agent MVP

**Fecha:** 2026-06-27  
**Objetivo principal:** Aprender arquitectura de soluciones de agentes IA usando un proyecto real como laboratorio.

---

## Estado actual del laboratorio

| Fase | Estado | Resultado |
|---|---|---|
| Phase 1 | COMPLETA | MVP local con consola |
| Phase 2 | COMPLETA | Persistencia SQLite |
| Phase 3 | COMPLETA | Alertas por Telegram |
| Phase 4 | COMPLETA | Review queue manual |
| Phase 5 | COMPLETA | Claude analiza casos ambiguos |
| Phase 6 | PENDIENTE | Logging, trazas y observabilidad |
| Phase 7 | PENDIENTE | Backend API + interfaz de usuario |

---

## Flujo actual implementado

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

Nota importante: `claude_analysis` siempre aparece en el grafo, pero solo procesa alertas con `tipo = ambiguous`. Si no hay casos ambiguos, el node termina sin llamar a Claude.

---

## Conceptos arquitectónicos aprendidos

### 1. State

`FlightMonitorState` es el expediente vivo de una corrida.

Vive en RAM durante `python main.py`. No es permanente.

Ejemplo:

```text
state.latest_offers
state.rule_matches
state.suspicious_cases
state.alerts_to_send
```

Cuando termina la ejecución, ese state desaparece.

### 2. Persistencia

SQLite es la memoria permanente.

Guarda:

```text
flights
 decisions
 review_queue
```

La tabla `flights` funciona también como cache mínima usando `searched_at` para identificar el último snapshot.

### 3. Snapshot

Un snapshot es la foto de vuelos encontrada en una corrida.

En modo `live`:

```text
SerpAPI -> state.latest_offers -> SQLite
```

En modo `cached`:

```text
SQLite -> state.latest_offers
```

La cache reconstruye objetos `Flight` para que el resto del grafo trabaje igual sin saber si los vuelos vinieron de SerpAPI o SQLite.

### 4. Nodes

Los nodes organizan el workflow.

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

### 5. Tools vs Persistence

Se separó el concepto:

```text
tools/
  capacidades externas del agente
  ejemplo: Claude, SerpAPI, Telegram

persistence/
  memoria permanente del sistema
  ejemplo: SQLite, snapshots, historial, review queue
```

`db.py` dejó de entenderse como tool agentica y pasó a verse como adapter de persistencia SQLite.

### 6. Bounded Agentic Workflow

Claude no controla todo el flujo.

Claude solo entra cuando el router marca un caso como ambiguo.

Esto mantiene el sistema:

```text
más barato
más trazable
más estable
menos variable
```

### 7. Modos de ejecución

Se agregaron banderas para controlar costos y efectos externos.

En `config/routes.yaml`:

```yaml
global:
  review_mode: true
  fetch_mode: "cached"
  claude_mode: "mock"
  telegram_enabled: false
```

Significado:

| Config | live / true | cached / mock / false |
|---|---|---|
| `fetch_mode` | llama SerpAPI | lee último snapshot desde SQLite |
| `claude_mode` | llama Claude | simula respuesta estructurada |
| `telegram_enabled` | envía Telegram | no envía Telegram |

Modo laboratorio seguro:

```text
fetch_mode: cached
claude_mode: mock
telegram_enabled: false
```

Este modo permite ejecutar el pipeline completo sin gastar SerpAPI, sin gastar Claude y sin enviar Telegram.

---

## Archivos principales

```text
config/routes.yaml
src/flight_agent/state.py
src/flight_agent/graph.py
src/flight_agent/nodes/load_config.py
src/flight_agent/nodes/fetch_flights.py
src/flight_agent/nodes/claude_analysis.py
src/flight_agent/nodes/nodes.py
src/flight_agent/tools/claude_tool.py
src/flight_agent/persistence/db.py
data/flight_agent.sqlite
main.py
```

---

## Decisiones de arquitectura tomadas

1. El flujo principal sigue siendo determinístico.
2. Claude se usa solo para interpretar casos ambiguos.
3. SQLite se usa como memoria permanente y cache local.
4. El state se mantiene como memoria temporal de la corrida.
5. `db.py` pertenece conceptualmente a `persistence/`, no a `tools/`.
6. Los modos `live/cached/mock` permiten separar desarrollo, pruebas y ejecución real.
7. Las credenciales deben vivir en `.env` y `.env` no debe versionarse.

---

## Pendientes próximos

### Phase 6: Observabilidad

Agregar mejor trazabilidad de ejecución:

```text
run_id
logs por node
tiempos por node
conteo de vuelos por ruta
conteo de llamadas externas
errores controlados
```

### Mejora futura: subgrafo condicional real

Actualmente `claude_analysis` está siempre conectado después de `decision_router`, aunque internamente solo procesa ambiguos.

Más adelante se puede convertir en routing condicional real:

```text
si hay ambiguous -> claude_analysis
si no hay ambiguous -> store_decisions
```

### Mejora futura: repositories

Si el proyecto crece, dividir `persistence/db.py` en:

```text
flight_repository.py
decision_repository.py
review_queue_repository.py
sqlite.py
```

Por ahora se mantiene simple para el laboratorio.
