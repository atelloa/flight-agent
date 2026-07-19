# Plan del laboratorio Flight Agent

## Objetivo general

Aprender arquitectura y diseño de agentes IA construyendo progresivamente un agente de monitoreo de vuelos.

El proyecto debe permitir comprender cómo se relacionan estado, nodos, tools, persistencia, routing, LLM, observabilidad, API, frontend, human-in-the-loop, jobs, workers, seguridad y operación.

## Alcance

El laboratorio cubre desde un MVP local hasta una arquitectura operable básica.

No busca construir inmediatamente una plataforma empresarial completa. Componentes como colas externas, microservicios, Kubernetes, autenticación avanzada o alta disponibilidad solo deben incorporarse cuando aporten un concepto arquitectónico nuevo y exista una necesidad clara.

## Estados utilizados

- **PENDIENTE:** todavía no iniciada.
- **EN CURSO:** parcialmente implementada o pendiente de validación final.
- **COMPLETADA:** objetivo conceptual e implementación mínima validados.
- **COMPLETADA / SUFICIENTE:** existen mejoras posibles, pero continuar refinándola no aporta suficiente aprendizaje en este momento.
- **DIFERIDA:** válida para el proyecto, pero no prioritaria.
- **OPCIONAL:** puede omitirse sin impedir el recorrido principal.

## Fases

### Phase 1 — MVP local

**Estado:** COMPLETADA

**Objetivo:** construir el primer flujo funcional de monitoreo desde consola.

**Criterio de cierre:** el programa carga configuración, obtiene o simula vuelos, evalúa reglas y produce una salida comprensible.

### Phase 2 — Persistencia

**Estado:** COMPLETADA

**Objetivo:** distinguir estado temporal de memoria permanente.

**Criterio de cierre:** los datos relevantes sobreviven entre ejecuciones, SQLite está aislado detrás de funciones de persistencia y el flujo puede consultar información histórica.

### Phase 3 — Alertas externas

**Estado:** COMPLETADA

**Objetivo:** integrar una capacidad externa sin mezclarla con la lógica central.

**Criterio de cierre:** Telegram está encapsulado, puede habilitarse o deshabilitarse mediante configuración y el agente sigue funcionando cuando está apagado.

### Phase 4 — Review queue manual

**Estado:** COMPLETADA

**Objetivo:** representar casos que requieren intervención humana.

**Criterio de cierre:** los casos ambiguos pueden persistirse en `review_queue`, la cola conserva estado y trazabilidad básica, y la revisión humana no está mezclada con la ejecución principal.

### Phase 5 — Análisis agentic acotado

**Estado:** COMPLETADA

**Objetivo:** usar un LLM solo en casos ambiguos, manteniendo el pipeline principal determinístico.

**Criterio de cierre:** las reglas resuelven casos claros, Claude o su modo mock procesa casos ambiguos, la salida cumple un contrato estructurado y un fallo del modelo no destruye necesariamente toda la corrida.

### Phase 6 — Observabilidad, auditoría y resiliencia básica

**Estado:** COMPLETADA / SUFICIENTE

**Objetivo:** hacer que una corrida pueda identificarse, revisarse y diagnosticarse.

**Subfases consolidadas:**

- `run_id` por corrida.
- Logs básicos por nodo.
- Duración total.
- Tabla `agent_runs`.
- Resumen de resultados.
- Errores no fatales en `state.errors`.
- Asociación de decisiones y review queue con `run_id`.

**Criterio de cierre:** cada corrida puede identificarse, sus resultados y errores principales pueden consultarse y los errores recuperables no necesariamente detienen todo el flujo.

**Diferido:** eventos detallados por nodo.

### Phase 7 — Backend API de lectura

**Estado:** COMPLETADA / SUFICIENTE

**Objetivo:** crear una frontera HTTP para consultar datos persistidos.

**Subfases consolidadas:**

- Health check.
- Consulta de corridas.
- Detalle de una corrida.
- Consulta de review queue.
- Consulta de ofertas.
- Validación de parámetros.
- Enriquecimiento mediante catálogo de aerolíneas.

**Criterio de cierre:** los consumidores no acceden directamente a SQLite, los endpoints de lectura no ejecutan LangGraph y la API devuelve contratos JSON definidos.

### Phase 8 — Frontend mínimo

**Estado:** COMPLETADA / SUFICIENTE

**Objetivo:** entender el frontend como consumidor de una API.

**Subfases consolidadas:**

- Frontend estático.
- Consulta de estado de API.
- Historial y detalle de corridas.
- Consulta de ofertas.
- Filtros básicos.
- CORS para desarrollo local.

**Criterio de cierre:** el navegador consume FastAPI, no accede directamente a SQLite y la lógica central del agente no está duplicada en JavaScript.

**Diferido:** operación visual de `review_queue`.

### Phase 9 — Human-in-the-loop operativo

**Estado:** DIFERIDA / OPCIONAL

**Objetivo:** permitir que una persona apruebe o rechace decisiones pendientes mediante API y UI.

**Subfases previstas:**

- Estados `pending`, `approved` y `rejected`.
- Commands de aprobación y rechazo.
- Registro de quién revisó y cuándo.
- UI mínima para operar la cola.
- Protección contra revisiones duplicadas.

**Criterio de cierre:** la decisión humana queda persistida y auditada, una misma revisión no puede resolverse dos veces de forma inconsistente y la API diferencia consultas de comandos.

Esta fase puede retomarse después de comprender la ejecución desacoplada.

### Phase 10 — Ejecución del agente por API

**Estado:** EN CURSO — implementación principal completada; cierre formal pendiente

**Objetivo:** reutilizar la misma ejecución del agente desde distintos puntos de entrada sin copiar la lógica de `main.py`.

#### 10.1 Frontera de ejecución

- Separación entre punto de entrada y lógica de aplicación.
- Definición de `AgentRunner`.

#### 10.2 CLI desacoplada

- `main.py` delega la ejecución al runner.
- La CLI conserva interacción y presentación.

#### 10.3 Command API síncrona

- `POST /runs` ejecuta una corrida.
- FastAPI valida el contrato de entrada.
- El endpoint delega en `AgentRunner`.

#### 10.4 Configuración por corrida

- Overrides temporales.
- Validación de valores permitidos.
- Precedencia sobre la configuración base sin modificar el YAML.
- Retorno de configuración efectiva.

#### 10.5 Rutas dinámicas

- Rutas enviadas en el request.
- Validación de IATA, fechas, precio y escalas.
- Rutas efectivas disponibles en el resultado.

#### 10.6 Tipos de búsqueda

- Solo ida.
- Ida y vuelta combinada.
- Fecha de regreso obligatoria y posterior para ida y vuelta.
- Rechazo de combinaciones inconsistentes.

#### 10.7 Identidad del dominio

- Separación entre `route` y `search_id`.
- Misma ruta permitida en fechas distintas.
- Duplicado exacto rechazado.
- Persistencia de la identidad de búsqueda.

#### 10.8 Ciclo de vida de corridas

- `running`.
- `completed`.
- `failed`.
- Compatibilidad prevista con un futuro estado `queued`.

#### 10.9 Persistencia y consulta

- Configuración y rutas efectivas persistidas.
- Resultados consultables mediante GET.
- UI capaz de iniciar corridas y refrescar resultados.

**Pendiente para cerrar la fase:**

- Confirmar la validación manual end-to-end de la versión actual.
- Revisar riesgos de petición HTTP larga, doble ejecución, consumo de APIs, alertas duplicadas y concurrencia.
- Declarar formalmente si la solución es suficiente para el laboratorio.

**Criterio de cierre:** CLI y API reutilizan la misma ejecución, el endpoint no contiene el pipeline del agente, las entradas están validadas, el ciclo de vida queda persistido y las limitaciones de la ejecución síncrona están comprendidas.

### Phase 11 — Jobs, worker y scheduler

**Estado:** PENDIENTE

**Objetivo:** desacoplar la solicitud de ejecución del trabajo real.

#### 11.1 Request frente a job

Comprender la diferencia entre:

```text
POST /runs -> ejecuta ahora
```

y:

```text
POST /runs -> registra job -> responde
worker -> toma job -> ejecuta AgentRunner
```

#### 11.2 Estados de job

- `queued`.
- `running`.
- `completed`.
- `failed`.

#### 11.3 Worker

- Ejecuta el trabajo fuera de la petición HTTP.
- Reutiliza `AgentRunner`.
- Actualiza el ciclo de vida persistido.

#### 11.4 Idempotencia y concurrencia

- Evitar ejecución duplicada.
- Definir identidad de solicitudes.
- Controlar alertas repetidas.
- Manejar corridas simultáneas.

#### 11.5 Scheduler

- Crear ejecuciones periódicas.
- Separar planificación de ejecución.
- Evitar que el scheduler contenga lógica del agente.

#### 11.6 Tecnología de cola

Evaluar primero una solución simple. Redis, Celery u otra tecnología solo deben agregarse cuando el concepto esté claro y el laboratorio lo necesite.

**Criterio de cierre:** la API no espera la ejecución completa, un worker independiente puede ejecutar `AgentRunner`, el estado del job puede consultarse y fallos y reintentos tienen reglas explícitas.

### Phase 12 — Seguridad, despliegue y operación

**Estado:** PENDIENTE

**Objetivo:** comprender qué cambia cuando el sistema deja de ser un laboratorio local.

**Subfases previstas:**

- Variables de entorno y secretos.
- Autenticación.
- Autorización.
- Rate limiting.
- Manejo consistente de errores.
- Logs de API.
- Docker.
- Reverse proxy.
- Despliegue.
- Monitoreo básico.
- Recuperación ante fallos.
- Política de costos para APIs externas.

**Criterio de cierre:** los secretos no están en el código, los endpoints de ejecución están protegidos, el servicio puede desplegarse de forma reproducible y existen señales mínimas para operarlo y diagnosticarlo.

## Mejoras transversales diferidas

Estas mejoras no constituyen fases inmediatas:

- Routing condicional real hacia `claude_analysis`.
- División de `db.py` en repositories más específicos.
- Traslado de la API a un paquete interno.
- Actualización automática del catálogo de aerolíneas.
- Eventos detallados por nodo.
- Dashboard más avanzado.
- Sustitución de SQLite cuando exista una necesidad real de concurrencia.

Solo deben priorizarse cuando resuelvan una limitación concreta o aporten un concepto arquitectónico nuevo.
