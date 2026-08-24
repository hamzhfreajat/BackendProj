from fastapi.testclient import TestClient
from test_exception import app

client = TestClient(app)
response = client.get("/test")
print("STATUS CODE:", response.status_code)
print("BODY:", response.json())
