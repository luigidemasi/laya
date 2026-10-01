# Copyright 2026 Luigi De Masi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run with python -m unittest; no model download or inference needed."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from laya.serve import create_app as create_laya_app

from app import create_app


class Router:
    def predict(self, state, questions, model=None):
        return {"model": "fixture", "usage": {}, "answers": {"q": {"type": "noul", "noul": 0.9}}}


class PathTest(unittest.TestCase):
    def client(self, path):
        def native_app():
            return create_laya_app(router=Router())

        with patch.dict(os.environ, {"LAYA_API_PATH": path, "LAYA_API_KEY": "test-key"}), \
                patch("app.create_laya_app", side_effect=native_app):
            return TestClient(create_app())

    def test_custom_path_keeps_native_contract_and_authentication(self):
        request = {"state": "hello", "questions": {"q": {"type": "noul", "instructions": "A greeting?"}}}
        for path in ("/v1/decision", "/laya/v1/decision", "/v1/systemone"):
            with self.subTest(path=path), self.client(path) as client:
                response = client.post(path, json=request, headers={"Authorization": "Bearer test-key"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["answers"]["q"]["noul"], 0.9)
                self.assertEqual(client.post(path, json=request).status_code, 401)
                self.assertEqual(client.post(path, json=request,
                                             headers={"Authorization": "Bearer wrong"}).status_code, 401)
                native = client.post("/v1/systemone", json=request, headers={"Authorization": "Bearer test-key"})
                self.assertEqual(response.json(), native.json())
                invalid = client.post(path, json={}, headers={"Authorization": "Bearer test-key"})
                self.assertEqual(invalid.status_code, 400)
                if path != "/v1/decision":
                    self.assertEqual(client.post("/v1/decision", json=request).status_code, 404)

    def test_invalid_paths_fail_before_loading_a_model(self):
        for path in ("", "decision", "//decision", "/", "/a/", "/a/../b", "/a?q=b", "/a#b", "/{name}"):
            with self.subTest(path=path), patch.dict(os.environ, {"LAYA_API_PATH": path}), \
                    patch("app.create_laya_app") as factory:
                with self.assertRaises(ValueError):
                    create_app()
                factory.assert_not_called()

    def test_reserved_paths_fail_instead_of_shadowing_health_or_docs(self):
        for path in ("/health", "/docs", "/v1/systemone/batch"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.client(path)

    def test_default_path(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch("app.create_laya_app", side_effect=lambda: create_laya_app(router=Router())):
            paths = [route.path for route in create_app().routes]
            self.assertEqual(paths.count("/v1/systemone"), 1)
            self.assertNotIn("/v1/decision", paths)


if __name__ == "__main__":
    unittest.main()
