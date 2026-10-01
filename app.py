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

"""Serve Laya's native protocol at a configurable additional request path."""

import os
import re

from laya.serve import create_app as create_laya_app


def create_app():
    api_path = os.environ.get("LAYA_API_PATH", "/v1/systemone")
    if not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+", api_path):
        raise ValueError("LAYA_API_PATH must be an absolute path of nonempty letters/digits/_/- segments")

    app = create_laya_app()
    if api_path != "/v1/systemone":
        if any(route.path == api_path for route in app.routes):
            raise ValueError("LAYA_API_PATH conflicts with an existing Laya endpoint")
        handler = next(route.endpoint for route in app.routes if route.path == "/v1/systemone")
        app.add_api_route(api_path, handler, methods=["POST"])
    return app
