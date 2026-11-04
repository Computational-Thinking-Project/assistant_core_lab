import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from assistant_api.db import ChatSession, Feedback, Interaction, Repository, hash_session, init_db, make_engine


def make_repo():
    engine = make_engine("sqlite://")
    init_db(engine)
    return Repository(engine, "salt"), engine


def test_session_id_is_hashed():
    repo, engine = make_repo()
    repo.record_interaction("student-42", "r1", "fee", None, True, False, 3.0)
    with Session(engine) as db:
        s = db.exec(select(ChatSession)).one()
    assert s.id == hash_session("student-42", "salt") and "student-42" not in s.id


def test_one_session_many_interactions():
    repo, engine = make_repo()
    for i in range(3):
        repo.record_interaction("s", f"r{i}", "rule", "H26-5.3", True, False, 10.0)
    with Session(engine) as db:
        assert len(db.exec(select(ChatSession)).all()) == 1
        assert len(db.exec(select(Interaction)).all()) == 3


def test_feedback_requires_existing_interaction():
    repo, _ = make_repo()
    assert repo.add_feedback("missing", 1, None) is None
    repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
    fb = repo.add_feedback("r1", -1, "wrong fee")
    assert fb is not None and fb.id == 1


def test_list_feedback_ordering_and_limit():
    repo, _ = make_repo()
    repo.record_interaction("s", "r1", "fee", None, True, False, 1.0)
    repo.record_interaction("s", "r2", "rule", None, True, False, 1.0)
    repo.add_feedback("r1", 1, "good")
    repo.add_feedback("r2", -1, "bad")
    feedbacks = repo.list_feedback(limit=10)
    assert len(feedbacks) == 2
    assert feedbacks[0].request_id == "r2"
    assert feedbacks[1].request_id == "r1"
    assert len(repo.list_feedback(limit=1)) == 1


def test_sqlite_foreign_key_enforcement():
    _, engine = make_repo()
    with pytest.raises(IntegrityError):
        with Session(engine) as db:
            fb = Feedback(request_id="non-existent-request", rating=1)
            db.add(fb)
            db.commit()

