"""API tests for the venue presence count endpoint."""

from tests.conftest import create_session, create_user, create_venue


def test_count_endpoint_returns_camel_case_json(client, db_session):
    venue_id = create_venue(db_session)
    for _ in range(2):
        create_session(db_session, create_user(db_session), venue_id)

    response = client.get(f"/venues/{venue_id}/presence/count")

    assert response.status_code == 200
    assert response.json() == {"venueId": venue_id, "count": 2}


def test_count_endpoint_returns_zero_for_empty_venue(client, db_session):
    venue_id = create_venue(db_session)

    response = client.get(f"/venues/{venue_id}/presence/count")

    assert response.status_code == 200
    assert response.json() == {"venueId": venue_id, "count": 0}


def test_count_endpoint_returns_404_for_unknown_venue(client):
    response = client.get("/venues/unknown-venue/presence/count")

    assert response.status_code == 404
