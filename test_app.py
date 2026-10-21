
from fastapi.testclient import TestClient
from app_final import app

client = TestClient(app)


# тест на работоспособность
def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# тест на вывод ожидаемого
def test_recommendations():

    response = client.get(
        "/recommend",
        params={
            "budget": "экономный",
            "continent": "азия",
            "month": 2,
            "climate": "жаркий",
            "interests": "история",
            "rest": "активный"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 4
    assert data["recommendations"][0]["country"] == "Вьетнам"
    assert data["recommendations"][0]["score"] == 95



# тест на ошибки в введенном месяце
def test_invalid_month():

    response = client.get(
        "/recommend",
        params={
            "budget": "экономный",
            "continent": "азия",
            "month": 13,
            "climate": "жаркий",
            "interests": "история",
            "rest": "активный"
        }
    )

    assert response.status_code == 422

    assert response.json()["detail"][0]["loc"] == ["query", "month"]


# тест на ввод бюджета
def test_invalid_budget():

    response = client.get(
        "/recommend",
        params={
            "budget": "Выберите из списка",
            "continent": "азия",
            "month": 6,
            "climate": "жаркий",
            "interests": "история",
            "rest": "активный"
        }
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Поле «Бюджет»: выберите из списка"
    }


    
def test_other_dropdowns():

    fields = {
        "continent": "Континент",
        "climate": "Климат",
        "rest": "Тип отдыха"
    }

    for field, field_name in fields.items():

        params = {
            "budget": "экономный",
            "continent": "азия",
            "month": 6,
            "climate": "жаркий",
            "interests": "история",
            "rest": "активный"
        }

        # Подставляем неправильное значение в проверяемое поле
        params[field] = "Выберите из списка"

        response = client.get("/recommend", params=params)

        assert response.status_code == 400

        assert response.json() == {
            "detail": f"Поле «{field_name}»: выберите из списка"
        }


