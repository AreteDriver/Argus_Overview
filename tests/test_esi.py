"""
Unit tests for the ESI integration module.

Tests cover:
- ESIClient HTTP operations and rate limiting
- UniverseCache system name lookups
- RouteService jump calculations
"""

import time
from unittest.mock import MagicMock, patch

from argus_overview.esi.client import ESIClient
from argus_overview.esi.route_service import RouteService
from argus_overview.esi.universe_cache import UniverseCache


class TestESIClient:
    """Tests for ESIClient HTTP operations"""

    def test_client_initialization(self):
        """ESIClient initializes with default settings"""
        client = ESIClient()
        assert client.BASE_URL == "https://esi.evetech.net/latest"
        assert client.timeout == 10.0
        assert client._error_limit_remain == 100
        client.close()

    def test_client_with_custom_timeout(self):
        """ESIClient accepts custom timeout"""
        client = ESIClient(timeout=30.0)
        assert client.timeout == 30.0
        client.close()

    @patch("httpx.Client.get")
    def test_get_success(self, mock_get):
        """GET request returns parsed JSON on success"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [30000142, 30000143, 30000144]
        mock_response.headers = {}
        mock_get.return_value = mock_response

        client = ESIClient()
        result = client.get("/route/30000142/30001161/")

        assert result == [30000142, 30000143, 30000144]
        client.close()

    @patch("httpx.Client.get")
    def test_get_404_returns_none(self, mock_get):
        """GET request returns None on 404"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_get.return_value = mock_response

        client = ESIClient()
        result = client.get("/route/invalid/path/")

        assert result is None
        client.close()

    @patch("httpx.Client.get")
    def test_rate_limit_headers_parsed(self, mock_get):
        """Rate limit headers are parsed from response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {
            "X-ESI-Error-Limit-Remain": "50",
            "X-ESI-Error-Limit-Reset": "30",
        }
        mock_get.return_value = mock_response

        client = ESIClient()
        client.get("/test/")

        assert client._error_limit_remain == 50
        client.close()

    @patch("httpx.Client.post")
    def test_post_success(self, mock_post):
        """POST request returns parsed JSON on success"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"systems": [{"id": 30000142, "name": "Jita"}]}
        mock_response.headers = {}
        mock_post.return_value = mock_response

        client = ESIClient()
        result = client.post("/universe/ids/", json_data=["Jita"])

        assert result["systems"][0]["id"] == 30000142
        client.close()


class TestUniverseCache:
    """Tests for UniverseCache system lookups"""

    def test_cache_initialization(self):
        """UniverseCache initializes and loads bundled data"""
        cache = UniverseCache()
        # Should have loaded systems from bundled data
        assert len(cache) > 0

    def test_get_system_id_cached(self):
        """Returns cached system ID"""
        cache = UniverseCache()
        cache.add_system("Jita", 30000142)

        result = cache.get_system_id("Jita")
        assert result == 30000142

    def test_get_system_id_case_insensitive(self):
        """System lookup is case-insensitive"""
        cache = UniverseCache()
        cache.add_system("Jita", 30000142)

        assert cache.get_system_id("jita") == 30000142
        assert cache.get_system_id("JITA") == 30000142
        assert cache.get_system_id("JiTa") == 30000142

    def test_get_system_name(self):
        """Returns system name by ID"""
        cache = UniverseCache()
        cache.add_system("Jita", 30000142)

        result = cache.get_system_name(30000142)
        assert result == "Jita"

    def test_get_unknown_system_returns_none(self):
        """Returns None for unknown system (without ESI client)"""
        cache = UniverseCache()
        result = cache.get_system_id("InvalidSystemXYZ123")
        assert result is None

    def test_contains_check(self):
        """Can check if system is in cache"""
        cache = UniverseCache()
        cache.add_system("Jita", 30000142)

        assert cache.contains("Jita") is True
        assert cache.contains("jita") is True
        assert cache.contains("InvalidSystem") is False

    def test_bundled_systems_loaded(self):
        """Bundled systems.json is loaded on init"""
        cache = UniverseCache()

        # These should be in the bundled data
        jita_id = cache.get_system_id("Jita")
        assert jita_id == 30000142

        hed_id = cache.get_system_id("HED-GP")
        assert hed_id == 30001161

    @patch.object(UniverseCache, "_lookup_system_esi")
    def test_fallback_to_esi(self, mock_lookup):
        """Falls back to ESI for unknown systems"""
        mock_lookup.return_value = 99999999

        esi_client = MagicMock()
        cache = UniverseCache(esi_client=esi_client)

        _ = cache.get_system_id("NewSystemXYZ")

        # Should have attempted ESI lookup
        mock_lookup.assert_called_once_with("NewSystemXYZ")


class TestRouteService:
    """Tests for RouteService jump calculations"""

    def test_route_service_initialization(self):
        """RouteService initializes with ESI client and cache"""
        service = RouteService()
        assert service.esi_client is not None
        assert service.universe_cache is not None
        service.close()

    def test_same_system_returns_zero(self):
        """Route to same system returns 0 jumps"""
        service = RouteService()

        result = service.calculate_jumps("Jita", "Jita")
        assert result == 0

        result = service.calculate_jumps("jita", "JITA")
        assert result == 0

        service.close()

    def test_empty_origin_returns_none(self):
        """Empty origin returns None"""
        service = RouteService()
        result = service.calculate_jumps("", "Jita")
        assert result is None
        service.close()

    def test_empty_destination_returns_none(self):
        """Empty destination returns None"""
        service = RouteService()
        result = service.calculate_jumps("Jita", "")
        assert result is None
        service.close()

    def test_route_flag_setting(self):
        """Route flag can be changed"""
        service = RouteService()

        service.set_route_flag("secure")
        assert service._route_flag == "secure"

        service.set_route_flag("insecure")
        assert service._route_flag == "insecure"

        service.set_route_flag("shortest")
        assert service._route_flag == "shortest"

        service.close()

    def test_invalid_route_flag_ignored(self):
        """Invalid route flag is ignored"""
        service = RouteService()
        service.set_route_flag("invalid")
        assert service._route_flag == "shortest"  # Default unchanged
        service.close()

    def test_cache_key_generation(self):
        """Cache key includes origin, destination, and flag"""
        service = RouteService()

        key = service._cache_key("Jita", "HED-GP", "shortest")
        assert key == "jita:hed-gp:shortest"

        key = service._cache_key("Amarr", "Dodixie", "secure")
        assert key == "amarr:dodixie:secure"

        service.close()

    def test_route_caching(self):
        """Routes are cached and returned from cache"""
        service = RouteService()

        # Manually cache a route
        cache_key = "jita:amarr:shortest"
        service._cache_route(cache_key, 15)

        # Should get from cache
        result = service._get_cached_route(cache_key)
        assert result == 15

        service.close()

    def test_cache_expiration(self):
        """Cached routes expire after TTL"""
        service = RouteService()
        service._cache_ttl = 0.1  # 100ms for testing

        cache_key = "test:route:shortest"
        service._cache_route(cache_key, 10)

        # Should get from cache immediately
        assert service._get_cached_route(cache_key) == 10

        # Wait for expiration
        time.sleep(0.15)

        # Should return None after expiration
        assert service._get_cached_route(cache_key) is None

        service.close()

    def test_cache_stats(self):
        """Cache stats returns size and system count"""
        service = RouteService()

        service._cache_route("a:b:shortest", 5)
        service._cache_route("c:d:shortest", 10)

        stats = service.get_cache_stats()
        assert stats["size"] == 2
        assert stats["systems_loaded"] > 0

        service.close()

    def test_clear_cache(self):
        """Cache can be cleared"""
        service = RouteService()

        service._cache_route("a:b:shortest", 5)
        service._cache_route("c:d:shortest", 10)

        service.clear_cache()

        assert service.get_cache_stats()["size"] == 0
        service.close()

    @patch.object(ESIClient, "get")
    def test_route_calculation_via_esi(self, mock_get):
        """Route calculation calls ESI and returns jump count"""
        # ESI returns list of system IDs in the route
        mock_get.return_value = [30000142, 30000143, 30000144, 30000145]

        service = RouteService()

        # Mock that both systems are in cache
        service.universe_cache.add_system("Origin", 30000142)
        service.universe_cache.add_system("Dest", 30000145)

        result = service.calculate_jumps("Origin", "Dest")

        # Route has 4 systems, so 3 jumps
        assert result == 3

        service.close()

    @patch.object(ESIClient, "get")
    def test_route_calculation_unknown_system(self, mock_get):
        """Route calculation fails gracefully for unknown systems"""
        service = RouteService()

        # System not in cache and no ESI fallback
        result = service.calculate_jumps("UnknownOrigin123", "UnknownDest456")

        # Should return None
        assert result is None
        service.close()


class TestESIIntegration:
    """Integration tests for ESI module components"""

    def test_route_service_uses_universe_cache(self):
        """RouteService correctly uses UniverseCache for lookups"""
        service = RouteService()

        # Jita should be in the bundled cache
        jita_id = service.universe_cache.get_system_id("Jita")
        assert jita_id == 30000142

        service.close()

    def test_cache_persists_across_lookups(self):
        """System IDs are cached after ESI lookup"""
        cache = UniverseCache()
        cache.add_system("TestSystem", 12345678)

        # Verify it's in cache
        assert cache.get_system_id("TestSystem") == 12345678
        assert cache.get_system_name(12345678) == "TestSystem"

    @patch.object(ESIClient, "get")
    def test_route_signals_emitted(self, mock_get):
        """RouteService emits signals on success/failure"""
        mock_get.return_value = [30000142, 30000143]

        service = RouteService()
        service.universe_cache.add_system("A", 30000142)
        service.universe_cache.add_system("B", 30000143)

        # Track signal emissions
        signals_received = []
        service.route_calculated.connect(
            lambda o, d, j: signals_received.append(("calculated", o, d, j))
        )

        result = service.calculate_jumps("A", "B")

        assert result == 1
        assert len(signals_received) == 1
        assert signals_received[0] == ("calculated", "A", "B", 1)

        service.close()
