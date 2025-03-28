"""
Standardized testing framework for Berrys_AgentsV2 services.

This package provides a standardized testing framework that can be applied
across all services in the Berrys_AgentsV2 system.
"""

# Import base classes
from .base import (
    BaseTest,
    BaseAsyncTest,
    BaseDatabaseTest,
    BaseAPITest,
    BaseModelTest,
    BaseServiceTest,
    BaseIntegrationTest,
)

# Import mock data utilities
from .mock_data import (
    MockDataGenerator,
    ModelFactory,
    create_user_factory,
    create_project_factory,
    create_agent_factory,
    create_tool_factory,
)

# Import database utilities
from .database import (
    DatabaseTestConfig,
    DatabaseTestHelper,
    MockDatabase,
)

# Import API utilities
from .api import (
    APITestConfig,
    APITestHelper,
    MockAuthHelper,
    MockResponse,
    MockClient,
)

# Import configuration utilities
from .config import (
    TestEnvironment,
    BaseTestConfig,
    ConfigLoader,
    TestConfigManager,
)

# Import performance utilities
from .performance import (
    Timer,
    AsyncTimer,
    timeit,
    async_timeit,
    Profiler,
    profile,
    Benchmark,
    PerformanceTest,
    LoadTest,
)

# Import reporting utilities
from .reporting import (
    TestResult,
    TestSuite,
    TestReport,
    TestReporter,
    TestVisualizer,
)

# Import test utilities
from .utils import (
    MockUtils,
    AssertionUtils,
    DatabaseTestUtils,
    AsyncTestUtils,
    FileTestUtils,
    TestDecorators,
)

# Import fixtures
from .fixtures import (
    db_engine,
    db_session_factory,
    db_session,
    db_helper,
    test_app,
    test_client,
    async_client,
    api_helper,
    test_config,
    test_config_from_file,
    test_logger,
    temp_dir,
    temp_file,
    mock_response,
    mock_error_response,
    mock_db_session,
    event_loop,
    agent_orchestrator_db,
    model_orchestration_db,
    project_coordinator_db,
    service_integration_db,
    tool_integration_db,
)

# Import constants
from .constants import (
    TestEnvironment as TestEnv,
    DATABASE_URL,
    DATABASE_SCHEMA,
    DATABASE_TABLES,
    API_BASE_URL,
    API_ENDPOINTS,
    API_HEADERS,
    API_AUTH_HEADER,
    MOCK_UUID,
    MOCK_DATETIME,
    MOCK_USER,
    MOCK_PROJECT,
    MOCK_AGENT,
    MOCK_AGENT_TEMPLATE,
    MOCK_AGENT_SPECIALIZATION,
    MOCK_MODEL,
    MOCK_MODEL_VERSION,
    MOCK_TOOL,
    MOCK_TOOL_VERSION,
    MOCK_TASK,
    MOCK_TASK_RESULT,
    TEST_USERS,
    TEST_PROJECTS,
    TEST_AGENTS,
    TEST_MODELS,
    TEST_TOOLS,
    ERROR_MESSAGES,
    ERROR_CODES,
    TEST_CONFIG,
    AGENT_ORCHESTRATOR_CONFIG,
    MODEL_ORCHESTRATION_CONFIG,
    PROJECT_COORDINATOR_CONFIG,
    SERVICE_INTEGRATION_CONFIG,
    TOOL_INTEGRATION_CONFIG,
    TEST_DATA_DIR,
    TEST_CONFIG_DIR,
    TEST_FIXTURES_DIR,
    TEST_REPORTS_DIR,
)

# Version
__version__ = "0.1.0"
