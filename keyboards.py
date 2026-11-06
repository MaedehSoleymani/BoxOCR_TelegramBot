from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import WEBSITE_URL

def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼️ تبدیل عکس به متن",
                    callback_data="upload_image"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 تبدیل PDF به متن",
                    callback_data="upload_pdf"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ راهنما",
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    text="🌐 وب‌سایت",
                    url=WEBSITE_URL
                )
            ]
        ]
    )
    return keyboard

def website_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 ورود به وب‌سایت BoxOCR",
                    url=WEBSITE_URL
                )
            ]
        ]
    )
    return keyboard

def back_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به منوی اصلی",
                    callback_data="main_menu"
                )
            ]
        ]
    )
    return keyboard