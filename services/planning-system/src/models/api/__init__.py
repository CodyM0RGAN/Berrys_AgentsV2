"""
Planning System Service API models.

This module defines Pydantic models for API requests and responses,
providing validation and serialization for the Planning System service.
"""

# Import shared components
from shared.models.src.api.responses import (
    create_data_response_model, 
    create_list_response_model,
    ListRequestParams,
    PaginatedResponse
)

# Import shared enums
from shared.models.src.enums import (
    TaskStatus, 
    DependencyType, 
    ResourceType, 
    TaskPriority, 
    ProjectStatus,
    OptimizationTarget
)

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus

# Pagination
class PaginationParams(ListRequestParams):
    """Parameters for pagination"""
    pass

# Import all models from submodules
from .strategic_plan import (
    StrategicPlanBase,
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponseData,
    StrategicPlanResponse,
    StrategicPlanListResponse
)

from .plan_phase import (
    PlanPhaseBase,
    PlanPhaseCreate,
    PlanPhaseUpdate,
    PlanPhaseResponseData,
    PlanPhaseResponse,
    PlanPhaseListResponse
)

from .plan_milestone import (
    PlanMilestone,
    PlanMilestoneCreate,
    PlanMilestoneUpdate,
    PlanMilestoneResponseData,
    PlanMilestoneResponse,
    PlanMilestoneListResponse
)

from .planning_task import (
    PlanningTaskBase,
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponseData,
    PlanningTaskResponse,
    PlanningTaskListResponse
)

from .dependency import (
    DependencyBase,
    DependencyCreate,
    DependencyUpdate,
    DependencyResponseData,
    DependencyResponse,
    DependencyListResponse
)

from .resource import (
    ResourceBase,
    ResourceCreate,
    ResourceUpdate,
    ResourceResponseData,
    ResourceResponse,
    ResourceListResponse
)

from .resource_allocation import (
    ResourceAllocationBase,
    ResourceAllocationCreate,
    ResourceAllocationUpdate,
    ResourceAllocationResponseData,
    ResourceAllocationResponse,
    ResourceAllocationListResponse
)

from .plan_template import (
    PlanTemplateBase,
    PlanTemplateCreate,
    PlanTemplateUpdate,
    PlanTemplateResponseData,
    PlanTemplateResponse,
    PlanTemplateListResponse,
    TemplatePhaseBase,
    TemplatePhaseCreate,
    TemplatePhaseUpdate,
    TemplatePhaseResponseData,
    TemplatePhaseResponse,
    TemplatePhaseListResponse,
    TemplateMilestoneBase,
    TemplateMilestoneCreate,
    TemplateMilestoneUpdate,
    TemplateMilestoneResponseData,
    TemplateMilestoneResponse,
    TemplateMilestoneListResponse,
    TemplateTaskBase,
    TemplateTaskCreate,
    TemplateTaskUpdate,
    TemplateTaskResponseData,
    TemplateTaskResponse,
    TemplateTaskListResponse
)

from .planning_methodology import (
    PlanningMethodologyBase,
    PlanningMethodologyCreate,
    PlanningMethodologyUpdate,
    PlanningMethodologyResponseData,
    PlanningMethodologyResponse,
    PlanningMethodologyListResponse
)

from .forecasting import (
    TimelinePoint,
    TimelineForecastData,
    ForecastRequest,
    BottleneckAnalysisData,
    TimelineForecastResponse,
    BottleneckAnalysisResponse,
    TimelineForecast,
    BottleneckAnalysis
)

from .optimization import (
    OptimizationRequest,
    OptimizationResultData,
    OptimizationResultResponse,
    OptimizationResult
)

from .dependency_type_info import (
    DependencyTypeInfo
)

from .task_template import (
    TaskTemplateBase,
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateResponseData,
    TaskTemplateResponse,
    TaskTemplateListResponse
)

from .what_if_analysis import (
    WhatIfScenarioBase,
    WhatIfScenarioCreate,
    WhatIfScenarioUpdate,
    WhatIfScenarioResponseData,
    WhatIfScenarioResponse,
    WhatIfScenarioListResponse,
    WhatIfAnalysisResult,
    WhatIfAnalysisResultResponse
)
