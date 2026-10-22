from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_services_list():
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4

def test_get_service_by_slug_success():
    response = client.get("/api/v1/services/website-development")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "website-development"
    assert "features" in data
    assert "benefits" in data

def test_get_service_by_slug_not_found():
    response = client.get("/api/v1/services/non-existent-service-slug")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"

def test_get_content_endpoints():
    endpoints = [
        "/api/v1/content/about",
        "/api/v1/content/why-choose-us",
        "/api/v1/content/capabilities",
        "/api/v1/content/faqs",
        "/api/v1/content/contact-info",
        "/api/v1/content/social-links",
        "/api/v1/content/privacy-policy",
        "/api/v1/content/terms",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Failed at endpoint: {ep}"

def test_get_sitemap():
    response = client.get("/api/v1/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<urlset" in response.text
    assert "website-development" in response.text

def test_get_robots():
    response = client.get("/api/v1/robots.txt")
    assert response.status_code == 200
    assert "User-agent:" in response.text

def test_admin_create_and_delete_faq():
    # Test admin CRUD endpoint
    faq_payload = {
        "question": "What technologies do you use?",
        "answer": "We use modern stacks tailored to high-scale production.",
        "category": "technical",
        "display_order": 1,
        "is_published": True
    }
    create_res = client.post("/api/v1/admin/content/faqs", json=faq_payload)
    assert create_res.status_code == 201
    created_faq = create_res.json()
    faq_id = created_faq["id"]

    delete_res = client.delete(f"/api/v1/admin/content/faqs/{faq_id}")
    assert delete_res.status_code == 200