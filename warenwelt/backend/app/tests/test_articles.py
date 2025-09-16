from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.article import create_random_article
from app.tests.utils.user import create_random_user, get_user_authentication_headers


def test_create_article(client: TestClient, db_session: Session) -> None:
    user_data = create_random_user(db_session)
    user = user_data["user"]
    headers = get_user_authentication_headers(
        client=client, email=user_data["email"], password=user_data["password"]
    )
    data = {"name": "Test Article", "description": "This is a test article", "price": 10.5}
    response = client.post(
        f"{settings.API_V1_STR}/articles/",
        headers=headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["price"] == data["price"]
    assert "id" in content
    assert content["owner"]["id"] == user.id


def test_read_article(client: TestClient, db_session: Session) -> None:
    user_data = create_random_user(db_session)
    user = user_data["user"]
    article = create_random_article(db_session, owner_id=user.id)
    headers = get_user_authentication_headers(
        client=client, email=user_data["email"], password=user_data["password"]
    )
    response = client.get(
        f"{settings.API_V1_STR}/articles/{article.id}",
        headers=headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == article.name
    assert content["description"] == article.description
    assert content["price"] == article.price
    assert content["id"] == article.id
    assert content["owner"]["id"] == user.id
