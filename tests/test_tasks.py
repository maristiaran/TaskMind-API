"""Tests del router de tareas: POST /api/v1/tasks/."""

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
