import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

from src.mbtaclient.mbta_utils import MBTAUtils, memoize_async


class TestMBTAUtils:
    @pytest.fixture
    def now(self):
        return datetime.now()

    @staticmethod
    def make_hashable(item):
        if isinstance(item, dict):
            return frozenset((TestMBTAUtils.make_hashable(k), TestMBTAUtils.make_hashable(v)) for k, v in item.items())
        return str(item)

    def test_get_route_type_desc_by_type_id(self):
        assert MBTAUtils.get_route_type_desc_by_type_id(0) == "Subway"
        assert MBTAUtils.get_route_type_desc_by_type_id(1) == "Subway"
        assert MBTAUtils.get_route_type_desc_by_type_id(2) == "Commuter Rail"
        assert MBTAUtils.get_route_type_desc_by_type_id(3) == "Bus"
        assert MBTAUtils.get_route_type_desc_by_type_id(4) == "Ferry"
        assert MBTAUtils.get_route_type_desc_by_type_id(5) == "Unknown"

    def test_get_uncertainty_description(self):
        assert MBTAUtils.get_uncertainty_description("60") == "Trip that has already started"
        assert MBTAUtils.get_uncertainty_description("120") == (
            "Trip not started and a vehicle is awaiting departure at the origin"
        )
        assert MBTAUtils.get_uncertainty_description("300") == "Vehicle has not yet been assigned to the trip"
        assert MBTAUtils.get_uncertainty_description("301") == (
            "Vehicle appears to be stalled or significantly delayed"
        )
        assert MBTAUtils.get_uncertainty_description("360") == (
            "Trip not started and a vehicle is completing a previous trip"
        )
        assert MBTAUtils.get_uncertainty_description("invalid") == "None"

    def test_time_to(self, now):
        future_time = now + timedelta(minutes=10)
        past_time = now - timedelta(minutes=5)

        # Test with valid time
        assert pytest.approx(MBTAUtils.time_to(future_time, now)) == 600, 1

        # Test with past time
        assert pytest.approx(MBTAUtils.time_to(past_time, now)) == -300, 1

        # Test with None time
        assert MBTAUtils.time_to(None, now) is None

        # Test with different timezones
        aware_time1 = now.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
        aware_time2 = now.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        assert pytest.approx(MBTAUtils.time_to(aware_time1, aware_time2)) == 32400.0, 1

    def test_calculate_time_difference(self, now):
        real_time = now + timedelta(minutes=5)
        scheduled_time = now

        # Test with valid times
        assert pytest.approx(MBTAUtils.calculate_time_difference(real_time, scheduled_time)) == 300, 1

        # Test with None times
        assert MBTAUtils.calculate_time_difference(None, scheduled_time) is None
        assert MBTAUtils.calculate_time_difference(real_time, None) is None
        assert MBTAUtils.calculate_time_difference(None, None) is None

    def test_parse_datetime(self):
        time_str = "2023-11-20T10:30:00+00:00"

        # Test with valid ISO 8601 string
        parsed_time = MBTAUtils.parse_datetime(time_str)
        assert parsed_time is not None
        assert parsed_time.isoformat() == time_str

        # Test with invalid string
        time_str = "invalid_time"
        parsed_time = MBTAUtils.parse_datetime(time_str)
        assert parsed_time is None

        # Test with non-string input
        parsed_time = MBTAUtils.parse_datetime(123)
        assert parsed_time is None

        @pytest.mark.asyncio
        @patch('src.mbtaclient.mbta_utils.logger.debug')
        @patch('src.mbtaclient.mbta_utils.logger.error')
        async def test_memoize_async(self, mock_error, mock_debug):
            @memoize_async()
            async def my_func(arg1, arg2):
                return arg1 + arg2

            # First call should miss the cache
            result1 = await my_func(1, 2)
            assert result1 == 3

            # Assert that both the 'Cache miss' and 'Cache updated' logs are called
            mock_debug.assert_any_call(f"Cache miss for my_func with arguments {(TestMBTAUtils.make_hashable(1), TestMBTAUtils.make_hashable(2))} at {datetime.now().isoformat()}")
            mock_debug.assert_any_call(f"Cache updated for key: {(TestMBTAUtils.make_hashable(1), TestMBTAUtils.make_hashable(2))} at {datetime.now().isoformat()}")

            # Second call should hit the cache
            result2 = await my_func(1, 2)
            assert result2 == 3

            # Check if cache hit log is called
            mock_debug.assert_any_call(f"Cache hit for my_func with arguments {(TestMBTAUtils.make_hashable(1), TestMBTAUtils.make_hashable(2))} at {datetime.now().isoformat()}")

            # Call with different arguments should miss the cache
            result3 = await my_func(1, 3)
            assert result3 == 4
            mock_debug.assert_any_call(f"Cache miss for my_func with arguments {(TestMBTAUtils.make_hashable(1), TestMBTAUtils.make_hashable(3))} at {datetime.now().isoformat()}")
            mock_debug.assert_any_call(f"Cache updated for key: {(TestMBTAUtils.make_hashable(1), TestMBTAUtils.make_hashable(3))} at {datetime.now().isoformat()}")

            # Test error handling
            @memoize_async()
            async def my_func_error(arg):
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                await my_func_error(1)
            mock_error.assert_called_with(f"Error occurred while executing my_func_error with arguments (1,): Test error")

