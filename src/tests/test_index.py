from api.app import app
from api.config import TestingConfig
app.config.from_object(TestingConfig)

def test_index_route():
    response = app.test_client().get('/')
    assert response.status_code == 200