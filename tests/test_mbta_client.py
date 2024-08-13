# tests/test_mbta_client.py
import pytest
from unittest.mock import patch
from mbta_client import MBTAClient

# Sample data for mocking
sample_route_data = {
    "data": [
        {
            "id": "1",
            "type": "route",
            "attributes": {
                "long_name": "Green Line",
                "short_name": "GL",
                "type": 0
            }
        }
    ]
}

# Test the get_routes method
def test_get_routes():
    client = MBTAClient(api_key="test_key")

    with patch('mbtaclient.requests.get') as mock_get:
        # Mock the response to return our sample data
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = sample_route_data
        
        routes = client.get_routes()
        assert len(routes) == 1
        assert routes[0].get("id") == "1"
        assert routes[0]["attributes"]["long_name"] == "Green Line"

# Test error handling in get_routes method
def test_get_routes_error_handling():
    client = MBTAClient(api_key="test_key")

    with patch('mbtaclient.requests.get') as mock_get:
        # Mock the response to return an error status code
        mock_get.return_value.status_code = 404
        
        with pytest.raises(Exception):
            client.get_routes()
