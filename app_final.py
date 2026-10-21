
from fastapi import FastAPI, HTTPException, Query
from countries_data import countries
from enum import Enum
from typing import Annotated
import os
import logging




# Классы для выпадающих списков

class Budget(str, Enum):
    choose = "Выберите из списка"
    economy = "экономный"
    medium = "средний"
    high = "высокий"


class Continent(str, Enum):
    choose = "Выберите из списка"
    europe = "европа"
    asia = "азия"
    africa = "африка"
    america = "америка"
    oceania = "океания"
    any = "любой"


class Climate(str, Enum):
    choose = "Выберите из списка"
    hot = "жаркий"
    warm = "тёплый"
    moderate = "умеренный"
    cool = "прохладный"


class RestType(str, Enum):
    choose = "Выберите из списка"
    calm = "спокойный"
    active = "активный"
    mixed = "смешанный"



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
    budget: Annotated[Budget, Query(description="Выберите из списка")],
    continent: Annotated[Continent, Query(description="Выберите из списка")],
    month: Annotated[int, Query(
        description="Введите номер месяца от 1 до 12",
        ge=1,
        le=12
    )],
    climate: Annotated[Climate, Query(description="Выберите из списка")],
    interests: Annotated[str, Query(
        description="Введите интересы через запятую: море, история, природа, развлечения, гастрономия, спорт"
    )],
    rest: Annotated[RestType, Query(description="Выберите из списка")]
):


    budget = budget.value
    continent = continent.value
    climate = climate.value
    rest = rest.value

    
    
    # Проверяем выбор пользователя в каждом поле
    fields = {
        "Бюджет": budget,
        "Континент": continent,
        "Климат": climate,
        "Тип отдыха": rest
    }

    for field_name, value in fields.items():
        if value == "Выберите из списка":
            raise HTTPException(
                status_code=400,
                detail=f"Поле «{field_name}»: выберите из списка"
            )
        

    # Преобразуем интересы в список
    user_interests = [
        interest.strip().lower()
        for interest in interests.split(",")
        if interest.strip()
    ]

    user_interests = list(dict.fromkeys(user_interests))



    
    valid_interests = [
        "море",
        "история",
        "природа",
        "развлечения",
        "гастрономия",
        "спорт"
    ]


    # Пользователь не указал интересы вообще или ввёл значение, которого нет в нашем справочнике
    if not user_interests:
        raise HTTPException(
            status_code=400,
            detail="Укажите хотя бы один интерес"
        )

    invalid_interests = [
        interest for interest in user_interests
        if interest not in valid_interests
    ]

    if invalid_interests:
        raise HTTPException(
            status_code=400,
            detail="Недопустимые интересы: " + ", ".join(invalid_interests)
        )


    

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

