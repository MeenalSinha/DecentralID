import pytest

@pytest.mark.asyncio
async def test_liveness_probe(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data

@pytest.mark.asyncio
async def test_readiness_probe(client):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"]["status"] == "healthy"
    assert "blockchain" in data
    assert data["blockchain"]["chain_id"] == 31337
