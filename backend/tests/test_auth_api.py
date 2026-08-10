"""API tests for sign-in registration endpoint."""


def auth_body(provider: str, subject: str, email: str | None = None) -> dict:
    body = {"authProvider": provider, "authSubject": subject}
    if email is not None:
        body["email"] = email
    return body


async def test_sign_in_registers_new_user(client):
    response = client.post("/auth/sign-in", json=auth_body("yandex", "ya-777"))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["userId"]
    assert data["isNewUser"] is True


async def test_repeated_sign_in_returns_same_user(client):
    first = client.post("/auth/sign-in", json=auth_body("vk", "vk-777"))
    second = client.post("/auth/sign-in", json=auth_body("vk", "vk-777"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["userId"] == first.json()["data"]["userId"]
    assert second.json()["data"]["isNewUser"] is False


async def test_sign_in_accepts_email_provider(client):
    response = client.post(
        "/auth/sign-in", json=auth_body("email", "person@example.com", "person@example.com")
    )

    assert response.status_code == 200
    assert response.json()["data"]["isNewUser"] is True


async def test_unknown_provider_returns_422(client):
    response = client.post("/auth/sign-in", json=auth_body("telegram", "t-1"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_blank_subject_returns_422(client):
    response = client.post("/auth/sign-in", json=auth_body("email", "   "))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"