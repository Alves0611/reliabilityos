import uuid
from unittest.mock import MagicMock, patch

import pytest


def test_process_order_success(patch_db, mock_order):
    order_id = str(mock_order.id)

    with patch("worker.tasks.publish_event") as mock_pub:
        with patch("worker.tasks.time.sleep"):
            from worker.tasks import process_order

            result = process_order(order_id)

    assert mock_order.status == "completed"
    assert result == {"order_id": order_id, "status": "completed"}
    patch_db.commit.assert_called()
    mock_pub.assert_called_once_with(
        "order.completed", {"event": "order.completed", "order_id": order_id}
    )


def test_process_order_not_found(patch_db):
    patch_db.get.return_value = None

    with patch("worker.tasks.time.sleep"):
        from worker.tasks import process_order

        with pytest.raises(ValueError, match="not found"):
            process_order(str(uuid.uuid4()))


def test_process_order_transitions_through_processing(patch_db, mock_order):
    statuses = []

    original_commit = patch_db.commit

    def track_commit():
        statuses.append(mock_order.status)
        original_commit()

    patch_db.commit = MagicMock(side_effect=track_commit)

    with patch("worker.tasks.publish_event"):
        with patch("worker.tasks.time.sleep"):
            from worker.tasks import process_order

            process_order(str(mock_order.id))

    assert "processing" in statuses
    assert "completed" in statuses
    assert mock_order.status == "completed"
