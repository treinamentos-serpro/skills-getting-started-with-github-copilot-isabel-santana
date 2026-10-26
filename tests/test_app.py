import pytest


def test_get_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    for details in activities.values():
        assert isinstance(details["description"], str)
        assert isinstance(details["schedule"], str)
        assert isinstance(details["max_participants"], int)
        assert isinstance(details["participants"], list)


def test_root_redirects_to_static_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant(client):
    expected_activities = client.get("/activities").json()
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    expected_activities["Chess Club"]["participants"].append(email)
    assert client.get("/activities").json() == expected_activities


def test_signup_rejects_duplicate_participant(client):
    original_activities = client.get("/activities").json()
    email = original_activities["Chess Club"]["participants"][0]

    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == original_activities


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_is_not_found(client, method):
    original_activities = client.get("/activities").json()

    response = client.request(
        method,
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == original_activities


def test_remove_deletes_participant(client):
    expected_activities = client.get("/activities").json()
    email = expected_activities["Chess Club"]["participants"][0]

    response = client.delete(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    expected_activities["Chess Club"]["participants"].remove(email)
    assert client.get("/activities").json() == expected_activities


def test_remove_rejects_unregistered_participant(client):
    original_activities = client.get("/activities").json()

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json() == original_activities


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_and_removal_require_email(client, method):
    original_activities = client.get("/activities").json()

    response = client.request(method, "/activities/Chess Club/signup")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] and error["type"] == "missing"
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == original_activities