"""Unit tests for football-data.org score sync status handling."""

from app.services.score_sync import resolve_sync_status


def test_resolve_sync_status_maps_finished_to_completed():
    status, ignored = resolve_sync_status("FINISHED", "in_progress")
    assert status == "completed"
    assert ignored is False


def test_resolve_sync_status_maps_extra_time_to_in_progress():
    status, ignored = resolve_sync_status("EXTRA_TIME", "upcoming")
    assert status == "in_progress"
    assert ignored is False


def test_resolve_sync_status_blocks_completed_to_in_progress():
    status, ignored = resolve_sync_status("IN_PLAY", "completed")
    assert status == "completed"
    assert ignored is True


def test_resolve_sync_status_blocks_completed_to_upcoming():
    status, ignored = resolve_sync_status("TIMED", "completed")
    assert status == "completed"
    assert ignored is True


def test_resolve_sync_status_unknown_api_status_keeps_current():
    status, ignored = resolve_sync_status("WEIRD_STATUS", "completed")
    assert status == "completed"
    assert ignored is False
