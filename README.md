# ApeRAG

ApeRAG is an advanced Retrieval-Augmented Generation (RAG) system designed to build sophisticated enterprise-level AI applications. It features a robust backend powered by Django and Celery for asynchronous task processing, and a dynamic frontend built with React and TypeScript (UmiJS). ApeRAG excels in parsing diverse document types, generating embeddings, performing hybrid vector/keyword searches, and integrating with Large Language Models (LLMs). It supports a wide array of databases including PostgreSQL, MongoDB, Neo4j, Redis, Qdrant, and Elasticsearch, enabling flexible data storage and retrieval strategies. With a focus on workflow automation, data source management, and seamless integration capabilities, ApeRAG provides a comprehensive platform for developing and deploying cutting-edge RAG solutions.

## Table of Contents

- [Getting Started](#getting-started)
  - [Getting Started with Kubernetes](#getting-started-with-kubernetes)
  - [Getting Started with Docker Compose](#getting-started-with-docker-compose)
  - [Getting Started with Source Code](#getting-started-with-source-code)
- [Development](#development)
  - [Development Environment](#development-environment)
  - [Key `make` Commands for Development](#key-make-commands-for-development)
  - [Typical Development Workflow](#typical-development-workflow)
- [Building and Deployment](#building-and-deployment)
  - [Building Container Images](#building-container-images)
  - [Deployment](#deployment)
- [Project Structure Overview](#project-structure-overview)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

This section will guide you through setting up ApeRAG using different methods.

### Getting Started with Kubernetes

ApeRAG can be deployed to a Kubernetes cluster using the provided Helm chart. This guide focuses on deploying the necessary databases using KubeBlocks and then deploying the ApeRAG application.

**Phase 1: Deploying Databases with KubeBlocks**

ApeRAG relies on several databases (PostgreSQL, Redis, Qdrant, Elasticsearch, Neo4j). The scripts in the `deploy/databases/` directory leverage [KubeBlocks](https://kubeblocks.io/) to simplify the deployment and management of these stateful services on Kubernetes.

1.  **Prerequisites for Database Deployment**:
    *   A running Kubernetes cluster (e.g., Minikube, EKS, GKE, AKS).
    *   `kubectl` installed and configured to connect to your cluster.
    *   Helm v3+ installed.

2.  **Configure Target Databases**:
    Edit the `deploy/databases/00-config.sh` script. Set the corresponding environment variable to `true` for each database you intend to deploy. For example:
    ```bash
    ENABLE_POSTGRESQL=true
    ENABLE_REDIS=true
    ENABLE_QDRANT=true
    ENABLE_ELASTICSEARCH=true # Optional, for hybrid search
    ENABLE_NEO4J=true       # Optional, for graph knowledge
    ENABLE_MONGODB=false    # Example: Not enabling MongoDB
    ```
    By default, scripts will operate in the `rag` namespace. You can change the `NAMESPACE` variable in `00-config.sh` if needed.

3.  **Prepare Environment & Install KubeBlocks Add-ons**:
    This script performs pre-checks, adds the KubeBlocks Helm repository, and installs necessary KubeBlocks components and add-ons for the selected databases.
    ```bash
    bash ./deploy/databases/01-prepare.sh
    ```

4.  **(Optional) Customize Database Instance Settings**:
    Before deploying the actual database clusters, you can customize their configurations (like version, replicas, CPU/memory, storage) by editing the respective `values.yaml` files located within each database subdirectory (e.g., `deploy/databases/postgresql/values.yaml`, `deploy/databases/redis/values.yaml`, etc.).

5.  **Install Database Clusters**:
    This script deploys the database clusters you configured in `00-config.sh` into your Kubernetes cluster using KubeBlocks.
    ```bash
    bash ./deploy/databases/02-install-database.sh
    ```
    Monitor the status of the database pods. It might take a few minutes for all services to become ready, especially if images need to be pulled.
    ```bash
    kubectl get clusters -n rag # Or your configured namespace
    kubectl get pods -n rag     # Or your configured namespace
    ```
    Wait until all relevant pods are in the `Running` state.

**Phase 2: Deploying ApeRAG Application**

Once the databases are running and accessible within your Kubernetes cluster:

1.  **Configure ApeRAG Helm Chart**:
    The Helm chart for ApeRAG is located in `deploy/aperag/`.
    *   Review and customize the `deploy/aperag/values.yaml` file. Crucially, ensure the database connection details (hostnames, ports, credentials) correctly point to the services created by KubeBlocks in the previous phase. The default service names in `values.yaml` often align with KubeBlocks conventions (e.g., `pg-cluster-postgresql-postgresql` for PostgreSQL in the `rag` namespace), but always verify.
    *   Consult the `deploy/databases/README.md` for guidance on how to retrieve credentials (e.g., from Kubernetes Secrets) for the KubeBlocks-managed databases and configure them in `deploy/aperag/values.yaml` or via secrets referenced by the Helm chart.
    *   Adjust other settings as needed: image repositories/tags, resource limits, ingress rules, `AUTH_TYPE`, `OBJECT_STORE_TYPE`, etc.

2.  **Deploy ApeRAG**:
    Deploy ApeRAG using the configured Helm chart:
    ```bash
    helm install <release-name> ./deploy/aperag -n <target-namespace-for-aperag> --create-namespace
    ```
    Replace `<release-name>` (e.g., `aperag`) and `<target-namespace-for-aperag>` (this can be the same as the database namespace, e.g., `rag`, or different).

3.  **Access ApeRAG**:
    The access method depends on your Kubernetes service type (e.g., LoadBalancer, NodePort) and Ingress configuration within the `deploy/aperag/values.yaml` file. If using an Ingress, access ApeRAG via the configured hostname. Otherwise, use the external IP and port of the relevant service.

For detailed instructions on managing the KubeBlocks-deployed databases (connecting, uninstalling), refer to `deploy/databases/README.md`.

### Getting Started with Docker Compose

To get started with ApeRAG using Docker Compose, follow these steps:

1.  **Prerequisites**:
    *   Docker & Docker Compose
    *   Git

2.  **Environment Setup**:
    Configure environment variables by copying the template files:
    ```bash
    cp envs/env.template .env
    cp frontend/deploy/env.local.template frontend/.env
    ```
    Then, **edit the `.env` file** to configure your AI service settings and other necessary configurations according to your needs.

3.  **Start Services**:
    You can start all ApeRAG services using the following `make` command:
    ```bash
    # Optional: Use Aliyun registry if in China
    # export REGISTRY=apecloud-registry.cn-zhangjiakou.cr.aliyuncs.com

    # Start ApeRAG services
    make compose-up
    ```
    If you need to use the `doc-ray` service for advanced document parsing (recommended for complex documents, tables, or formulas), you can start it along with other services:
    ```bash
    make compose-up WITH_DOCRAY=1
    ```
    If your environment has GPUs, you can enable GPU support for `doc-ray` for better performance:
    ```bash
    make compose-up WITH_DOCRAY=1 WITH_GPU=1
    ```
    > **About the doc-ray parsing service**
    >
    > ApeRAG includes a basic built-in parser for extracting text from documents like PDFs and DOCX files for RAG indexing. However, this parser may not optimally handle complex document structures, tables, or formulas.
    >
    > For enhanced document parsing capabilities and more accurate content extraction, we recommend deploying the [doc-ray](https://github.com/apecloud/doc-ray) service. `doc-ray` leverages **MinerU** for advanced document analysis.
    >
    > * When `WITH_GPU=1` is not specified, `doc-ray` will run using only the CPU. In this case, it is recommended to allocate at least 4 CPU cores and 8GB+ of RAM for it.
    > * When `WITH_GPU=1` is specified, `doc-ray` will run using the GPU. It requires approximately 6GB of VRAM, along with 2 CPU cores and 8GB of RAM.

4.  **Access ApeRAG**:
    Once the services are up and running, open your browser and navigate to: http://localhost:3000/web/

### Getting Started with Source Code

This approach is suitable for developers who want to contribute to ApeRAG or run it locally for development purposes.

1.  **Prerequisites**:
    *   Git
    *   Python (>=3.10 recommended, check `pyproject.toml` for exact version)
    *   Node.js (>=20 recommended, for frontend development)
    *   `uv` (Python package installer, `pip install uv`)
    *   Access to database services (PostgreSQL, Redis, Qdrant, etc.). You can run these locally using Docker, or connect to remote instances.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/apecloud/ApeRAG.git
    cd ApeRAG
    ```

3.  **Environment Setup**:
    *   Copy and configure the backend environment file:
        ```bash
        cp envs/env.template .env
        ```
        Edit `.env` to set database connection strings, API keys for AI services, and other configurations.
    *   Copy and configure the frontend environment file (if you plan to run/develop the frontend):
        ```bash
        cp frontend/deploy/env.local.template frontend/.env
        ```
        Edit `frontend/.env` for frontend-specific settings.

4.  **Install Dependencies**:
    This command installs both backend and frontend dependencies.
    ```bash
    make install
    ```

5.  **Setup Databases**:
    Ensure your databases are running and accessible. If you are running them locally (e.g., via Docker containers started separately or using `make run-db` from the Docker Compose setup), make sure the connection details in `.env` are correct.
    Apply database migrations:
    ```bash
    make migrate
    ```

6.  **Run Backend Services**:
    *   Activate the Python virtual environment:
        ```bash
        source .venv/bin/activate
        ```
    *   Start the Django backend server:
        ```bash
        make run-backend
        ```
    *   In a separate terminal, start the Celery worker (ensure the virtual environment is activated):
        ```bash
        make run-celery
        ```
    *   (Optional) In another terminal, start the Celery beat scheduler if needed:
        ```bash
        make run-celery-beat
        ```

7.  **Run Frontend Service** (Optional):
    If you need to run the frontend development server:
    ```bash
    make run-frontend
    ```
    The frontend will typically be available at `http://localhost:3000`.

8.  **Access ApeRAG**:
    The backend API will be available at `http://localhost:8000` (or as configured). The frontend, if started, will be at `http://localhost:3000`.

## Development

This section focuses on the development workflow and tools provided for ApeRAG.

### Development Environment

It's recommended to use the "Getting Started with Source Code" approach for setting up a development environment. Ensure all prerequisites are met and dependencies are installed using `make install`.

### Key `make` Commands for Development

The `Makefile` at the root of the project provides several helpful commands to streamline development:

*   **Environment & Dependencies**:
    *   `make install`: Installs all necessary backend (Python) and frontend (Node.js) dependencies. It sets up a virtual environment for Python.
    *   `make dev`: Installs development tools like pre-commit hooks to ensure code quality before commits.

*   **Running Services**:
    *   `make run-db`: (Uses Docker Compose) Starts all required database services (PostgreSQL, Redis, Qdrant, etc.) as defined in `docker-compose.yml`. Useful if you don't have these services running elsewhere.
    *   `make run-backend`: Starts the Django development server.
    *   `make run-frontend`: Starts the UmiJS frontend development server.
    *   `make run-celery`: Starts a Celery worker for processing background tasks.
    *   `make run-celery-beat`: Starts the Celery beat scheduler for periodic tasks.

*   **Code Quality & Testing**:
    *   `make format`: Formats Python code using Ruff and frontend code using Prettier.
    *   `make lint`: Lints Python code with Ruff and frontend code.
    *   `make static-check`: Performs static type checking for Python code using Mypy (if configured).
    *   `make test`: Runs all automated tests (Python unit tests, integration tests).

*   **Database Management**:
    *   `make makemigration`: Creates new database migration files based on changes to Django models.
    *   `make migrate`: Applies pending database migrations to your connected database.
    *   `make connect-metadb`: Provides a command to connect to the primary PostgreSQL database (usually for inspection).
    *   `make diff`: Shows differences in Django settings (useful for debugging configurations).

*   **Generators**:
    *   `make generate-models`: Generates LLM model configuration files.
    *   `make generate-frontend-sdk`: Generates the frontend API client/SDK from the OpenAPI specification. **Run this command whenever backend API definitions change.**

*   **Docker Compose (for local full-stack testing)**:
    *   `make compose-up`: Starts all services (backend, frontend, databases, Celery) using Docker Compose. This is similar to the "Getting Started with Docker Compose" method but can also be used during development for a full-stack test.
    *   `make compose-down`: Stops all services started with `make compose-up`.
    *   `make compose-logs`: Tails the logs from all services running under Docker Compose.

*   **Cleanup**:
    *   `make clean`: Removes temporary files, build artifacts, and caches from the development environment.

### Typical Development Workflow

1.  Ensure your development environment is set up (dependencies installed, databases running/accessible).
2.  Create a new branch for your feature or bug fix.
3.  Make code changes in the backend (`aperag/`) or frontend (`frontend/src/`) directories.
4.  If you change backend API endpoints (add, remove, modify parameters/responses):
    *   Update the OpenAPI specification (usually in `aperag/api/`).
    *   Run `make generate-frontend-sdk` to update the frontend client.
5.  If you change Django models:
    *   Run `make makemigration` to create migration files.
    *   Run `make migrate` to apply changes to your development database.
6.  Regularly run `make format` and `make lint` to maintain code quality.
7.  Write unit tests for new functionality and run `make test` to ensure everything passes.
8.  Commit your changes and push to your branch.

## Building and Deployment

This section covers how to build ApeRAG container images and deploy the application. It's primarily for users who need to create their own builds or deploy to environments other than the ones covered in "Getting Started".

### Building Container Images

The project uses Docker and `make` commands to build container images.

*   **Local Platform Builds**:
    These commands build images for your current machine's architecture.
    ```bash
    # Build all necessary images for local platform
    make build-local

    # Build only the backend image for local platform
    make build-aperag-local

    # Build only the frontend image for local platform
    make build-aperag-frontend-local
    ```

*   **Multi-platform Builds**:
    These commands build images for multiple architectures (e.g., amd64, arm64). This requires Docker Buildx to be set up and configured.
    ```bash
    # Build all necessary images for multiple platforms
    make build

    # Build only the backend image for multiple platforms
    make build-aperag

    # Build only the frontend image for multiple platforms
    make build-aperag-frontend
    ```
    You can specify the target platforms using the `PLATFORMS` variable, for example:
    ```bash
    make build PLATFORMS=linux/amd64,linux/arm64
    ```

### Deployment

Refer to the "Getting Started" section for common deployment methods:
*   [Getting Started with Kubernetes](#getting-started-with-kubernetes)
*   [Getting Started with Docker Compose](#getting-started-with-docker-compose)

For custom deployments, you will need to adapt these methods or use the built container images with your chosen orchestration platform. Ensure all required services (databases, backend, frontend, Celery workers) are correctly configured and can communicate with each other.

## Project Structure Overview

ApeRAG follows a modular structure to separate concerns and facilitate development. Here's a high-level overview of the key directories:

*   **`aperag/`**: Contains the core backend Django application.
    *   `api/`: OpenAPI specifications and generated schema components.
    *   `auth/`: Authentication and authorization logic.
    *   `chat/`: Real-time chat functionalities.
    *   `docparser/`: Document parsing and text extraction modules.
    *   `embed/`: Embedding generation and management.
    *   `flow/`: Workflow orchestration for RAG pipelines.
    *   `graph/`: Graph database interactions (e.g., Neo4j).
    *   `llm/`: Large Language Model integration.
    *   `schema/`: Pydantic models and data schemas.
    *   `service/`: Core business logic and services.
    *   `tasks/`: Celery asynchronous background tasks.
    *   `views/`: Django Ninja API endpoint definitions.
    *   `vectorstore/`: Vector database operations (e.g., Qdrant).
*   **`frontend/`**: Contains the UmiJS (React/TypeScript) frontend application.
    *   `src/api/`: Auto-generated API client from OpenAPI specs.
    *   `src/components/`: Reusable UI components.
    *   `src/layouts/`: Page layout components.
    *   `src/locales/`: Internationalization (i18n) files.
    *   `src/models/`: UmiJS state management models.
    *   `src/pages/`: Application pages and views.
*   **`deploy/`**: Contains deployment configurations.
    *   `aperag/`: Helm chart for Kubernetes deployment.
    *   `databases/`: Scripts and configurations for deploying dependent databases (e.g., PostgreSQL, Redis, Qdrant) often using KubeBlocks.
*   **`docker-compose.yml`**: Defines services for local development and testing using Docker Compose.
*   **`Makefile`**: Provides convenient `make` commands for common development tasks like installation, running services, linting, testing, and building.
*   **`docs/`**: Contains additional project documentation, guides, and design documents.
*   **`tests/`**: Contains unit, integration, and end-to-end tests.

This structure helps maintain a clean and organized codebase, making it easier to navigate and contribute to the project.

## Contributing

We welcome contributions to ApeRAG! If you're interested in contributing, please follow these general guidelines:

1.  **Fork the Repository**: Start by forking the official ApeRAG repository to your own GitHub account.
2.  **Create a Branch**: Create a new branch from `main` for your feature or bug fix. Use a descriptive branch name (e.g., `feat/add-new-parser` or `fix/login-bug`).
3.  **Follow Code Style**:
    *   Python: Adhere to PEP 8. Use `make format` and `make lint` to ensure consistency.
    *   TypeScript/React: Follow standard practices. Use `make format` to format frontend code.
    *   Use English for all code, comments, and documentation.
4.  **Write Tests**: Add unit tests for new backend logic and integration tests for API changes. Ensure existing tests pass by running `make test`.
5.  **Update Documentation**: If your changes affect API specifications, user guides, or deployment, update the relevant documentation (OpenAPI specs, README, docs/).
6.  **Generate Frontend SDK**: If you modify backend API definitions, run `make generate-frontend-sdk` to update the frontend client.
7.  **Commit Changes**: Make clear and concise commit messages.
8.  **Submit a Pull Request (PR)**: Push your branch to your fork and submit a PR to the `main` branch of the official ApeRAG repository.
    *   Provide a clear description of your changes in the PR.
    *   Link any relevant issues.
9.  **Code Review**: Your PR will be reviewed by maintainers. Be prepared to address feedback and make further changes if necessary.

Before starting significant work, it's a good idea to open an issue to discuss your proposed changes with the maintainers.

## License

ApeRAG is licensed under the Apache License 2.0. See the [LICENSE](./LICENSE) file for details.