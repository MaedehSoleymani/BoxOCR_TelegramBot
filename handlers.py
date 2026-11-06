from io import BytesIO
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from config import MAX_FILE_SIZE
from database import get_remaining_pages
from keyboards import main_menu, website_button, back_button
from ocr import get_pdf_page_count

router = Router()

# وضعیت دریافت فایل
class Upload(StatesGroup):
    waiting_for_image = State()
    waiting_for_pdf = State()

# پیام شروع
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "سلام! 👋\n"
        "به ربات BoxOCR خوش اومدی.\n\n"
        "با استفاده از این ربات می‌تونی متن موجود در "
        "تصاویر و فایل‌های PDF رو استخراج کنی.\n\n"
        "✨ بدون نیاز به ثبت‌نام\n"
        "🖼️ پشتیبانی از تصاویر\n"
        "📄 پشتیبانی از PDF\n"
        "🎁 پنج صفحه پردازش رایگان\n\n"
        "برای شروع یکی از گزینه‌های زیر رو انتخاب کن."
    )
    await message.answer(text, reply_markup=main_menu())

# بازگشت به منوی اصلی
@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "منوی اصلی BoxOCR:",
        reply_markup=main_menu()
    )
    await callback.answer()

# انتخاب تصویر
@router.callback_query(F.data == "upload_image")
async def upload_image_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.waiting_for_image)
    await callback.message.answer(
        "🖼️ لطفاً تصویر موردنظر خود را ارسال کن.\n\n"
        "فرمت‌های مجاز: JPG و PNG\n"
        "حداکثر حجم فایل: ۱۰ مگابایت",
        reply_markup=back_button()
    )
    await callback.answer()

# انتخاب PDF
@router.callback_query(F.data == "upload_pdf")
async def upload_pdf_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.waiting_for_pdf)
    await callback.message.answer(
        "📄 لطفاً فایل PDF موردنظر خود را ارسال کن.\n\n"
        "حداکثر حجم فایل: ۱۰ مگابایت",
        reply_markup=back_button()
    )
    await callback.answer()

# بررسی اعتبار رایگان
async def check_free_quota(message: Message):
    remaining = await get_remaining_pages(message.from_user.id)
    if remaining == 0:
        await message.answer(
            "🎁 سهمیه رایگان شما به پایان رسیده است!\n\n"
            "برای ادامه استفاده از BoxOCR به وب‌سایت ما مراجعه کن.",
            reply_markup=website_button()
        )
        return 0
    return remaining

# دریافت تصویر
@router.message(Upload.waiting_for_image, F.photo)
async def receive_image_handler(message: Message, state: FSMContext):
    remaining = await check_free_quota(message)
    if remaining == 0:
        await state.clear()
        return
    photo = message.photo[-1]
    if photo.file_size and photo.file_size > MAX_FILE_SIZE:
        await message.answer(
            "حجم تصویر بیشتر از ۱۰ مگابایت است. لطفاً تصویر دیگری ارسال کن."
        )
        return
    await state.clear()
    await message.answer(
        "✅ تصویر با موفقیت دریافت شد.\n\n"
        f"صفحات قابل استفاده از سهمیه رایگان: {remaining}\n\n"
        "⚙️ دریافت فایل و بررسی اولیه انجام شد.\n"
        "اتصال سرویس OCR هنوز در حال آماده‌سازی است.",
        reply_markup=main_menu()
    )

# دریافت تصویر به صورت فایل
@router.message(Upload.waiting_for_image, F.document)
async def receive_image_document_handler(message: Message, state: FSMContext):
    document = message.document
    if document.mime_type not in ["image/jpeg", "image/png"]:
        await message.answer(
            "❌ فرمت فایل معتبر نیست.\n"
            "لطفاً یک تصویر JPG یا PNG ارسال کن."
        )
        return
    remaining = await check_free_quota(message)
    if remaining == 0:
        await state.clear()
        return
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer("حجم فایل نباید بیشتر از ۱۰ مگابایت باشد.")
        return
    await state.clear()
    await message.answer(
        "✅ تصویر دریافت شد.\n\n"
        f"صفحات قابل استفاده از سهمیه رایگان: {remaining}\n\n"
        "اتصال سرویس OCR هنوز انجام نشده است.",
        reply_markup=main_menu()
    )

# دریافت PDF
@router.message(Upload.waiting_for_pdf, F.document)
async def receive_pdf_handler(message: Message, state: FSMContext):
    document = message.document
    if document.mime_type != "application/pdf":
        await message.answer(
            "❌ فایل ارسالی PDF نیست.\n"
            "لطفاً یک فایل PDF ارسال کن."
        )
        return
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer(
            "حجم فایل بیشتر از ۱۰ مگابایت است."
        )
        return
    remaining = await check_free_quota(message)
    if remaining == 0:
        await state.clear()
        return
    # دانلود فایل برای تشخیص تعداد صفحات
    file = await message.bot.get_file(document.file_id)
    buffer = BytesIO()
    await message.bot.download_file(
        file.file_path,
        destination=buffer
    )
    try:
        page_count = get_pdf_page_count(buffer.getvalue())
    except Exception:
        await message.answer(
            "❌ امکان خواندن این فایل PDF وجود ندارد.\n"
            "لطفاً یک فایل PDF معتبر و غیررمزگذاری‌شده ارسال کن."
        )
        return
    if page_count == 0:
        await message.answer("این فایل PDF صفحه‌ای برای پردازش ندارد.")
        return
    await state.clear()
    allowed_pages = min(page_count, remaining)
    text = (
        "✅ فایل PDF دریافت شد.\n\n"
        f"📄 تعداد صفحات فایل: {page_count}\n"
        f"🎁 صفحات قابل استفاده از سهمیه رایگان: {allowed_pages}\n"
        f"⛔ صفحات خارج از سهمیه: {page_count - allowed_pages}\n\n"
        "⚙️ بررسی اولیه فایل انجام شد.\n"
        "اتصال سرویس OCR هنوز در حال آماده‌سازی است."
    )

    await message.answer(text, reply_markup=main_menu())

# فایل نامعتبر
@router.message(Upload.waiting_for_image)
async def invalid_image_handler(message: Message):

    await message.answer(
        "لطفاً یک تصویر JPG یا PNG ارسال کن."
    )

@router.message(Upload.waiting_for_pdf)
async def invalid_pdf_handler(message: Message):

    await message.answer(
        "لطفاً یک فایل PDF ارسال کن."
    )

# راهنما
@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    text = (
        "ℹ️ راهنمای استفاده از BoxOCR\n\n"
        "۱. نوع فایل موردنظر را انتخاب کن.\n"
        "۲. تصویر یا PDF خود را ارسال کن.\n"
        "۳. متن استخراج‌شده را دریافت کن.\n\n"
        "فرمت تصاویر: JPG و PNG\n"
        "فرمت اسناد: PDF\n"
        "حداکثر حجم فایل: ۱۰ مگابایت\n"
        "سهمیه رایگان: ۵ صفحه برای هر کاربر\n\n"
        "برای اطلاعات بیشتر به وب‌سایت مراجعه کن."
    )
    await callback.message.answer(
        text,
        reply_markup=back_button()
    )
    await callback.answer()