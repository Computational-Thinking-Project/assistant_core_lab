"""Verify that feedback survives recreation of the API with a file database."""

from fastapi.testclient import TestClient

from assistant_api.main import create_app


def test_feedback_survives_app_recreation(tmp_path, settings, service):
    database = tmp_path / "assistant.db"
    qa_settings = settings.model_copy(
        update={
            "database_url": f"sqlite:///{database.as_posix()}",
            "session_salt": "qa-test-salt",
            "api_admin_key": "qa-test-admin-key",
        }
    )

    with TestClient(create_app(qa_settings, service)) as first_client:
        chat = first_client.post("/v1/chat", json={"message": "hi", "session_id": "qa-session"})
        assert chat.status_code == 200
        request_id = chat.json()["request_id"]

        feedback = first_client.post(
            "/v1/feedback",
            json={"request_id": request_id, "rating": 1, "comment": "clear answer"},
        )
        assert feedback.status_code == 201
        saved = feedback.json()
        assert saved["id"] > 0
        assert saved["request_id"] == request_id
        assert saved["rating"] == 1
        assert saved["comment"] == "clear answer"
        assert saved["created_at"]

    assert database.is_file()

    with TestClient(create_app(qa_settings, service)) as second_client:
        assert second_client.get("/v1/feedback").status_code == 401
        response = second_client.get("/v1/feedback?limit=10", headers={"X-API-Key": "qa-test-admin-key"})

    assert response.status_code == 200
    assert response.json() == [saved]
