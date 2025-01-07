import pytest

from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientConnectionError, ClientResponseError, RequestInfo
from yarl import URL

from src.mbtaclient.mbta_client import MBTAClient, MBTA_DEFAULT_HOST, ENDPOINTS
from src.mbtaclient.mbta_route import MBTARoute


@pytest.mark.asyncio
async def test_get_route():
    async def mock_fetch_data(url, params):
        return {'data': {'id': 'route-xyz'}}

    client = MBTAClient()
    client._fetch_data = AsyncMock(side_effect=mock_fetch_data)
    route = await client.get_route('route-xyz')
    assert route.id == 'route-xyz'
    client._fetch_data.assert_called_once_with(f'{ENDPOINTS["ROUTES"]}/route-xyz', None)
    await client.close()


@pytest.mark.asyncio
async def test_get_route_error():
    async def mock_request(method, url, params=None):
        return MagicMock(json=AsyncMock(return_value={}))

    client = MBTAClient()
    client.request = AsyncMock(side_effect=mock_request)
    with patch.object(client, 'logger', MagicMock()) as mock_logger:
        with pytest.raises(ValueError) as excinfo:
            await client.get_route('route-xyz')
        assert str(excinfo.value) == "missing 'data'"
        mock_logger.error.assert_called_once_with("Error fetching data: missing 'data'")
    await client.close()


@pytest.mark.asyncio
async def test_list_routes():
    async def mock_fetch_data(url, params):
        return {'data': [{'id': 'route-1'}, {'id': 'route-2'}]}

    client = MBTAClient()
    client._fetch_data = AsyncMock(side_effect=mock_fetch_data)
    routes = await client.list_routes()
    assert len(routes) == 2
    assert isinstance(routes[0], MBTARoute)
    client._fetch_data.assert_called_once_with(ENDPOINTS['ROUTES'], None)
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
        mock_logger.error.assert_called_once_with('Connection error: Connection error')
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
        mock_logger.error.assert_called_once_with(
            'Client response error: 404 - 404, message=\'Not Found\', url=URL(\'https://api-v3.mbta.com/test\')'
        )
    await client.close()


@pytest.mark.asyncio
async def test_request_success():
    async def mock_request(*args, **kwargs):
        return MagicMock(status=200, json=AsyncMock(return_value={}))

    client = MBTAClient()
    client._session.request = AsyncMock(side_effect=mock_request)
    response = await client.request('get', 'test')
    assert response.status == 200
    client._session.request.assert_called_once_with(
        'get',
        f'https://{MBTA_DEFAULT_HOST}/test',
        params={},
    )
    await client.close()