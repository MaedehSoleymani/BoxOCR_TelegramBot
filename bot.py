import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import TOKEN, WEBSITE_URL, MAX_FILE_SIZE
from database import init_db, get_remaining_pages
from ocr import get_pdf_page_count

router = Router()

class UploadState(StatesGroup):
    waiting_for_image = State()
    waiting_for_pdf = State()

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼️ تبدیل عکس به متن", callback_data="upload_image")],
            [InlineKeyboardButton(text="📄 تبدیل PDF به متن", callback_data="upload_pdf")],
            [
                InlineKeyboardButton(text="ℹ️ راهنما", callback_data="help"),
                InlineKeyboardButton(text="🌐 وب‌سایت", url=WEBSITE_URL)
            ]
        ]
    )

def back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
    )

async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    remaining = await get_remaining_pages(message.from_user.id)
    await message.answer(
        "سلام! 👋\n"
        "به ربات BoxOCR خوش اومدی.\n\n"
        "با این ربات می‌تونی متن موجود در تصاویر و فایل‌های PDF رو استخراج کنی.\n\n"
        "✨ بدون نیاز به ثبت‌نام\n"
        "🖼️ پشتیبانی از تصاویر\n"
        "📄 پشتیبانی از PDF\n"
        f"🎁 اعتبار رایگان باقی‌مانده: {remaining} صفحه\n\n"
        "برای شروع یکی از گزینه‌های زیر رو انتخاب کن.",
        reply_markup=main_menu()
    )

async def show_image_menu(message: Message, state: FSMContext):
    remaining = await get_remaining_pages(message.from_user.id)

    if remaining <= 0:
        await state.clear()
        await message.answer(
            "🎁 فرصت‌های رایگان شما به پایان رسیده!\n\n"
            f"برای ادامه استفاده از خدمات به وب‌سایت ما مراجعه کن:\n{WEBSITE_URL}"
        )
        return

    await state.set_state(UploadState.waiting_for_image)
    await message.answer(
        "🖼️ لطفاً تصویر موردنظرت رو ارسال کن.\n\n"
        "فرمت‌های مجاز: JPG و PNG\n"
        "حجم مجاز: حداکثر ۱۰ مگابایت\n"
        f"اعتبار باقی‌مانده: {remaining} صفحه",
        reply_markup=back_button()
    )

async def show_pdf_menu(message: Message, state: FSMContext):
    remaining = await get_remaining_pages(message.from_user.id)

    if remaining <= 0:
        await state.clear()
        await message.answer(
            "🎁 فرصت‌های رایگان شما به پایان رسیده!\n\n"
            f"برای ادامه استفاده از خدمات به وب‌سایت ما مراجعه کن:\n{WEBSITE_URL}"
        )
        return

    await state.set_state(UploadState.waiting_for_pdf)
    await message.answer(
        "📄 لطفاً فایل PDF موردنظرت رو ارسال کن.\n\n"
        "حجم مجاز: حداکثر ۱۰ مگابایت\n"
        f"اعتبار باقی‌مانده: {remaining} صفحه",
        reply_markup=back_button()
    )

async def show_help(message: Message):
    await message.answer(
        "ℹ️ راهنمای استفاده از BoxOCR\n\n"
        "۱. نوع فایل موردنظرت رو انتخاب کن.\n"
        "۲. تصویر یا فایل PDF رو ارسال کن.\n"
        "۳. متن استخراج‌شده رو در تلگرام دریافت کن.\n\n"
        "🎁 هر کاربر ۵ صفحه اعتبار رایگان داره.\n"
        "هر تصویر یک صفحه و هر صفحه PDF یک صفحه محاسبه می‌شه.\n\n"
        "حداکثر حجم فایل: ۱۰ مگابایت",
        reply_markup=back_button()
    )

# Commands

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await show_main_menu(message, state)

@router.message(Command("image"))
async def image_command_handler(message: Message, state: FSMContext):
    await show_image_menu(message, state)

@router.message(Command("pdf"))
async def pdf_command_handler(message: Message, state: FSMContext):
    await show_pdf_menu(message, state)

@router.message(Command("help"))
async def help_command_handler(message: Message):
    await show_help(message)

# Inline keyboard handlers

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await show_main_menu(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "upload_image")
async def upload_image_handler(callback: CallbackQuery, state: FSMContext):
    await show_image_menu(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "upload_pdf")
async def upload_pdf_handler(callback: CallbackQuery, state: FSMContext):
    await show_pdf_menu(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await show_help(callback.message)
    await callback.answer()

# Image handlers

@router.message(UploadState.waiting_for_image, F.photo)
async def receive_photo_handler(message: Message, state: FSMContext, bot: Bot):
    remaining = await get_remaining_pages(message.from_user.id)

    if remaining <= 0:
        await message.answer(f"🎁 اعتبار رایگان شما تمام شده است.\n{WEBSITE_URL}")
        await state.clear()
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_data = await bot.download_file(file.file_path)
    file_data = file_data.read()

    if len(file_data) > MAX_FILE_SIZE:
        await message.answer("❌ حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
        return

    await message.answer(
        "✅ تصویر دریافت شد و بررسی اولیه آن موفق بود.\n\n"
        "⚠️ سرویس OCR هنوز به ربات متصل نشده است؛ بنابراین فعلاً متنی استخراج نمی‌شود و از سهمیه شما چیزی کم نشده است."
    )
    await state.clear()

@router.message(UploadState.waiting_for_image, F.document)
async def receive_image_document_handler(message: Message, state: FSMContext, bot: Bot):
    document = message.document

    if document.mime_type not in ("image/jpeg", "image/png"):
        await message.answer("❌ لطفاً فقط تصویر JPG یا PNG ارسال کن.")
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer("❌ حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
        return

    file = await bot.get_file(document.file_id)
    file_data = await bot.download_file(file.file_path)
    file_data = file_data.read()

    if len(file_data) > MAX_FILE_SIZE:
        await message.answer("❌ حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد.")
        return

    remaining = await get_remaining_pages(message.from_user.id)

    if remaining <= 0:
        await message.answer(f"🎁 اعتبار رایگان شما تمام شده است.\n{WEBSITE_URL}")
        await state.clear()
        return

    await message.answer(
        "✅ تصویر دریافت شد و بررسی اولیه آن موفق بود.\n\n"
        "⚠️ سرویس OCR هنوز متصل نشده است؛ سهمیه شما نیز کم نشده است."
    )
    await state.clear()

# PDF handlers

@router.message(UploadState.waiting_for_pdf, F.document)
async def receive_pdf_handler(message: Message, state: FSMContext, bot: Bot):
    document = message.document

    if document.mime_type != "application/pdf":
        await message.answer("❌ لطفاً یک فایل PDF ارسال کن.")
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer("❌ حجم فایل نباید بیشتر از ۱۰ مگابایت باشد.")
        return

    file = await bot.get_file(document.file_id)
    file_data = await bot.download_file(file.file_path)
    file_data = file_data.read()

    if len(file_data) > MAX_FILE_SIZE:
        await message.answer("❌ حجم فایل نباید بیشتر از ۱۰ مگابایت باشد.")
        return

    try:
        page_count = get_pdf_page_count(file_data)
    except Exception:
        await message.answer("❌ فایل PDF معتبر نیست یا قابل خواندن نیست.")
        return

    if page_count == 0:
        await message.answer("❌ فایل PDF هیچ صفحه‌ای ندارد.")
        return

    remaining = await get_remaining_pages(message.from_user.id)
    processable_pages = min(page_count, remaining)

    await message.answer(
        f"✅ فایل PDF دریافت شد.\n\n"
        f"📄 تعداد صفحات فایل: {page_count}\n"
        f"🎁 صفحات قابل استفاده از اعتبار رایگان: {processable_pages}\n\n"
        "⚠️ سرویس OCR هنوز متصل نشده است؛ بنابراین فعلاً متنی استخراج نمی‌شود و سهمیه‌ای از شما کم نشده است."
    )
    await state.clear()

# Invalid file handlers

@router.message(UploadState.waiting_for_image)
async def invalid_image_handler(message: Message):
    await message.answer("❌ لطفاً یک تصویر JPG یا PNG ارسال کن.")

@router.message(UploadState.waiting_for_pdf)
async def invalid_pdf_handler(message: Message):
    await message.answer("❌ لطفاً یک فایل PDF ارسال کن.")

async def main():
    if not TOKEN or TOKEN == "YOUR_TOKEN":
        raise ValueError("توکن ربات را در config.py وارد کن.")

    await init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("BoxOCR Bot is running...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())