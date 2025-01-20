import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientConnectionError, ClientResponseError, RequestInfo
from yarl import URL

from src.mbtaclient.client.mbta_client import MBTAClient, MBTA_DEFAULT_HOST, ENDPOINTS
from src.mbtaclient.models.mbta_route import MBTARoute
from src.mbtaclient.models.mbta_trip import MBTATrip
from src.mbtaclient.models.mbta_stop import MBTAStop
from src.mbtaclient.models.mbta_schedule import MBTASchedule
from src.mbtaclient.models.mbta_prediction import MBTAPrediction
from src.mbtaclient.models.mbta_alert import MBTAAlert

@pytest.mark.asyncio
async def test_fetch_route():
    async def mock_fetch_data(path, params):
        return {"data": {"id": "Red"}}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            route, _ = await client.fetch_route('Red')
            assert route.id == 'Red'
            mock_method.assert_called_once_with(f'{ENDPOINTS["ROUTES"]}/Red', None)


@pytest.mark.asyncio
async def test_fetch_trip():
    async def mock_fetch_data(path, params):
        return {"data": {"id": "66715083"}}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            trip, _ = await client.fetch_trip('66715083')
            assert trip.id == '66715083'
            mock_method.assert_called_once_with(f'{ENDPOINTS["TRIPS"]}/66715083', None)


@pytest.mark.asyncio
async def test_fetch_stop():
    async def mock_fetch_data(path, params):
        return {"data": {"id": "1936"}}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            stop, _ = await client.fetch_stop('1936')
            assert stop.id == '1936'
            mock_method.assert_called_once_with(f'{ENDPOINTS["STOPS"]}/1936', None)


@pytest.mark.asyncio
async def test_fetch_routes():
    async def mock_fetch_data(path, params):
        return {"data": [{"id": "Red"}, {"id": "Orange"}]}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            routes, _ = await client.fetch_routes()
            assert len(routes) == 2
            assert isinstance(routes[0], MBTARoute)
            mock_method.assert_called_once_with(ENDPOINTS["ROUTES"], None)


@pytest.mark.asyncio
async def test_fetch_schedules():
    async def mock_fetch_data(path, params):
        return {"data": [{"id": "schedule-1"}, {"id": "schedule-2"}]}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            schedules, _ = await client.fetch_schedules()
            assert len(schedules) == 2
            assert isinstance(schedules[0], MBTASchedule)
            mock_method.assert_called_once_with(ENDPOINTS["SCHEDULES"], None)


@pytest.mark.asyncio
async def test_fetch_predictions():
    async def mock_fetch_data(path, params):
        return {"data": [{"id": "prediction-1"}, {"id": "prediction-2"}]}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            predictions, _ = await client.fetch_predictions()
            assert len(predictions) == 2
            assert isinstance(predictions[0], MBTAPrediction)
            mock_method.assert_called_once_with(ENDPOINTS["PREDICTIONS"], None)


@pytest.mark.asyncio
async def test_fetch_alerts():
    async def mock_fetch_data(path, params):
        return {"data": [{"id": "alert-1"}, {"id": "alert-2"}]}, 0.0

    async with MBTAClient() as client:
        with patch.object(client, '_fetch_data', side_effect=mock_fetch_data) as mock_method:
            alerts, _ = await client.fetch_alerts()
            assert len(alerts) == 2
            assert isinstance(alerts[0], MBTAAlert)
            mock_method.assert_called_once_with(ENDPOINTS["ALERTS"], None)


@pytest.mark.asyncio
async def test_request_connection_error():
    async def mock_request(*args, **kwargs):
        raise ClientConnectionError("Connection error")

    async with MBTAClient() as client:
        with patch.object(client, "request", side_effect=mock_request):
            with pytest.raises(ClientConnectionError):
                await client.request("GET", "/test")


@pytest.mark.asyncio
async def test_request_client_response_error():
    request_info = RequestInfo(
        url=URL(f"https://{MBTA_DEFAULT_HOST}/test"),
        method="GET",
        headers={},
    )

    async def mock_request(*args, **kwargs):
        raise ClientResponseError(
            request_info=request_info,
            history=None,
            status=404,
            message="Not Found",
            headers=None,
        )

    async with MBTAClient() as client:
        with patch.object(client, "request", side_effect=mock_request):
            with pytest.raises(ClientResponseError) as exc:
                await client.request("GET", "/test")
            assert exc.value.status == 404
