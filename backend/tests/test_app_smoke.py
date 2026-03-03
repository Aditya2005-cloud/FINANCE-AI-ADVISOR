import unittest

from finance_ai import main


class AppFactorySmokeTests(unittest.TestCase):
    def test_app_registers_core_routes(self):
        app = main({}, **{"sqlalchemy.url": "sqlite:///:memory:"})
        route_names = {route.name for route in app.routes_mapper.get_routes()}

        self.assertIn("home", route_names)
        self.assertIn("predict", route_names)
        self.assertIn("predictions", route_names)


if __name__ == "__main__":
    unittest.main()
