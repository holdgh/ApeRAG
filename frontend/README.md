# ApeRAG Console

This is the ApeRAG front-end project.

# Development

The project calls the local api by default.

- .env file config

  ```shell
  # No changes are required for the environment variables below
  PORT=3000
  BASE_PATH=/web/
  DID_YOU_KNOW=none
  MOCK=none
  ```

- install dependencies:

  ```
  # The node engine version should be ">=20"
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
make
```
