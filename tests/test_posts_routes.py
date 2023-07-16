import pytest

from tests.test_accounts_routes import client

AUTHORIZED_ACCESS_ROUTES = [
    ("/posts/", "GET"),
    ("/posts/user", "GET"),
    ("/posts/1", "GET"),
    ("/posts/1", "PUT"),
    ("/posts/1", "DELETE"),
]


@pytest.fixture
def test_access_token():
    response = client.post(
        "/accounts/login", data={
            "username": "GuildNavigator",
            "password": "password1"
        }
    )
    assert response.status_code == 200
    response_json = response.json()
    assert "access_token" in response_json
    assert response_json["token_type"] == "bearer"
    return response_json["access_token"]


@pytest.mark.parametrize("route, method", AUTHORIZED_ACCESS_ROUTES)
def test_unauthorized_access(route, method):
    response = None
    if method == "GET":
        response = client.get(route)
    elif method == "POST":
        response = client.post(route)
    elif method == "PUT":
        response = client.put(route)
    elif method == "DELETE":
        response = client.delete(route)

    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    "title, text, expected_status_code",
    [
        ("Test Post 1", "This is test post 1.", 201),  # Successful post creation
        ("", "This is test post 2.", 201),  # Empty title: should be ok
        ("Test Post 3", "", 422),  # Empty text: should return error
        ("Test Post 4", None, 422),  # Text not provided: should return error
    ]
)
def test_create_new_post(title: str, text: str, expected_status_code: int, test_access_token):
    response = client.post(
        "/posts/",
        json={"title": title, "text": text},
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == expected_status_code
    if response.status_code == 201:
        data = response.json()
        assert "id" in data
        assert data["title"] == title
        assert data["text"] == text
        assert "author_id" in data
        assert "created_at" in data


@pytest.mark.parametrize(
    "limit, offset, expected_status_code",
    [
        (10, 0, 200),  # Successful request with default limit and offset
        (5, 0, 200),  # Successful request with custom limit and default offset
        (10, 5, 200),  # Successful request with custom offset and default limit
        (0, 0, 422),  # Invalid limit: zero (less than 1)
        (-5, 0, 422),  # Invalid limit: negative value
        (10, -5, 422),  # Invalid offset: negative value
    ]
)
def test_get_all_posts(limit: int, offset: int, expected_status_code: int, test_access_token):
    response = client.get(
        "/posts/",
        params={"limit": limit, "offset": offset},
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == expected_status_code
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        for post in data:
            assert "id" in post
            assert "title" in post
            assert "text" in post
            assert "author_id" in post
            assert "created_at" in post


@pytest.mark.parametrize("expected_status_code", [200])
def test_get_user_posts(expected_status_code: int, test_access_token):
    response = client.get(
        "/posts/user",
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == expected_status_code
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["author_id"] == 1


@pytest.mark.parametrize(
    "post_id, expected_status_code",
    [
        (2, 200),  # Existing post ID
        (1000, 404),  # Invalid post ID
    ]
)
def test_get_single_post(post_id: int, expected_status_code: int, test_access_token):
    response = client.get(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == expected_status_code
    if response.status_code == 404:
        data = response.json()
        assert data["detail"] == "Post not found"


@pytest.mark.parametrize(
    "post_id, request_data, expected_status_code, expected_response",
    [
        (2, {"title": "Updated Title", "text": "Updated Text"}, 200,
         {"title": "Updated Title", "text": "Updated Text"}),  # Update existing post
        (1000, {"title": "Invalid Post", "text": "Invalid Text"}, 404, None),  # Invalid post ID
        (2, {"text": "New Updated text"}, 200,
         {"title": "Updated Title", "text": "New Updated text"}),  # Update only text
        (2, {"title": "New Updated Title"}, 200,
         {"title": "New Updated Title", "text": "New Updated text"}),  # Update only title
        (2, {"text": ""}, 422, None),  # Trying to delete the text and save empty value. Should return error
    ]
)
def test_update_user_post(post_id: int, request_data: dict, expected_status_code: int, expected_response: dict, test_access_token):
    response = client.put(
        f"/posts/{post_id}",
        json=request_data,
        headers={"Authorization": f"Bearer {test_access_token}"}
    )
    assert response.status_code == expected_status_code
    if expected_response:
        assert response.json()["title"] == expected_response["title"]
        assert response.json()["text"] == expected_response["text"]
