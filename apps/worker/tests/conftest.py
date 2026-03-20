import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from worker.models import Order


@pytest.fixture
def mock_order():
    return Order(
        id=uuid.uuid4(),
        status="pending",
        total=Decimal("29.99"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_db(mock_order):
    session = MagicMock()
    session.get.return_value = mock_order
    return session


@pytest.fixture
def patch_db(mock_db):
    with patch("worker.tasks.get_db") as mock:
        mock.return_value = iter([mock_db])
        yield mock_db
