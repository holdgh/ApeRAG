# ApeRAG Console

This is the ApeRAG front-end project.

# Development

The project calls the local api by default. 

- .env file config

  ```shell
  # change api endpoint for local server debug
  API_ENDPOINT=http://127.0.0.1:8000

  # No changes are required for the environment variables below
  BASE_PATH=/web
  PUBLIC_PATH=/web/
  MOCK=none
  PORT=8001
  ```

- install dependencies:
  ```
  # The node engine version should be ">=16"
  yarn install
  ```

- start command:
  ```
  yarn dev
  ```

# Deploy

#### STEP1: Build docker image

After merging into the main branch, CICD will be triggered to build the image, or you can manually trigger the image build.

```
make build
```
