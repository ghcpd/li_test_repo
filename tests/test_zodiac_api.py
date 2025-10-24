import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_homepage_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Zodiac Explorer" in response.data


def test_list_all_zodiacs(client):
    response = client.get("/zodiacs")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == 12
    assert len(payload["zodiacs"]) == 12
    sample = payload["zodiacs"][0]
    assert {"name", "slug", "date_range", "element", "traits", "origin", "symbol", "color"}.issubset(sample.keys())


def test_search_by_name(client):
    response = client.get("/zodiacs", query_string={"q": "leo"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == 1
    assert payload["zodiacs"][0]["name"] == "Leo"


def test_filter_by_element(client):
    response = client.get("/zodiacs", query_string={"element": "Water"})
    assert response.status_code == 200
    payload = response.get_json()
    elements = {item["element"] for item in payload["zodiacs"]}
    assert elements == {"Water"}


def test_combined_search_and_filter(client):
    response = client.get("/zodiacs", query_string={"q": "a", "element": "Fire"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == len(payload["zodiacs"])
    assert all(item["element"] == "Fire" for item in payload["zodiacs"])
    assert any(item["name"] == "Aries" for item in payload["zodiacs"])


def test_random_zodiac(client):
    responses = {client.get("/zodiacs/random").get_json()["slug"] for _ in range(5)}
    assert responses <= {"aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"}
    assert responses  # at least one response captured


def test_zodiac_detail_success(client):
    response = client.get("/zodiacs/aries")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["name"] == "Aries"


def test_zodiac_detail_not_found(client):
    response = client.get("/zodiacs/ophichus")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["error"] == "Not Found"
