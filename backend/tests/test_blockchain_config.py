import pytest

@pytest.mark.asyncio
async def test_blockchain_config_endpoint(client):
    response = await client.get("/api/v1/blockchain/config")
    assert response.status_code == 200
    data = response.json()
    assert data["chain_id"] == 31337
    assert data["network_name"] == "hardhat"
    assert "contracts" in data
    assert "IssuerRegistry" in data["contracts"]
    assert "CredentialRegistry" in data["contracts"]
    assert "CredentialStatusRegistry" in data["contracts"]
