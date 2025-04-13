**Инструкция по установке**

Создайте структуру папок:


    config/
        └── custom_components/
        └── hite_pro/
            ├── __init__.py
            ├── config_flow.py
            ├── manifest.json
            ├── button.py
            ├── switch.py
            ├── light.py
            ├── sensor.py
            └── binary_sensor.py

Перезагрузите Home Assistant

**Добавьте интеграцию через UI:**
- Настройки → Устройства и службы → Добавить интеграцию
- Найдите "HiTE-PRO Auto Discovery"
- Введите MQTT topic (по умолчанию /devices/hite-pro/controls/#)

**Проверьте работу:**
- Устройства должны появиться автоматически
- Проверьте лог на ошибки
