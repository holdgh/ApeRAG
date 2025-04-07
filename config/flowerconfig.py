# Copyright 2025 ApeCloud, Inc.
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

# Broker settings
BROKER_URL = 'redis://localhost:6379/0'

# Enable debug logging
logging = 'DEBUG'

# Web server address
address = '127.0.0.1'

# Run the http server on a given port
port = 5555

# Refresh dashboards automatically
auto_refresh = True

# Enable support of X-Real-Ip and X-Scheme headers
xheaders = True

# A database file to use if persistent mode is enabled
# db = '/var/flower/db/flower.db'

# Enable persistent mode. If the persistent mode is enabled Flower saves the current state and reloads on restart
# persistent = True
