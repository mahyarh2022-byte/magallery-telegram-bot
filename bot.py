import os
import logging
import csv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("TOKEN")  # توکن را از متغیر محیطی می‌خوانیم
if not TOKEN:
    raise RuntimeError("Environment variable TOKEN not set.")

user_data = {}
(TYPING_TITLE, TYPING_DESCRIPTION, TYPING_PRICE, TYPING_PHOTOS) = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_data[user.id] = {'state': TYPING_TITLE, 'photos': []}
    await update.message.reply_html(
        f"سلام {user.mention_html()}! به ربات بارگذاری محصولات ماگالری خوش آمدی. لطفا <b>نام محصول</b> رو وارد کن."
    )
    return TYPING_TITLE

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    state = user_data.get(user_id, {}).get('state')

    if state == TYPING_TITLE:
        user_data[user_id]['title'] = update.message.text
        user_data[user_id]['state'] = TYPING_DESCRIPTION
        await update.message.reply_text("عالی! حالا <b>توضیحات محصول</b> رو برام بنویس.", parse_mode="HTML")
        return TYPING_DESCRIPTION

    elif state == TYPING_DESCRIPTION:
        user_data[user_id]['description'] = update.message.text
        user_data[user_id]['state'] = TYPING_PRICE
        await update.message.reply_text("خب، حالا <b>قیمت محصول</b> رو به تومان وارد کن.", parse_mode="HTML")
        return TYPING_PRICE

    elif state == TYPING_PRICE:
        user_data[user_id]['price'] = update.message.text
        user_data[user_id]['state'] = TYPING_PHOTOS
        await update.message.reply_text("ممنون! حالا لطفا <b>تصاویر محصول</b> رو بفرست و در پایان /done بزن.", parse_mode="HTML")
        return TYPING_PHOTOS

    else:
        await update.message.reply_text("لطفا برای شروع مجدد، دستور /start رو بزن.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_data.get(user_id, {}).get('state')
    if state == TYPING_PHOTOS:
        photo_id = update.message.photo[-1].file_id
        user_data[user_id]['photos'].append(photo_id)
        await update.message.reply_text("عکس دریافت شد. اگر عکس دیگه‌ای داری بفرست؛ وگرنه /done رو بزن.")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id].get('title'):
        await update.message.reply_text("شما هیچ محصولی رو شروع نکردید. با /start شروع کنید.")
        return

    product_info = user_data[user_id]

    # هشدار: روی Render فایل‌ها پایدار نیستند مگر دیسک اضافه کنی.
    # فعلاً به CSV می‌نویسیم؛ بعداً مستقیم به WooCommerce می‌فرستیم.
    with open('products.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['Title', 'Description', 'Price', 'Photos'])
        writer.writerow([
            product_info.get('title', ''),
            product_info.get('description', ''),
            product_info.get('price', ''),
            ' '.join(product_info.get('photos', []))
        ])

    await update.message.reply_text("اطلاعات ذخیره شد. ممنون!")
    del user_data[user_id]

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    application.run_polling()

if __name__ == "__main__":
    main()
