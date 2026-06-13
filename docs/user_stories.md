# Historias de Usuario — TaskMind-API MVP

**Proyecto:** TaskMind-API  
**Versión:** 1.0  
**Fecha:** 2026-06-08  
**Autor:** Product Manager

---

## HU-01 — Creación de Tareas con Priorización por IA

### Descripción

> **Como** usuario autenticado de la aplicación,  
> **quiero** crear una nueva tarea enviando su título y descripción al backend,  
> **para** que el sistema utilice Inteligencia Artificial (Gemini) y me asigne automáticamente un nivel de prioridad, ahorrándome tiempo y mejorando mi organización personal.

### Información Adicional

| Campo           | Detalle                                                                 |
|-----------------|-------------------------------------------------------------------------|
| Endpoint        | `POST /api/v1/tasks`                                                    |
| Autenticación   | Requerida — Bearer Token (Firebase ID Token)                            |
| Motor de IA     | Google Gemini (via Google GenAI SDK)                                    |
| Persistencia    | Firebase Firestore                                                      |
| Modo de ejecución | Completamente asíncrono (`async/await`)                               |

### Criterios de Aceptación

---

#### Escenario 1: Creación exitosa de una tarea con priorización por IA

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que envía una petición POST a /api/v1/tasks
  Y que el cuerpo de la petición contiene un "title" no vacío y una "description" no vacía
Cuando el servidor recibe la petición
  Y valida el token de autenticación contra Firebase Auth
  Y envía el título y la descripción a la API de Gemini para determinar la prioridad
  Y Gemini devuelve un nivel de prioridad ("low", "medium" o "high")
  Y la tarea es persistida en Firestore con el campo "priority" asignado por la IA
Entonces la API responde con el código de estado HTTP 201 Created
  Y el cuerpo de la respuesta contiene el objeto de la tarea creada en formato JSON
  Y dicho objeto incluye un "id" único generado por Firestore
  Y el objeto incluye los campos "title", "description", "priority", "owner_uid" y "created_at"
  Y el campo "priority" refleja el valor retornado por Gemini
```

---

#### Escenario 2: Rechazo de la solicitud por cuerpo de petición inválido

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que envía una petición POST a /api/v1/tasks
  Y que el cuerpo de la petición está incompleto (por ejemplo, el campo "title" está vacío o ausente)
Cuando el servidor recibe la petición
  Y el validador de esquema (Pydantic) detecta los campos requeridos faltantes o inválidos
Entonces la API responde con el código de estado HTTP 422 Unprocessable Entity
  Y el cuerpo de la respuesta contiene un mensaje de error detallando qué campos son inválidos
  Y la API de Gemini no es invocada
  Y no se persiste ningún documento en Firestore
```

---

#### Escenario 3: Fallo en la comunicación con la API de Gemini

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que envía una petición POST /api/v1/tasks con datos válidos
Cuando el servidor intenta invocar a la API de Gemini
  Y la API de Gemini no está disponible o devuelve un error
Entonces la API responde con el código de estado HTTP 503 Service Unavailable
  Y el cuerpo de la respuesta contiene un mensaje de error indicando un fallo en el servicio de IA
  Y no se persiste ningún documento en Firestore
```

---

#### Escenario 4: Rechazo de la solicitud por token de autenticación ausente o inválido

```gherkin
Dado que el cliente envía una petición POST a /api/v1/tasks
  Y que la petición no incluye un header "Authorization" o el token es inválido/expirado
Cuando el servidor intenta validar el token contra Firebase Auth
  Y la validación falla
Entonces la API responde con el código de estado HTTP 401 Unauthorized
  Y el cuerpo de la respuesta contiene un mensaje de error de autenticación
  Y la API de Gemini no es invocada
  Y no se persiste ningún documento en Firestore
```

---

---

## HU-02 — Autenticación de Usuarios con Firebase Auth

### Descripción

> **Como** usuario de la aplicación,  
> **quiero** que cada petición que realice al backend sea verificada mediante mi identidad de Firebase,  
> **para** que solo yo pueda acceder y gestionar mis propios datos, garantizando la seguridad y privacidad de mi información.

### Información Adicional

| Campo               | Detalle                                                              |
|---------------------|----------------------------------------------------------------------|
| Mecanismo           | Verificación de Firebase ID Token (JWT) en cada petición protegida  |
| Header requerido    | `Authorization: Bearer <firebase_id_token>`                         |
| SDK utilizado       | Firebase Admin SDK                                                   |
| Alcance             | Aplica a todos los endpoints bajo `/api/v1/`                        |
| Modo de ejecución   | Completamente asíncrono (`async/await`)                             |

### Criterios de Aceptación

---

#### Escenario 1: Acceso exitoso a un recurso protegido con token válido

```gherkin
Dado que el usuario ha iniciado sesión previamente en el cliente de la aplicación
  Y que posee un Firebase ID Token vigente (no expirado)
  Y que incluye el token en el header "Authorization: Bearer <token>" de su petición
Cuando el servidor recibe la petición hacia cualquier endpoint protegido bajo /api/v1/
  Y el middleware de autenticación extrae el token del header
  Y verifica el token mediante Firebase Admin SDK de forma asíncrona
  Y el token es válido, no está expirado y corresponde a un usuario registrado
Entonces el servidor permite el acceso al recurso solicitado
  Y el contexto de la petición contiene el "uid" del usuario autenticado
  Y el "uid" es utilizado para asociar todas las operaciones de datos al usuario correcto
```

---

#### Escenario 2: Rechazo de acceso por token expirado

```gherkin
Dado que el usuario posee un Firebase ID Token que ha superado su tiempo de expiración
  Y que incluye dicho token en el header "Authorization: Bearer <token>"
Cuando el servidor recibe la petición hacia un endpoint protegido
  Y el middleware de autenticación intenta verificar el token mediante Firebase Admin SDK
  Y Firebase Admin SDK determina que el token está expirado
Entonces la API responde con el código de estado HTTP 401 Unauthorized
  Y el cuerpo de la respuesta contiene un mensaje indicando que la sesión ha expirado
  Y se deniega el acceso al recurso protegido
```

---

#### Escenario 3: Rechazo de acceso por token malformado o inválido

```gherkin
Dado que un cliente envía una petición a un endpoint protegido bajo /api/v1/
  Y que el header "Authorization" contiene un token que no es un Firebase ID Token legítimo
    (por ejemplo, un token modificado, un JWT de otro proveedor, o una cadena arbitraria)
Cuando el middleware de autenticación intenta verificar el token mediante Firebase Admin SDK
  Y Firebase Admin SDK detecta que la firma o estructura del token es inválida
Entonces la API responde con el código de estado HTTP 401 Unauthorized
  Y el cuerpo de la respuesta contiene un mensaje de error de autenticación genérico
  Y no se expone información interna sobre el motivo exacto del rechazo (por seguridad)
```

---

#### Escenario 4: Rechazo de acceso por ausencia del header de autorización

```gherkin
Dado que un cliente envía una petición a un endpoint protegido bajo /api/v1/
  Y que la petición no incluye el header "Authorization"
Cuando el middleware de autenticación procesa la petición
  Y detecta la ausencia del header requerido
Entonces la API responde con el código de estado HTTP 401 Unauthorized
  Y el cuerpo de la respuesta contiene un mensaje indicando que se requiere autenticación
  Y Firebase Admin SDK no es invocado innecesariamente
```

---

#### Escenario 5: Aislamiento de datos entre usuarios autenticados

```gherkin
Dado que el Usuario A y el Usuario B están ambos autenticados con tokens válidos distintos
  Y que el Usuario A ha creado tareas asociadas a su "uid"
Cuando el Usuario B envía una petición para listar o acceder a tareas
  Y el middleware extrae correctamente el "uid" del Usuario B desde su token
Entonces el Usuario B únicamente recibe los datos asociados a su propio "uid"
  Y los datos del Usuario A no son accesibles ni visibles para el Usuario B
```

---

---

## HU-03 — Filtrado de Tareas por Nivel de Prioridad

### Descripción

> **Como** usuario autenticado de la aplicación,  
> **quiero** poder consultar mis tareas filtrando por un nivel de prioridad específico (`low`, `medium` o `high`),  
> **para** enfocarme en lo que realmente importa en cada momento y gestionar mi tiempo de forma más efectiva.

### Información Adicional

| Campo              | Detalle                                                                 |
|--------------------|-------------------------------------------------------------------------|
| Endpoint           | `GET /api/v1/tasks?priority={valor}`                                    |
| Autenticación      | Requerida — Bearer Token (Firebase ID Token)                            |
| Parámetro          | `priority` (query param, opcional) — valores aceptados: `low`, `medium`, `high` |
| Persistencia       | Firebase Firestore — consulta filtrada por `owner_uid` y `priority`     |
| Modo de ejecución  | Completamente asíncrono (`async/await`)                                 |

### Criterios de Aceptación

---

#### Escenario 1: Filtrado exitoso por una prioridad válida

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que el usuario posee tareas creadas con distintos niveles de prioridad en Firestore
  Y que envía una petición GET a /api/v1/tasks?priority=high
Cuando el servidor recibe la petición
  Y valida el token de autenticación contra Firebase Auth
  Y ejecuta una consulta asíncrona en Firestore filtrando por "owner_uid" igual al UID del usuario
    Y además filtrando por el campo "priority" igual a "high"
Entonces la API responde con el código de estado HTTP 200 OK
  Y el cuerpo de la respuesta contiene una lista JSON con únicamente las tareas cuya prioridad es "high"
  Y cada objeto de la lista incluye los campos "id", "title", "description", "priority", "owner_uid" y "created_at"
  Y no se incluyen tareas de otros usuarios en la respuesta
```

---

#### Escenario 2: Filtrado exitoso que no retorna resultados

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que el usuario no posee ninguna tarea con prioridad "low" en Firestore
  Y que envía una petición GET a /api/v1/tasks?priority=low
Cuando el servidor ejecuta la consulta filtrada en Firestore
  Y no encuentra documentos que coincidan con los criterios
Entonces la API responde con el código de estado HTTP 200 OK
  Y el cuerpo de la respuesta contiene una lista JSON vacía: []
  Y no se retorna ningún código de error
```

---

#### Escenario 3: Listado de todas las tareas sin aplicar filtro

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que envía una petición GET a /api/v1/tasks sin el parámetro "priority"
Cuando el servidor recibe la petición
  Y valida el token de autenticación
  Y ejecuta una consulta asíncrona en Firestore filtrando únicamente por "owner_uid"
Entonces la API responde con el código de estado HTTP 200 OK
  Y el cuerpo de la respuesta contiene la lista completa de tareas del usuario, independientemente de su prioridad
```

---

#### Escenario 4: Rechazo de la solicitud por valor de prioridad inválido

```gherkin
Dado que el usuario está autenticado con un Firebase ID Token válido
  Y que envía una petición GET a /api/v1/tasks?priority=urgente
    (donde "urgente" no es un valor perteneciente al conjunto {"low", "medium", "high"})
Cuando el servidor recibe la petición
  Y el validador de parámetros detecta que el valor de "priority" no es válido
Entonces la API responde con el código de estado HTTP 422 Unprocessable Entity
  Y el cuerpo de la respuesta contiene un mensaje de error indicando los valores permitidos: "low", "medium", "high"
  Y no se realiza ninguna consulta a Firestore
```

---

#### Escenario 5: Rechazo de la solicitud por token de autenticación ausente o inválido

```gherkin
Dado que un cliente envía una petición GET a /api/v1/tasks?priority=high
  Y que la petición no incluye un header "Authorization" o el token es inválido/expirado
Cuando el servidor intenta validar el token contra Firebase Auth
  Y la validación falla
Entonces la API responde con el código de estado HTTP 401 Unauthorized
  Y el cuerpo de la respuesta contiene un mensaje de error de autenticación
  Y no se realiza ninguna consulta a Firestore
```

---

#### Escenario 6: Aislamiento de datos — el filtro solo actúa sobre las tareas del usuario autenticado

```gherkin
Dado que el Usuario A y el Usuario B están autenticados y ambos poseen tareas con prioridad "medium"
Cuando el Usuario A envía una petición GET a /api/v1/tasks?priority=medium
Entonces la respuesta contiene únicamente las tareas con prioridad "medium" pertenecientes al Usuario A
  Y las tareas del Usuario B con prioridad "medium" no aparecen en la respuesta
```

---

*Fin del documento de Historias de Usuario — TaskMind-API MVP*
