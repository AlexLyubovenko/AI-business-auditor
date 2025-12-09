from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# integrations/telegram/keyboards.py (добавьте в get_main_menu)
def get_main_menu():
    """Главное меню с кнопками"""
    keyboard = [
        [KeyboardButton("📊 Анализ файла")],
        [KeyboardButton("🤖 GPT Анализ"), KeyboardButton("📋 Отчеты")],
        [KeyboardButton("📈 Метрики"), KeyboardButton("🏢 AmoCRM")],
        [KeyboardButton("💡 Советы"), KeyboardButton("❓ Помощь")],
        [KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

def get_file_types_keyboard():
    """Клавиатура для выбора типа файла"""
    buttons = [
        [
            InlineKeyboardButton("📁 CSV", callback_data="file_csv"),
            InlineKeyboardButton("📊 Excel", callback_data="file_excel")
        ],
        [
            InlineKeyboardButton("📄 JSON", callback_data="file_json"),
            InlineKeyboardButton("📝 TXT", callback_data="file_txt")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_analysis_options_keyboard():
    """Опции анализа"""
    buttons = [
        [
            InlineKeyboardButton("📊 Быстрый анализ", callback_data="analysis_quick"),
            InlineKeyboardButton("🤖 GPT анализ", callback_data="analysis_gpt")
        ],
        [
            InlineKeyboardButton("📈 Графики", callback_data="analysis_charts"),
            InlineKeyboardButton("📋 Полный отчет", callback_data="analysis_full")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_files")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_amocrm_menu():
    """Меню AmoCRM"""
    buttons = [
        [
            InlineKeyboardButton("📋 Список сделок", callback_data="amo_leads"),
            InlineKeyboardButton("💰 Статистика", callback_data="amo_stats")
        ],
        [
            InlineKeyboardButton("👥 Контакты", callback_data="amo_contacts"),
            InlineKeyboardButton("📅 События", callback_data="amo_events")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="amo_refresh"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_reports_menu():
    """Меню отчетов"""
    buttons = [
        [
            InlineKeyboardButton("📄 PDF", callback_data="report_pdf"),
            InlineKeyboardButton("📝 Markdown", callback_data="report_md")
        ],
        [
            InlineKeyboardButton("📊 Excel", callback_data="report_excel"),
            InlineKeyboardButton("📋 JSON", callback_data="report_json")
        ],
        [
            InlineKeyboardButton("📊 Текущий анализ", callback_data="report_current"),
            InlineKeyboardButton("📈 Графики", callback_data="report_charts")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_metrics_dashboard():
    """Дашборд метрик"""
    buttons = [
        [
            InlineKeyboardButton("📈 Финансы", callback_data="metrics_finance"),
            InlineKeyboardButton("👥 Клиенты", callback_data="metrics_clients")
        ],
        [
            InlineKeyboardButton("📊 Продажи", callback_data="metrics_sales"),
            InlineKeyboardButton("⏱️ Эффективность", callback_data="metrics_efficiency")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="metrics_refresh"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_tips_categories():
    """Категории советов"""
    buttons = [
        [
            InlineKeyboardButton("💰 Финансы", callback_data="tips_finance"),
            InlineKeyboardButton("📈 Продажи", callback_data="tips_sales")
        ],
        [
            InlineKeyboardButton("👥 Маркетинг", callback_data="tips_marketing"),
            InlineKeyboardButton("⚙️ Операции", callback_data="tips_operations")
        ],
        [
            InlineKeyboardButton("🎯 Случайный совет", callback_data="tips_random"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_settings_menu():
    """Меню настроек"""
    buttons = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notify"),
            InlineKeyboardButton("🌙 Тема", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton("🔄 Автообновление", callback_data="settings_auto"),
            InlineKeyboardButton("📧 Email отчеты", callback_data="settings_email")
        ],
        [
            InlineKeyboardButton("🧹 Очистить данные", callback_data="settings_clear"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_main")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    buttons = [
        [
            InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_navigation_keyboard():
    """Навигационные кнопки"""
    buttons = [
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="nav_back"),
            InlineKeyboardButton("🏠 Главная", callback_data="nav_home"),
            InlineKeyboardButton("Далее ➡️", callback_data="nav_next")
        ]
    ]
    return InlineKeyboardMarkup(buttons)