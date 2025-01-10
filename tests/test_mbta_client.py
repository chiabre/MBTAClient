import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientConnectionError, ClientResponseError, RequestInfo
from yarl import URL

from src.mbtaclient.client import MBTAClient, MBTA_DEFAULT_HOST, ENDPOINTS
from src.mbtaclient.route import MBTARoute
from src.mbtaclient.trip import MBTATrip
from src.mbtaclient.stop import MBTAStop
from src.mbtaclient.schedule import MBTASchedule
from src.mbtaclient.prediction import MBTAPrediction
from src.mbtaclient.alert import MBTAAlert


@pytest.mark.asyncio
async def test_get_route():
    async def mock_fetch_data(url, params):
        return {'data': {'id': 'Red'}}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        route: MBTARoute = await client.get_route('Red')
        assert route.id == 'Red'
        client._fetch_data.assert_called_once_with(f'{ENDPOINTS["ROUTES"]}/Red', None)
    await client.close()


@pytest.mark.asyncio
async def test_get_trip():
    async def mock_fetch_data(url, params):
        return {'data': {'id': '66715083'}}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        trip: MBTATrip = await client.get_trip('66715083')
        assert trip.id == '66715083'
        client._fetch_data.assert_called_once_with(f'{ENDPOINTS["TRIPS"]}/66715083', None)
    await client.close()


@pytest.mark.asyncio
async def test_get_stop():
    async def mock_fetch_data(url, params):
        return {'data': {'id': '1936'}}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        stop: MBTAStop = await client.get_stop('1936')
        assert stop.id == '1936'
        client._fetch_data.assert_called_once_with(f'{ENDPOINTS["STOPS"]}/1936', None)
    await client.close()


@pytest.mark.asyncio
async def test_list_routes():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': 'Red'}, {'id': 'Orange'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        routes: list[MBTARoute] = await client.list_routes()
        assert len(routes) == 2
        assert isinstance(routes[0], MBTARoute)
        client._fetch_data.assert_called_once_with(ENDPOINTS['ROUTES'], None)
    await client.close()


@pytest.mark.asyncio
async def test_list_trips():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': '66715083'}, {'id': '66715084'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        trips: list[MBTATrip] = await client.list_trips()
        assert len(trips) == 2
        assert isinstance(trips[0], MBTATrip)
        client._fetch_data.assert_called_once_with(ENDPOINTS['TRIPS'], None)
    await client.close()


@pytest.mark.asyncio
async def test_list_stops():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': '1936'}, {'id': '3831'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        stops: list[MBTAStop] = await client.list_stops()
        assert len(stops) == 2
        assert isinstance(stops[0], MBTAStop)
        client._fetch_data.assert_called_once_with(ENDPOINTS['STOPS'], None)
    await client.close()


@pytest.mark.asyncio
async def test_list_schedules():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': 'schedule-66715083-70094-50'}, {'id': 'schedule-66715083-70090-70'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        schedules: list[MBTASchedule] = await client.list_schedules()
        assert len(schedules) == 2
        assert isinstance(schedules[0], MBTASchedule)
        client._fetch_data.assert_called_once_with(ENDPOINTS['SCHEDULES'], None)
    await client.close()


@pytest.mark.asyncio
async def test_list_predictions():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': 'prediction-66715348-70105-1-Red'}, {'id': 'prediction-66715346-70105-1-Red'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        predictions: list[MBTAPrediction] = await client.list_predictions()
        assert len(predictions) == 2
        assert isinstance(predictions[0], MBTAPrediction)
        client._fetch_data.assert_called_once_with(ENDPOINTS['PREDICTIONS'], None)
    await client.close()


@pytest.mark.asyncio
async def test_list_alerts():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': '382310'}, {'id': '620609'}]}

    client = MBTAClient()
    with patch.object(client, '_fetch_data', side_effect=mock_fetch_data):
        alerts: list[MBTAAlert] = await client.list_alerts()
        assert len(alerts) == 2
        assert isinstance(alerts[0], MBTAAlert)
        client._fetch_data.assert_called_once_with(ENDPOINTS['ALERTS'], None)
    await client.close()


@pytest.mark.asyncio
async def test_request_connection_error():
    async def mock_request(*args, **kwargs):
        raise ClientConnectionError('Connection error')

    client = MBTAClient()
    client._session.request = AsyncMock(side_effect=mock_request)
    with patch.object(client, 'logger', MagicMock()) as mock_logger:
        with pytest.raises(ClientConnectionError):
            await client.request('get', '/test')
        mock_logger.error.assert_any_call('Connection error: Connection error')
    await client.close()


@pytest.mark.asyncio
async def test_request_client_response_error():
    request_info = RequestInfo(
        url=URL("https://api-v3.mbta.com/test"),
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

    client = MBTAClient()
    client._session.request = AsyncMock(side_effect=mock_request)
    with patch.object(client, 'logger', MagicMock()) as mock_logger:
        with pytest.raises(ClientResponseError):
            await client.request('get', '/test')
        
        logged_error = mock_logger.error.call_args[0][0]
        assert "Client response error" in logged_error
        assert "404 - 404" in logged_error
        assert "message='Not Found'" in logged_error
        expected_url = "url='https://api-v3.mbta.com/test'"
        logged_url = f"url='{str(request_info.url)}'"
        assert logged_url in expected_url
    await client.close()


@pytest.mark.asyncio
async def test_request_success():
    async def mock_request(*args, **kwargs):
        return MagicMock(status=200, json=AsyncMock(return_value={}))

    client = MBTAClient()
    client._session.request = AsyncMock(side_effect=mock_request)
    with patch.object(client._session, 'request', side_effect=mock_request):
        response = await client.request('get', 'test')
        assert response.status == 200
        client._session.request.assert_called_once_with(
            'get',
            f'https://{MBTA_DEFAULT_HOST}/test',
            params={},
        )
    await client.close()
