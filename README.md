**Инструкция по установке**

Создайте структуру папок:

config/
└── custom_components/

    └── hite_pro/
    
        ├── __init__.py
        
        ├── manifest.json
        
        └── strings.json

Перезагрузите Home Assistant

**Добавьте интеграцию через UI:**
- Настройки → Устройства и службы → Добавить интеграцию
- Найдите "HiTE-PRO Auto Discovery"
- Введите MQTT topic (по умолчанию /devices/hite-pro/controls/#)

**Проверьте работу:**
- Устройства должны появиться автоматически
- Проверьте лог на ошибки
