Перепиши этот класс в Pydantic v2:
- Замени `class Config` на `model_config = ConfigDict(...)`.
- Убери `from_attributes = True` (не нужно).
- Замени `@validator` на `@field_validator` + `@classmethod`.
- Для каждого поля добавь Field(description=..., examples=[...] где полезно).
- Для опционального summary добавь `= None`.
- Не меняй логику.