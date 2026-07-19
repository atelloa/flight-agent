# Checkpoint: Flight Agent

**Última actualización:** 2026-07-18  
**Proyecto:** `flight-agent`  
**Repositorio:** `atelloa/flight-agent`

Este documento conserva únicamente el estado vigente necesario para retomar el laboratorio. El recorrido completo está en [`PLAN.md`](PLAN.md) y los conceptos consolidados en [`KNOWLEDGE.md`](KNOWLEDGE.md).

## Objetivo general

Aprender arquitectura y diseño de agentes IA mediante la construcción incremental de un agente de monitoreo de vuelos con Python, LangGraph, FastAPI y SQLite.

El objetivo principal no es acumular funcionalidades, sino comprender las decisiones arquitectónicas: responsabilidades, fronteras, estado, persistencia, ejecución, observabilidad, intervención humana y operación.

## Forma de trabajo

- Avanzar un solo paso por vez.
- Explicar siempre qué hacer, por qué se hace y cómo validar.
- No continuar hasta que el usuario diga `siguiente`.
- Entender primero la decisión de diseño y después escribir código.
- Separar arquitectura de implementación.
- Evitar sobrearquitectura.
- No seguir refinando una fase cuando su concepto principal ya quedó comprendido.
- No incorporar componentes empresariales complejos antes de que sean necesarios.

## Arquitectura vigente

El agente usa un enfoque híbrido:

```text
Pipeline determinístico + intervención agentic acotada
```

Flujo interno principal:

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

Fronteras de ejecución:

```text
main.py
  -> AgentRunner
  -> LangGraph
  -> SQLite

Frontend
  -> FastAPI
  -> AgentRunner para ejecutar corridas
  -> SQLite para consultar resultados
```

`main.py` y `api.py` son puntos de entrada. La ejecución completa del agente está centralizada en `src/flight_agent/runner.py`.

## Estado actual

- **Phases 1–8:** completadas.
- **Phase 9 — Human-in-the-loop operativo:** planificada y diferida.
- **Phase 10 — Ejecución del agente por API:** implementación principal completada; cierre formal pendiente de confirmar.
- **Phases 11–12:** planificadas y no implementadas.

Consultar [`PLAN.md`](PLAN.md) para el detalle de fases y criterios de cierre.

## Implementación vigente relevante

Actualmente están implementados:

- `AgentRunner` como frontera de ejecución reutilizable.
- CLI y API usando el mismo runner.
- `POST /runs` síncrono para ejecutar el agente.
- Validación de requests mediante Pydantic.
- Overrides temporales de configuración por corrida.
- Rutas dinámicas por corrida sin modificar `routes.yaml`.
- Búsquedas de solo ida e ida y vuelta combinada.
- Persistencia del ciclo de vida de la corrida con estados `running`, `completed` y `failed`.
- Persistencia de configuración y rutas efectivas.
- Separación entre `route`, que representa el trayecto, y `search_id`, que representa una búsqueda concreta con tipo y fechas.
- Posibilidad de repetir una ruta en fechas diferentes y rechazo de duplicados exactos.
- Frontend estático capaz de iniciar corridas y consultar resultados.
- Persistencia de vuelos, decisiones, review queue y agent runs en SQLite.
- Observabilidad básica y errores no fatales asociados a la corrida.

## Modo seguro del laboratorio

Para aprender y validar sin consumir servicios externos:

```text
fetch_mode: cached
claude_mode: mock
telegram_enabled: false
review_mode: true
```

Los overrides enviados en una corrida son temporales y no modifican `config/routes.yaml`.

## Último resultado verificable

El código vigente permite ejecutar desde la UI búsquedas dinámicas de solo ida o ida y vuelta, repetir una misma ruta en fechas distintas y conservar separadamente la identidad del trayecto y la identidad de cada búsqueda.

**Pendiente de confirmar:** cuál fue la última prueba manual end-to-end completada después de estos cambios.

## Tema actual

Cerrar correctamente Phase 10 después de revisar el resultado completo de la ejecución síncrona por API y de las búsquedas dinámicas.

La limitación arquitectónica vigente es:

```text
POST /runs mantiene abierta la petición HTTP
durante toda la ejecución del agente.
```

Esto es aceptable para el laboratorio local y corridas cortas, pero todavía no representa una arquitectura desacoplada mediante jobs y workers.

## Siguiente paso concreto

Revisar conceptualmente el límite de la implementación síncrona actual y decidir si Phase 10 puede cerrarse como `COMPLETA / SUFICIENTE`.

Después de esa decisión, el siguiente bloque recomendado es:

```text
Phase 11.1 — Diferencia entre ejecutar una corrida dentro de la petición HTTP
y registrar un job para que un worker lo ejecute fuera de la petición.
```

No implementar Redis, Celery, scheduler ni infraestructura adicional antes de comprender esa frontera.

## Bloqueos o incertidumbres

- Pendiente confirmar la última validación manual end-to-end.
- Pendiente confirmar si Phase 10 ya fue declarada formalmente cerrada en una sesión posterior.
- No existe todavía ejecución desacoplada con queue y worker.
- `review_queue` existe en backend y persistencia, pero su operación humana mediante UI continúa diferida.
- No implementar todavía autenticación, despliegue cloud, scheduler ni dashboard empresarial.
