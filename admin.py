
import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Bot token from environment
BOT_TOKEN = os.environ.get('YOUR_BOT_TOKEN')

# Admin chat ID
ADMIN_ID = 58573285

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON file paths
USER_DB = "user.json"
GAME_DB = "game.json"
DEPOSIT_DB = "deposit.json"
WITHDRAWAL_DB = "withdrawal.json"
LOGIC_DB = "logic.json"
WALLET_DB = "wallet.json"

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
        return

    keyboard = [
        [InlineKeyboardButton("مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("تغییر منطق بازی", callback_data="admin_logic")],
        [InlineKeyboardButton("درخواست‌های واریز", callback_data="admin_deposits")],
        [InlineKeyboardButton("درخواست‌های برداشت", callback_data="admin_withdrawals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("پنل ادمین:", reply_markup=reply_markup)

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("شما دسترسی ادمین ندارید.")
        return

    if query.data == "admin_users":
        users = load_json(USER_DB)
        if not users:
            await query.edit_message_text("کاربری یافت نشد.")
            return
            
        text = "کاربران:\n\n"
        keyboard = []
        
        for user in users[:10]:  # Show first 10 users
            text += f"ID: {user['ID']} | @{user['Username']} | موجودی: {user['Balance']} | وضعیت: {user['Status']}\n"
            keyboard.append([InlineKeyboardButton(f"ویرایش {user['Username']}", callback_data=f"edit_user_{user['ID']}")])
        
        keyboard.append([InlineKeyboardButton("برگشت", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data == "admin_logic":
        logic = load_json(LOGIC_DB)[0]
        text = f"منطق فعلی بازی:\n\nدرصد برد: {logic['win']}%\nدرصد باخت: {logic['lose']}%\nتصادفی: {'بله' if logic['random'] else 'خیر'}"
        
        keyboard = [
            [InlineKeyboardButton("تغییر درصد برد", callback_data="change_win")],
            [InlineKeyboardButton("تغییر درصد باخت", callback_data="change_lose")],
            [InlineKeyboardButton("تغییر حالت تصادفی", callback_data="toggle_random")],
            [InlineKeyboardButton("برگشت", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data == "admin_deposits":
        deposits = load_json(DEPOSIT_DB)
        pending_deposits = [d for d in deposits if d['status'] == 'Pending']
        
        if not pending_deposits:
            keyboard = [[InlineKeyboardButton("برگشت", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("درخواست واریز در انتظاری وجود ندارد.", reply_markup=reply_markup)
            return
        
        text = "درخواست‌های واریز در انتظار:\n\n"
        keyboard = []
        
        for deposit in pending_deposits[:5]:  # Show first 5 pending
            text += f"ID: {deposit['ID']} | @{deposit['Username']} | مبلغ: {deposit['amount']} | روش: {deposit['side']}\n"
            keyboard.append([InlineKeyboardButton(f"بررسی {deposit['ID']}", callback_data=f"review_deposit_{deposit['ID']}")])
        
        keyboard.append([InlineKeyboardButton("برگشت", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data == "admin_withdrawals":
        withdrawals = load_json(WITHDRAWAL_DB)
        pending_withdrawals = [w for w in withdrawals if w['status'] == 'Pending']
        
        if not pending_withdrawals:
            keyboard = [[InlineKeyboardButton("برگشت", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("درخواست برداشت در انتظاری وجود ندارد.", reply_markup=reply_markup)
            return
        
        text = "درخواست‌های برداشت در انتظار:\n\n"
        keyboard = []
        
        for withdrawal in pending_withdrawals[:5]:  # Show first 5 pending
            text += f"ID: {withdrawal['ID']} | @{withdrawal['Username']} | مبلغ: {withdrawal['amount']} | روش: {withdrawal['side']}\n"
            keyboard.append([InlineKeyboardButton(f"بررسی {withdrawal['ID']}", callback_data=f"review_withdrawal_{withdrawal['ID']}")])
        
        keyboard.append([InlineKeyboardButton("برگشت", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data.startswith("edit_user_"):
        user_id = int(query.data.split("_")[2])
        users = load_json(USER_DB)
        user = next((u for u in users if u['ID'] == user_id), None)
        
        if not user:
            await query.edit_message_text("کاربر یافت نشد.")
            return
        
        text = f"ویرایش کاربر:\n\nID: {user['ID']}\nنام کاربری: @{user['Username']}\nموجودی: {user['Balance']}\nوضعیت: {user['Status']}\nتوضیحات: {user['Description']}"
        
        keyboard = [
            [InlineKeyboardButton("تغییر موجودی", callback_data=f"change_balance_{user_id}")],
            [InlineKeyboardButton("تغییر وضعیت", callback_data=f"change_status_{user_id}")],
            [InlineKeyboardButton("برگشت", callback_data="admin_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data.startswith("review_deposit_"):
        deposit_id = int(query.data.split("_")[2])
        deposits = load_json(DEPOSIT_DB)
        deposit = next((d for d in deposits if d['ID'] == deposit_id), None)
        
        if not deposit:
            await query.edit_message_text("درخواست یافت نشد.")
            return
        
        text = f"بررسی درخواست واریز:\n\nID: {deposit['ID']}\nکاربر: @{deposit['Username']}\nمبلغ: {deposit['amount']}\nروش: {deposit['side']}\nاطلاعات: {deposit['information']}"
        
        keyboard = [
            [InlineKeyboardButton("تأیید", callback_data=f"accept_deposit_{deposit_id}"),
             InlineKeyboardButton("رد", callback_data=f"reject_deposit_{deposit_id}")],
            [InlineKeyboardButton("برگشت", callback_data="admin_deposits")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data.startswith("review_withdrawal_"):
        withdrawal_id = int(query.data.split("_")[2])
        withdrawals = load_json(WITHDRAWAL_DB)
        withdrawal = next((w for w in withdrawals if w['ID'] == withdrawal_id), None)
        
        if not withdrawal:
            await query.edit_message_text("درخواست یافت نشد.")
            return
        
        text = f"بررسی درخواست برداشت:\n\nID: {withdrawal['ID']}\nکاربر: @{withdrawal['Username']}\nمبلغ: {withdrawal['amount']}\nروش: {withdrawal['side']}\nکیف پول: {withdrawal['wallet-code']}"
        
        keyboard = [
            [InlineKeyboardButton("تأیید", callback_data=f"accept_withdrawal_{withdrawal_id}"),
             InlineKeyboardButton("رد", callback_data=f"reject_withdrawal_{withdrawal_id}")],
            [InlineKeyboardButton("برگشت", callback_data="admin_withdrawals")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        
    elif query.data.startswith("accept_deposit_"):
        deposit_id = int(query.data.split("_")[2])
        deposits = load_json(DEPOSIT_DB)
        
        for deposit in deposits:
            if deposit['ID'] == deposit_id:
                deposit['status'] = 'Accept'
                
                # Update user balance
                users = load_json(USER_DB)
                for user in users:
                    if user['ID-Telegram'] == deposit['ID-Telegram']:
                        user['Balance'] += deposit['amount']
                        break
                save_json(USER_DB, users)
                break
        
        save_json(DEPOSIT_DB, deposits)
        await query.edit_message_text("درخواست واریز تأیید شد و موجودی کاربر بروزرسانی شد.")
        
    elif query.data.startswith("reject_deposit_"):
        deposit_id = int(query.data.split("_")[2])
        deposits = load_json(DEPOSIT_DB)
        
        for deposit in deposits:
            if deposit['ID'] == deposit_id:
                deposit['status'] = 'Reject'
                break
        
        save_json(DEPOSIT_DB, deposits)
        await query.edit_message_text("درخواست واریز رد شد.")
        
    elif query.data.startswith("accept_withdrawal_"):
        withdrawal_id = int(query.data.split("_")[2])
        withdrawals = load_json(WITHDRAWAL_DB)
        
        for withdrawal in withdrawals:
            if withdrawal['ID'] == withdrawal_id:
                withdrawal['status'] = 'Accept'
                break
        
        save_json(WITHDRAWAL_DB, withdrawals)
        await query.edit_message_text("درخواست برداشت تأیید شد.")
        
    elif query.data.startswith("reject_withdrawal_"):
        withdrawal_id = int(query.data.split("_")[2])
        withdrawals = load_json(WITHDRAWAL_DB)
        
        for withdrawal in withdrawals:
            if withdrawal['ID'] == withdrawal_id:
                withdrawal['status'] = 'Reject'
                
                # Return balance to user
                users = load_json(USER_DB)
                for user in users:
                    if user['ID-Telegram'] == withdrawal['ID-Telegram']:
                        user['Balance'] += withdrawal['amount']
                        break
                save_json(USER_DB, users)
                break
        
        save_json(WITHDRAWAL_DB, withdrawals)
        await query.edit_message_text("درخواست برداشت رد شد و موجودی به کاربر برگردانده شد.")
        
    elif query.data.startswith("change_balance_"):
        user_id = int(query.data.split("_")[2])
        context.user_data['editing_user_balance'] = user_id
        await query.edit_message_text("موجودی جدید را وارد کنید:")
        
    elif query.data.startswith("change_status_"):
        user_id = int(query.data.split("_")[2])
        keyboard = [
            [InlineKeyboardButton("فعال", callback_data=f"set_status_{user_id}_Active")],
            [InlineKeyboardButton("غیرفعال", callback_data=f"set_status_{user_id}_Inactive")],
            [InlineKeyboardButton("مسدود", callback_data=f"set_status_{user_id}_Blocked")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("وضعیت جدید را انتخاب کنید:", reply_markup=reply_markup)
        
    elif query.data.startswith("set_status_"):
        parts = query.data.split("_")
        user_id = int(parts[2])
        new_status = parts[3]
        
        users = load_json(USER_DB)
        for user in users:
            if user['ID'] == user_id:
                user['Status'] = new_status
                break
        save_json(USER_DB, users)
        
        await query.edit_message_text(f"وضعیت کاربر به {new_status} تغییر یافت.")
        
    elif query.data == "change_win":
        context.user_data['changing_win_rate'] = True
        await query.edit_message_text("درصد برد جدید را وارد کنید (0-100):")
        
    elif query.data == "change_lose":
        context.user_data['changing_lose_rate'] = True
        await query.edit_message_text("درصد باخت جدید را وارد کنید (0-100):")
        
    elif query.data == "toggle_random":
        logic = load_json(LOGIC_DB)
        logic[0]['random'] = not logic[0]['random']
        save_json(LOGIC_DB, logic)
        
        status = "فعال" if logic[0]['random'] else "غیرفعال"
        await query.edit_message_text(f"حالت تصادفی {status} شد.")
        
    elif query.data == "admin_back":
        await admin_start_menu(query)

async def admin_start_menu(query):
    keyboard = [
        [InlineKeyboardButton("مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("تغییر منطق بازی", callback_data="admin_logic")],
        [InlineKeyboardButton("درخواست‌های واریز", callback_data="admin_deposits")],
        [InlineKeyboardButton("درخواست‌های برداشت", callback_data="admin_withdrawals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("پنل ادمین:", reply_markup=reply_markup)

async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    
    text = update.message.text
    
    # Handle balance change
    if context.user_data.get('editing_user_balance') and text.isdigit():
        user_id = context.user_data['editing_user_balance']
        new_balance = int(text)
        
        users = load_json(USER_DB)
        for user in users:
            if user['ID'] == user_id:
                user['Balance'] = new_balance
                break
        save_json(USER_DB, users)
        
        await update.message.reply_text(f"موجودی کاربر به {new_balance} تومان تغییر یافت.")
        del context.user_data['editing_user_balance']
        
    # Handle win rate change
    elif context.user_data.get('changing_win_rate') and text.isdigit():
        win_rate = int(text)
        if 0 <= win_rate <= 100:
            logic = load_json(LOGIC_DB)
            logic[0]['win'] = win_rate
            logic[0]['lose'] = 100 - win_rate
            save_json(LOGIC_DB, logic)
            
            await update.message.reply_text(f"درصد برد به {win_rate}% تغییر یافت.")
        else:
            await update.message.reply_text("لطفا عددی بین 0 تا 100 وارد کنید.")
        
        del context.user_data['changing_win_rate']
        
    # Handle lose rate change
    elif context.user_data.get('changing_lose_rate') and text.isdigit():
        lose_rate = int(text)
        if 0 <= lose_rate <= 100:
            logic = load_json(LOGIC_DB)
            logic[0]['lose'] = lose_rate
            logic[0]['win'] = 100 - lose_rate
            save_json(LOGIC_DB, logic)
            
            await update.message.reply_text(f"درصد باخت به {lose_rate}% تغییر یافت.")
        else:
            await update.message.reply_text("لطفا عددی بین 0 تا 100 وارد کنید.")
        
        del context.user_data['changing_lose_rate']

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("admin", admin_start))
    application.add_handler(CallbackQueryHandler(admin_button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message_handler))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
