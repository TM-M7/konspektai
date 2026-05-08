from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AIAnswerRecord


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


def test_question_ingest_emits_ai_answer_and_persists_it(monkeypatch) -> None:
    async def fake_generate_answer_text(_: str) -> str:
        return "RAID 1 spiegelt Daten auf zwei Festplatten. RU: RAID 1 зеркалирует данные."

    monkeypatch.setattr("app.main.answer_service._generate_answer_text", fake_generate_answer_text)

    with TestClient(app) as client:
        session = client.post("/sessions", json={"title": "Answers test"})
        session_id = session.json()["id"]

        with client.websocket_connect("/ws/events") as websocket:
            websocket.receive_json()
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
            status_event = websocket.receive_json()
            answer_event = websocket.receive_json()
            completion_event = websocket.receive_json()

        answers = client.get(f"/sessions/{session_id}/answers")

    assert transcript_event["event_type"] == "transcript_segment"
    assert status_event["event_type"] == "status"
    assert status_event["payload"]["state"] == "thinking"
    assert answer_event["event_type"] == "ai_answer"
    assert answer_event["payload"]["question_text"] == "Was ist RAID 1?"
    assert completion_event["event_type"] == "status"
    assert completion_event["payload"]["state"] == "completed"
    assert answers.status_code == 200
    assert len(answers.json()) == 1
    assert answers.json()[0]["question_text"] == "Was ist RAID 1?"
