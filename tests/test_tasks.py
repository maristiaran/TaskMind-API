"""Tests del router de tareas: POST /api/v1/tasks/ y GET /api/v1/tasks/."""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from tests.conftest import unauthenticated_client  # noqa: F401  (fixture re-export)


@pytest.mark.asyncio
async def test_create_task_retorna_201_y_estructura_correcta(client: AsyncClient):
    """Una petición válida debe crear la tarea y retornar HTTP 201
    con todos los campos esperados en el cuerpo de la respuesta."""
    payload = {
        "title": "Preparar informe mensual",
        "description": "Redactar el resumen ejecutivo de ventas del trimestre.",
    }

    response = await client.post(
        "/api/v1/tasks/",
        json=payload,
        headers={"Authorization": "Bearer fake-token-para-test"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-task-id-abc123"
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["priority"] == "medium"
    assert data["owner_uid"] == "test-user-uid-001"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_task_sin_titulo_retorna_422(client: AsyncClient):
    """Una petición sin campo `title` debe ser rechazada con HTTP 422
    por la validación de Pydantic antes de llegar a la lógica de negocio."""
    payload = {"description": "Descripción sin título"}

    response = await client.post(
        "/api/v1/tasks/",
        json=payload,
        headers={"Authorization": "Bearer fake-token-para-test"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_titulo_vacio_retorna_422(client: AsyncClient):
    """Un `title` vacío debe fallar la validación de longitud mínima (min_length=1)."""
    payload = {"title": "", "description": "Descripción válida"}

    response = await client.post(
        "/api/v1/tasks/",
        json=payload,
        headers={"Authorization": "Bearer fake-token-para-test"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_sin_header_auth_retorna_401(
    unauthenticated_client: AsyncClient,
):
    """Una petición sin header Authorization debe ser rechazada con HTTP 401
    por el esquema HTTPBearer antes de evaluar el token.

    Usa `unauthenticated_client` que NO sobreescribe `get_current_user_uid`,
    permitiendo que FastAPI ejecute la validación real del header.
    """
    payload = {
        "title": "Tarea sin auth",
        "description": "No debería procesarse.",
    }

    response = await unauthenticated_client.post("/api/v1/tasks/", json=payload)

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/tasks/ — Filtrado por prioridad (HU-03)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_tasks_filtra_por_prioridad_high(
    client: AsyncClient, mock_firestore: MagicMock
):
    """GET /api/v1/tasks/?priority=high debe retornar HTTP 200 con únicamente
    las tareas cuyo campo 'priority' sea 'high'.

    Este test falla intencionalmente hasta que el endpoint GET sea implementado,
    siguiendo la metodología TDD (Red → Green → Refactor).

    Estrategia de mock:
    - Se simulan dos documentos Firestore con priority='high'.
    - Se configura la cadena de consulta:
        collection().where("owner_uid", ...).where("priority", ...).stream()
    - `stream()` se implementa como un generador asíncrono que devuelve
      los documentos simulados, replicando el comportamiento de Firestore.
    """
    # --- Documentos Firestore simulados ---
    mock_doc_1 = MagicMock()
    mock_doc_1.id = "task-high-001"
    mock_doc_1.to_dict.return_value = {
        "title": "Desplegar a producción",
        "description": "Ejecutar el pipeline de CI/CD antes del cierre de sprint.",
        "priority": "high",
        "owner_uid": "test-user-uid-001",
        "created_at": "2026-06-13T10:00:00+00:00",
    }

    mock_doc_2 = MagicMock()
    mock_doc_2.id = "task-high-002"
    mock_doc_2.to_dict.return_value = {
        "title": "Resolver bug crítico en pagos",
        "description": "El servicio de cobros arroja 500 en el 3% de las transacciones.",
        "priority": "high",
        "owner_uid": "test-user-uid-001",
        "created_at": "2026-06-13T11:30:00+00:00",
    }

    # --- Generador asíncrono que replica Firestore Query.stream() ---
    async def fake_stream():
        yield mock_doc_1
        yield mock_doc_2

    # --- Configurar la cadena: collection().where().where().stream() ---
    # Representa: db.collection("tasks")
    #               .where("owner_uid", "==", uid)
    #               .where("priority", "==", "high")
    #               .stream()
    mock_query = MagicMock()
    mock_query.stream = fake_stream
    mock_firestore.collection.return_value.where.return_value.where.return_value = (
        mock_query
    )

    # --- Petición al endpoint ---
    response = await client.get(
        "/api/v1/tasks/",
        params={"priority": "high"},
        headers={"Authorization": "Bearer fake-token-para-test"},
    )

    # --- Assertions ---
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) == 2
    assert all(t["priority"] == "high" for t in tasks)
    assert tasks[0]["id"] == "task-high-001"
    assert tasks[1]["id"] == "task-high-002"
    # Verificar que Firestore fue consultado con la colección correcta
    mock_firestore.collection.assert_called_with("tasks")



