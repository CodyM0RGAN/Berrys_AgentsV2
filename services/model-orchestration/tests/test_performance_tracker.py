import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.src.messaging import EventBus

from src.config import Settings
from src.services.performance_tracker import PerformanceTracker
from src.models.performance import (
    ModelPerformanceModel,
    ModelFeedbackModel,
    ModelPerformanceHistoryModel,
)


@pytest.fixture
def mock_event_bus():
    """
    Fixture for a mock event bus.
    """
    event_bus = AsyncMock()
    event_bus.publish_event = AsyncMock()
    return event_bus


@pytest.fixture
def mock_settings():
    """
    Fixture for mock settings.
    """
    return Settings()


@pytest.fixture
def performance_tracker(mock_db_session, mock_event_bus, mock_settings):
    """
    Fixture for a performance tracker.
    """
    return PerformanceTracker(
        db=mock_db_session,
        event_bus=mock_event_bus,
        settings=mock_settings,
    )


class TestPerformanceTracker:
    """
    Tests for the performance tracker.
    """
    
    @pytest.mark.asyncio
    async def test_record_request_result_new_model(self, performance_tracker, mock_db_session):
        """
        Test recording a request result for a new model.
        """
        # Setup
        mock_db_session.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: None)))
        mock_db_session.commit = AsyncMock()
        
        # Execute
        await performance_tracker.record_request_result(
            request_id="req-123",
            model_id="gpt-4",
            task_type="code_generation",
            success=True,
            quality_score=0.9,
            confidence=0.8,
        )
        
        # Verify
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # Check the model that was added
        added_model = mock_db_session.add.call_args[0][0]
        assert isinstance(added_model, ModelPerformanceModel)
        assert added_model.model_id == "gpt-4"
        assert added_model.task_type == "code_generation"
        assert added_model.quality_score == 0.9
        assert added_model.success_rate == 1.0
        assert added_model.sample_count == 1
        assert added_model.metrics["confidence_sum"] == 0.8
        assert added_model.metrics["quality_sum"] == 0.9
    
    @pytest.mark.asyncio
    async def test_record_request_result_existing_model(self, performance_tracker, mock_db_session):
        """
        Test recording a request result for an existing model.
        """
        # Setup
        existing_model = ModelPerformanceModel(
            model_id="gpt-4",
            task_type="code_generation",
            quality_score=0.8,
            success_rate=0.5,
            sample_count=2,
            metrics={
                "confidence_sum": 1.5,
                "quality_sum": 1.6,
            },
        )
        
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: existing_model))
        )
        mock_db_session.commit = AsyncMock()
        
        # Execute
        await performance_tracker.record_request_result(
            request_id="req-123",
            model_id="gpt-4",
            task_type="code_generation",
            success=True,
            quality_score=0.9,
            confidence=0.8,
        )
        
        # Verify
        mock_db_session.commit.assert_called_once()
        
        # Check the updated model
        assert existing_model.quality_score == pytest.approx(0.8333, abs=0.001)  # (1.6 + 0.9) / 3
        assert existing_model.success_rate == pytest.approx(0.6667, abs=0.001)  # (0.5*2 + 1) / 3
        assert existing_model.sample_count == 3
        assert existing_model.metrics["confidence_sum"] == 2.3  # 1.5 + 0.8
        assert existing_model.metrics["quality_sum"] == 2.5  # 1.6 + 0.9
    
    @pytest.mark.asyncio
    async def test_record_feedback(self, performance_tracker, mock_db_session, mock_event_bus):
        """
        Test recording feedback.
        """
        # Setup
        existing_model = ModelPerformanceModel(
            model_id="gpt-4",
            task_type="code_generation",
            quality_score=0.8,
            success_rate=0.5,
            sample_count=2,
            metrics={
                "quality_sum": 1.6,
            },
        )
        
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: existing_model))
        )
        mock_db_session.commit = AsyncMock()
        
        # Execute
        feedback_id = await performance_tracker.record_feedback(
            request_id="req-123",
            model_id="gpt-4",
            success=True,
            quality_rating=0.9,
            feedback_text="Great response!",
            task_type="code_generation",
            corrections=None,
            user_id="user-123",
        )
        
        # Verify
        assert feedback_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_event_bus.publish_event.assert_called_once()
        
        # Check the feedback that was added
        added_feedback = mock_db_session.add.call_args[0][0]
        assert isinstance(added_feedback, ModelFeedbackModel)
        assert added_feedback.request_id == "req-123"
        assert added_feedback.model_id == "gpt-4"
        assert added_feedback.task_type == "code_generation"
        assert added_feedback.quality_rating == 0.9
        assert added_feedback.success is True
        assert added_feedback.feedback_text == "Great response!"
        assert added_feedback.user_id == "user-123"
        
        # Check the updated model (feedback is weighted more heavily)
        feedback_weight = 2.0
        assert existing_model.quality_score == pytest.approx(0.85, abs=0.001)  # (1.6 + 0.9*2) / (2 + 2)
        assert existing_model.success_rate == pytest.approx(0.75, abs=0.001)  # (0.5*2 + 1*2) / (2 + 2)
        assert existing_model.sample_count == 4  # 2 + 2
        assert existing_model.metrics["quality_sum"] == pytest.approx(3.4)  # 1.6 + 0.9*2
    
    @pytest.mark.asyncio
    async def test_get_model_performance(self, performance_tracker, mock_db_session):
        """
        Test getting model performance.
        """
        # Setup
        models = [
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="gpt-4",
                task_type="code_generation",
                quality_score=0.9,
                success_rate=0.8,
                sample_count=10,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="gpt-4",
                task_type="reasoning",
                quality_score=0.85,
                success_rate=0.75,
                sample_count=8,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="claude-2",
                task_type="code_generation",
                quality_score=0.88,
                success_rate=0.82,
                sample_count=12,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: models))
        )
        
        # Execute
        result = await performance_tracker.get_model_performance()
        
        # Verify
        assert len(result) == 3
        assert result[0]["model_id"] == "gpt-4"
        assert result[0]["task_type"] == "code_generation"
        assert result[0]["quality_score"] == 0.9
        assert result[0]["success_rate"] == 0.8
        assert result[0]["sample_count"] == 10
        
        # Test with filters
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [models[0]]))
        )
        
        result = await performance_tracker.get_model_performance(
            model_id="gpt-4",
            task_type="code_generation",
        )
        
        assert len(result) == 1
        assert result[0]["model_id"] == "gpt-4"
        assert result[0]["task_type"] == "code_generation"
    
    @pytest.mark.asyncio
    async def test_get_best_model_for_task(self, performance_tracker, mock_db_session):
        """
        Test getting the best model for a task.
        """
        # Setup
        models = [
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="gpt-4",
                task_type="code_generation",
                quality_score=0.9,
                success_rate=0.8,
                sample_count=10,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="claude-2",
                task_type="code_generation",
                quality_score=0.88,
                success_rate=0.82,
                sample_count=12,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: models[0]))
        )
        
        # Execute
        result = await performance_tracker.get_best_model_for_task(
            task_type="code_generation",
            min_quality_score=0.8,
            min_success_rate=0.7,
        )
        
        # Verify
        assert result == "gpt-4"
        
        # Test with no results
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: None))
        )
        
        result = await performance_tracker.get_best_model_for_task(
            task_type="unknown_task",
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_performance_history(self, performance_tracker, mock_db_session):
        """
        Test updating performance history.
        """
        # Setup
        models = [
            ModelPerformanceModel(
                id=uuid.uuid4(),
                model_id="gpt-4",
                task_type="code_generation",
                quality_score=0.9,
                success_rate=0.8,
                sample_count=10,
                metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        
        mock_db_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalars=lambda: MagicMock(all=lambda: models)),  # First call for all models
                MagicMock(scalars=lambda: MagicMock(first=lambda: None)),  # No existing day record
                MagicMock(scalars=lambda: MagicMock(first=lambda: None)),  # No existing week record
                MagicMock(scalars=lambda: MagicMock(first=lambda: None)),  # No existing month record
            ]
        )
        mock_db_session.commit = AsyncMock()
        
        # Execute
        await performance_tracker.update_performance_history()
        
        # Verify
        assert mock_db_session.add.call_count == 3  # One for each period type
        mock_db_session.commit.assert_called_once()
        
        # Check the history records that were added
        for i, period_type in enumerate(["day", "week", "month"]):
            history = mock_db_session.add.call_args_list[i][0][0]
            assert isinstance(history, ModelPerformanceHistoryModel)
            assert history.model_id == "gpt-4"
            assert history.task_type == "code_generation"
            assert history.quality_score == 0.9
            assert history.success_rate == 0.8
            assert history.sample_count == 10
            assert history.period_type == period_type
