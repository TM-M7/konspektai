from fastapi.testclient import TestClient

from app.main import app


def test_openapi_examples_are_bound_to_correct_models() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()["components"]["schemas"]
    assert schema["SessionCreateRequest"]["example"] == {"title": "Test lesson"}
    assert schema["TranscriptIngestRequest"]["example"]["text"] == (
        "Was ist der Unterschied zwischen RAID 0 und RAID 1?"
    )


def test_empty_text_reaches_pipeline_and_returns_rejection() -> None:
    with TestClient(app) as client:
        session = client.post("/sessions", json={"title": "API test"})
        session_id = session.json()["id"]
        response = client.post(
            "/ingest",
            json={
                "session_id": session_id,
                "timestamp": "00:40",
                "language": "de",
                "text": "",
                "confidence": 0.9,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "accepted": False,
        "reason": "empty_text",
        "segment": None,
    }


def test_websocket_events_include_event_type() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/events") as websocket:
            status_event = websocket.receive_json()

            session = client.post("/sessions", json={"title": "WS test"})
            session_id = session.json()["id"]
            client.post(
                "/ingest",
                json={
                    "session_id": session_id,
                    "timestamp": "00:35",
                    "language": "de",
                    "text": "Was ist RAID 1?",
                    "confidence": 0.91,
                },
            )
            transcript_event = websocket.receive_json()

    assert status_event["event_type"] == "status"
    assert transcript_event["event_type"] == "transcript_segment"
    assert transcript_event["payload"]["phrase_type"] == "question"


def test_question_answer_endpoint_persists_answer() -> None:
    with TestClient(app) as client:
        session = client.post("/sessions", json={"title": "Answers test"})
        session_id = session.json()["id"]
        ingest = client.post(
            "/ingest",
            json={
                "session_id": session_id,
                "timestamp": "00:35",
                "language": "de",
                "text": "Was ist RAID 1?",
                "confidence": 0.91,
            },
        )
        question_id = ingest.json()["segment"]["question_id"]
        answer = client.post(f"/questions/{question_id}/answer")

        answers = client.get(f"/sessions/{session_id}/answers")

    assert answer.status_code == 200
    assert answer.json()["question_text"] == "Was ist RAID 1?"
    assert answers.status_code == 200
    assert len(answers.json()) == 1
    assert answers.json()[0]["question_text"] == "Was ist RAID 1?"


def test_question_answer_endpoint_returns_404_for_unknown_question() -> None:
    with TestClient(app) as client:
        response = client.post("/questions/999999/answer")

    assert response.status_code == 404
    assert response.json()["detail"] == "question_not_found"


def test_export_endpoints_return_404_for_unknown_session() -> None:
    with TestClient(app) as client:
        markdown = client.post("/sessions/999999/export/markdown")
        anki = client.post("/sessions/999999/export/anki_csv")
        flashcards = client.post("/sessions/999999/flashcards/generate")

    assert markdown.status_code == 404
    assert markdown.json()["detail"] == "session_not_found"
    assert anki.status_code == 404
    assert anki.json()["detail"] == "session_not_found"
    assert flashcards.status_code == 404
    assert flashcards.json()["detail"] == "session_not_found"


def test_session_management_endpoints_list_get_and_rename() -> None:
    with TestClient(app) as client:
        created = client.post("/sessions", json={"title": "Desktop Session"})
        session_id = created.json()["id"]

        ingest = client.post(
            "/ingest",
            json={
                "session_id": session_id,
                "timestamp": "00:10",
                "language": "de",
                "text": "Was ist RAID 1?",
                "confidence": 0.93,
            },
        )
        question_id = ingest.json()["segment"]["question_id"]
        client.post(f"/questions/{question_id}/answer")

        listing = client.get("/sessions")
        detail = client.get(f"/sessions/{session_id}")
        renamed = client.patch(f"/sessions/{session_id}", json={"title": "Desktop Session Updated"})

    assert listing.status_code == 200
    assert listing.json()[0]["id"] == session_id
    assert listing.json()[0]["question_count"] >= 1
    assert detail.status_code == 200
    assert detail.json()["answer_count"] >= 1
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Desktop Session Updated"


def test_session_detail_and_rename_return_404_for_unknown_session() -> None:
    with TestClient(app) as client:
        detail = client.get("/sessions/999999")
        renamed = client.patch("/sessions/999999", json={"title": "Missing"})

    assert detail.status_code == 404
    assert detail.json()["detail"] == "session_not_found"
    assert renamed.status_code == 404
    assert renamed.json()["detail"] == "session_not_found"
