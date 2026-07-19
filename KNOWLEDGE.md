# Conocimiento consolidado: Flight Agent

Este documento conserva principios y conceptos aprendidos que deberían seguir siendo válidos aunque cambie el estado del proyecto.

## 1. Enfoque arquitectónico del agente

`flight-agent` no es un agente completamente autónomo. Usa un patrón híbrido:

```text
Pipeline determinístico + intervención agentic acotada
```

Las tareas predecibles se resuelven mediante nodos y reglas. El LLM interviene únicamente cuando aparece un caso ambiguo.

Esto reduce comportamiento impredecible, consumo innecesario del modelo, dificultad de auditoría y dependencia de un servicio externo.

El uso de IA no convierte automáticamente todo el sistema en agentic. La autonomía debe introducirse solo donde aporte valor.

## 2. Pipeline y agente no son opuestos

Un sistema puede combinar:

```text
flujo fijo
+ decisiones dinámicas
+ tools externas
+ estado compartido
```

LangGraph puede organizar tanto pipelines determinísticos como rutas condicionales. La presencia de LangGraph no obliga a que el modelo decida todos los pasos.

## 3. State y persistencia

### State

`FlightMonitorState` representa el expediente temporal de una corrida.

Puede contener `run_id`, configuración, rutas, ofertas, resultados de reglas, casos ambiguos, alertas y errores.

El state:

- vive durante la ejecución;
- conecta los nodos;
- no es la memoria permanente del sistema;
- desaparece cuando termina el proceso, salvo que sus datos se persistan.

### Persistencia

SQLite conserva información entre ejecuciones, como vuelos, decisiones, review queue y agent runs.

Regla mental:

```text
State = contexto vivo de una corrida.
Persistence = información durable entre corridas.
```

Guardar algo en state no equivale a conservarlo permanentemente.

## 4. Responsabilidad de un node

Un node debe tener una responsabilidad arquitectónica clara:

```text
recibe state
-> realiza una tarea
-> actualiza o devuelve state
```

Ejemplos: cargar configuración, buscar vuelos, guardar un snapshot, evaluar reglas, analizar ambigüedades, persistir decisiones o enviar alertas.

Un node no debe convertirse en una función gigante que mezcle configuración, persistencia, integraciones, reglas y presentación.

## 5. Router

Un router decide qué camino debe seguir una entrada o un estado. No es un concepto exclusivo de agentes IA.

En un agente puede decidir:

```text
caso claro -> persistir decisión
caso ambiguo -> pedir análisis al LLM
caso rechazado -> terminar o registrar
```

La decisión puede estar implementada mediante reglas, código, un modelo o una combinación de ellos.

## 6. Tools, persistencia y catálogos

### Tools

Representan capacidades externas o acciones disponibles, como SerpAPI, Claude o Telegram.

### Persistencia

Representa acceso a memoria durable: insertar vuelos, consultar historial, guardar decisiones o registrar corridas.

SQLite no es una tool agentic por el solo hecho de ser utilizado por el agente.

### Catálogos

Contienen metadata referencial del dominio, como la clasificación de aerolíneas.

Un catálogo puede enriquecer una respuesta sin consultar internet en runtime, modificar el flujo del agente ni convertirse en una fuente absoluta de verdad.

Regla:

```text
Tool = capacidad externa.
Persistence = memoria durable.
Catalog = conocimiento referencial.
```

## 7. Observabilidad y auditoría

Observabilidad es una preocupación transversal, no una tool del agente.

Permite responder qué corrida ocurrió, cuánto duró, qué falló, cuántos vuelos encontró y qué decisiones pertenecen a esa corrida.

`run_id` crea una identidad común para relacionar logs, agent runs, decisiones y review queue.

### Error fatal y error recuperable

Un error fatal impide completar la corrida.

Un error recuperable puede registrarse en `state.errors` y permitir que el flujo continúe.

No todos los fallos externos deben derribar todo el agente. Esa decisión depende de la responsabilidad del componente y de la importancia de su resultado.

## 8. API como frontera

La API separa el interior del sistema de sus consumidores.

Un cliente no necesita conocer LangGraph, SQLite, la estructura de nodos ni los detalles de Claude. Solo necesita conocer el contrato HTTP.

```text
Cliente -> API -> aplicación -> persistencia o agente
```

La API no debe copiar el código interno. Debe validar entradas, delegar el caso de uso y transformar resultados en contratos externos.

## 9. Query API y Command API

Una query consulta información sin pedir un cambio principal:

```text
GET /runs
GET /runs/{run_id}
GET /review-queue
GET /offers/cheapest
```

Un command solicita que el sistema haga algo:

```text
POST /runs
POST /review-queue/{id}/approve
```

Regla conceptual:

```text
GET pregunta.
POST ordena o crea.
```

Una Command API requiere más atención a validación, idempotencia, autorización, duplicados, efectos secundarios y estados de ejecución.

## 10. AgentRunner

`AgentRunner` es una frontera de aplicación que centraliza el caso de uso de ejecutar una corrida completa del agente.

Puede ser invocado desde CLI, API, un worker futuro, un scheduler futuro o tests.

El runner no es un node de LangGraph, una tool, un endpoint ni una interfaz de usuario.

Su función es coordinar el ciclo alrededor del grafo:

- validar entradas internas;
- crear el state;
- asignar o recibir `run_id`;
- registrar el inicio;
- invocar LangGraph;
- capturar errores;
- registrar el final;
- devolver un resultado estructurado.

Principio aprendido:

```text
Los puntos de entrada deben ser delgados.
La lógica de aplicación debe ser reutilizable.
```

Copiar `main.py` dentro de FastAPI habría creado dos implementaciones divergentes de la misma ejecución.

## 11. Validación en distintas fronteras

Las validaciones pueden existir en más de una capa sin ser duplicación inútil.

### API

Pydantic valida el contrato HTTP: tipos, campos permitidos, formatos, límites y combinaciones válidas.

### AgentRunner

Protege reglas necesarias para cualquier punto de entrada, no solo HTTP.

Esto permite que una futura CLI, worker o scheduler no pueda saltarse las invariantes esenciales.

```text
La API protege su contrato externo.
La capa de aplicación protege sus invariantes de ejecución.
```

## 12. Configuración base y overrides

`config/routes.yaml` contiene configuración base.

Una corrida puede aplicar overrides temporales:

```text
configuración base
+ overrides de la solicitud
= configuración efectiva
```

Los overrides aplican únicamente a una corrida, no modifican el archivo YAML, deben validarse y deben poder auditarse mediante la configuración efectiva.

## 13. Ejecución síncrona y ejecución mediante jobs

### Ejecución síncrona

```text
POST /runs
-> valida request
-> ejecuta AgentRunner
-> espera que termine
-> devuelve resultado
```

Ventajas: es simple, fácil de comprender, suficiente para corridas cortas y no requiere infraestructura adicional.

Limitaciones: la petición permanece abierta, un timeout puede cortar la respuesta, la concurrencia y los reintentos son más difíciles y repetir la petición puede duplicar efectos.

### Ejecución mediante job

```text
POST /runs
-> registra job
-> devuelve run_id

worker
-> toma job
-> ejecuta AgentRunner
-> actualiza estado
```

Esto desacopla la duración del agente de la duración de la petición HTTP.

No se debe introducir una cola externa solo porque sea habitual en sistemas empresariales. Primero debe existir una necesidad concreta.

## 14. Ciclo de vida de una corrida

Los estados expresan una máquina de estados simple:

```text
running -> completed
running -> failed
```

Un diseño futuro con queue puede agregar:

```text
queued -> running -> completed
queued -> running -> failed
```

Los estados no son solo etiquetas visuales. Definen transiciones permitidas.

Una corrida finalizada no debería volver arbitrariamente a `running` usando el mismo identificador.

## 15. Identidad de ruta e identidad de búsqueda

Una ruta representa un trayecto lógico:

```text
LIM-MAD
```

Una búsqueda concreta incluye además tipo de viaje y fechas.

Por eso una misma ruta puede corresponder a varias búsquedas:

```text
LIM-MAD · solo ida · 2026-11-10
LIM-MAD · solo ida · 2026-11-12
LIM-MAD · ida y vuelta · 2026-11-10 a 2026-11-20
```

Regla:

```text
route identifica el trayecto.
search_id identifica la consulta concreta.
```

Usar solo `route` como identidad habría impedido distinguir fechas y tipos de viaje.

## 16. Solo ida e ida y vuelta

El tipo de búsqueda forma parte del contrato del dominio.

Una búsqueda de solo ida requiere origen, destino y fecha de salida. No debe recibir fecha de regreso.

Una búsqueda de ida y vuelta requiere origen, destino, fecha de salida y una fecha de regreso posterior.

No basta con agregar un campo opcional. El contrato debe validar la relación entre los campos.

```text
si trip_type = round_trip,
return_date es obligatoria y posterior a date.
```

## 17. Duplicado exacto

Repetir la misma ruta no siempre es un duplicado.

Estas búsquedas son diferentes:

```text
LIM-MAD el 10 de noviembre
LIM-MAD el 12 de noviembre
```

Existe duplicado cuando coinciden los atributos que definen la identidad de la búsqueda: ruta, tipo, fecha de ida y fecha de vuelta.

La unicidad debe modelarse según el significado del dominio, no según el campo más visible.

## 18. Persistir configuración efectiva

Guardar solo que una corrida ocurrió no basta para reproducir o auditar su comportamiento.

También importa conocer los modos utilizados, las rutas solicitadas, las rutas efectivas, fechas, reglas de precio y límites de escalas.

```text
Auditar una ejecución requiere conservar no solo el resultado,
sino también las condiciones bajo las cuales se produjo.
```

## 19. Frontend como consumidor

El frontend recoge entradas, construye requests, consume endpoints y presenta resultados.

No debe leer SQLite, ejecutar LangGraph, llamar directamente a Claude ni contener las reglas centrales del agente.

La validación en JavaScript mejora la experiencia, pero no reemplaza la validación del backend.

## 20. CORS

Un origin está formado por:

```text
protocolo + host + puerto
```

Por ejemplo, `http://127.0.0.1:5500` y `http://127.0.0.1:8000` son orígenes distintos.

CORS es una política aplicada por el navegador. No es un mecanismo general de autenticación ni autorización.

## 21. Human-in-the-loop

Human-in-the-loop no significa que una persona revise manualmente todo.

El patrón esperado es:

```text
casos claros -> decisión automática
casos ambiguos -> review_queue
humano -> aprueba o rechaza
resultado -> auditado
```

La intervención humana debe modelarse con estados, responsable, fecha, decisión y protección contra doble revisión.

## 22. Low-cost y condiciones tarifarias

Clasificar una aerolínea como low-cost es metadata referencial.

No permite concluir automáticamente que no incluye equipaje, que siempre es más barata o que una tarifa concreta tiene determinadas condiciones.

```text
Tipo de aerolínea != condiciones de la tarifa.
```

Las condiciones reales pertenecen a la oferta o tarifa específica.

## 23. Principios de diseño consolidados

1. Mantener los puntos de entrada delgados.
2. Centralizar cada caso de uso importante.
3. No confundir state con persistencia.
4. No convertir cualquier función en una tool.
5. Validar contratos en las fronteras.
6. Persistir identidad y contexto suficiente para auditar.
7. Modelar la unicidad según el dominio.
8. Preferir un diseño simple mientras sea suficiente.
9. Incorporar autonomía únicamente donde aporte valor.
10. Diferir infraestructura que todavía no resuelve una necesidad real.
