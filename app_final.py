
from fastapi import FastAPI, HTTPException
from countries_data import countries
import os
import logging

# Запускаем логгирование (выводы каждого действия)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("travel_compass")


APP_NAME = os.getenv("APP_NAME", "Travel Compass")

app = FastAPI(
    title=APP_NAME,
    description="Система рекомендаций стран для путешествий",
    version="1.0.0"
)

budget_levels = {
    "экономный": 1,
    "средний": 2,
    "высокий": 3
}


# Подсчет баллов
def calculate_score(info, user_month, user_climate, user_interests, user_rest):

    score = 0

    # Сезонность — 20 баллов
    if user_month in info["best_months"]:
        score += 20

    # Климат — 15 баллов
    if user_climate in info["climate"]:
        score += 15

    # Интересы — до 50 баллов
    matching_interests = set(user_interests) & set(info["interests"])

    if user_interests:
        score += 50 * len(matching_interests) / len(user_interests)

    # Тип отдыха — 15 баллов
    country_rest = info["rest_type"]

    if user_rest == country_rest:
        score += 15
    elif user_rest == "смешанный" or country_rest == "смешанный":
        score += 10

    return round(score, 2)


# Вывод причин
def get_reasons(info, user_month, user_climate, user_interests, user_rest):

    reasons = []

    if user_month in info["best_months"]:
        reasons.append("подходящий сезон")

    if user_climate in info["climate"]:
        reasons.append("подходящий климат")

    matching_interests = [
        interest for interest in user_interests
        if interest in info["interests"]
    ]

    if matching_interests:
        reasons.append("интересы: " + ", ".join(matching_interests))

    if user_rest == info["rest_type"]:
        reasons.append("подходящий тип отдыха")
    elif user_rest == "смешанный" or info["rest_type"] == "смешанный":
        reasons.append("частично подходящий тип отдыха")

    return reasons


# вывод топ 5 стран
def recommend_countries(user_budget, user_continent, user_month,
                        user_climate, user_interests, user_rest):

    results = []

    for name, info in countries.items():

        # Фильтр бюджета
        if budget_levels[info["budget"]] > budget_levels[user_budget]:
            continue

        # Фильтр континента
        country_continent = info["continent"].lower()

        if user_continent == "америка":
            if country_continent not in ["северная америка", "южная америка"]:
                continue

        elif user_continent != "любой" and country_continent != user_continent:
            continue

        # Рассчитываем баллы
        score = calculate_score(
            info, user_month, user_climate, user_interests, user_rest
        )

        # Получаем причины
        reasons = get_reasons(
            info, user_month, user_climate, user_interests, user_rest
        )

        results.append({
            "country": name,
            "score": score,
            "reasons": reasons
        })

    results = sorted(
        results,
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:5]



@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": app.version}

# вывод всех стран
@app.get("/countries")
def get_countries():

    country_names = list(countries.keys())

    return {
        "total": len(country_names),
        "countries": country_names
    }


# вывод информации по введенной стране
@app.get("/countries/{name}")
def get_country(name: str):

    if name not in countries:
        raise HTTPException(
            status_code=404,
            detail="Страна не найдена"
        )

    return {
        "country": name,
        "information": countries[name]
    }



# ввод информации от пользователя
@app.get("/recommend")
def get_recommendations(
    budget: str,
    continent: str,
    month: int,
    climate: str,
    interests: str,
    rest: str
):

    # Приводим текст к единому формату
    budget = budget.strip().lower()
    continent = continent.strip().lower()
    climate = climate.strip().lower()
    rest = rest.strip().lower()

    # Проверяем бюджет
    if budget not in budget_levels:
        raise HTTPException(
            status_code=400,
            detail="Некорректный бюджет"
        )

    # Проверяем месяц
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Месяц должен быть от 1 до 12"
        )

    # Преобразуем интересы в список
    user_interests = [
        interest.strip().lower()
        for interest in interests.split(",")
        if interest.strip()
    ]

    user_interests = list(dict.fromkeys(user_interests))

    # Вызываем наш алгоритм
    recommendations = recommend_countries(
        budget,
        continent,
        month,
        climate,
        user_interests,
        rest
    )

    logger.info(
        "Подобрано направлений: %s",
        len(recommendations)
    )

    
    return {
        "total": len(recommendations),
        "recommendations": recommendations
    }

