
import logging
import json
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Bot token from environment
BOT_TOKEN = os.environ.get('YOUR_BOT_TOKEN')

# Required channels
REQUIRED_CHANNELS = ["@Topdieshistory", "@Toptasbet"]

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

# Initialize JSON files
def init_json_files():
    files = {
        USER_DB: [],
        GAME_DB: [],
        DEPOSIT_DB: [],
        WITHDRAWAL_DB: [],
        LOGIC_DB: [{"win": 50, "lose": 50, "random": True}],
        WALLET_DB: [{"TRC20": "890qya3ymf8oqkzfgqa9HKDSU89QWFU8", "POL": "werj9yxf78wgo7frgwiarfsjdufgfnxvidb"}]
    }
    
    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_json(USER_DB)
    for user in users:
        if user.get('ID-Telegram') == user_id:
            return user
    return None

def create_user(user_id, username):
    users = load_json(USER_DB)
    new_id = len(users) + 1
    new_user = {
        "ID": new_id,
        "ID-Telegram": user_id,
        "Username": username,
        "Balance": 0,
        "Status": "Active",
        "Description": "New User"
    }
    users.append(new_user)
    save_json(USER_DB, users)
    return new_user

def update_user_balance(user_id, amount):
    users = load_json(USER_DB)
    for user in users:
        if user.get('ID-Telegram') == user_id:
            user['Balance'] += amount
            save_json(USER_DB, users)
            return user['Balance']
    return None

async def check_membership(context, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not await check_membership(context, user.id):
        keyboard = [[InlineKeyboardButton("Join @Topdieshistory", url="https://t.me/Topdieshistory")],
                   [InlineKeyboardButton("Join @Toptasbet", url="https://t.me/Toptasbet")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "برای استفاده از ربات باید عضو کانال‌های زیر باشید:",
            reply_markup=reply_markup
        )
        return

    db_user = get_user(user.id)
    if not db_user:
        db_user = create_user(user.id, user.username or "Unknown")

    keyboard = [
        [InlineKeyboardButton("شروع بازی", callback_data="play")],
        [InlineKeyboardButton("واریز", callback_data="deposit"), 
         InlineKeyboardButton("برداشت", callback_data="withdrawal")],
        [InlineKeyboardButton("رتبه", callback_data="leaderboard"), 
         InlineKeyboardButton("راهنما", callback_data="guide")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"سلام {user.first_name}!\nموجودی شما: {db_user['Balance']} تومان",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_membership(context, user_id):
        keyboard = [[InlineKeyboardButton("Join @Topdieshistory", url="https://t.me/Topdieshistory")],
                   [InlineKeyboardButton("Join @Toptasbet", url="https://t.me/Toptasbet")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "برای استفاده از ربات باید عضو کانال‌های زیر باشید:",
            reply_markup=reply_markup
        )
        return

    if query.data == "play":
        keyboard = [
            [InlineKeyboardButton("2x زوج", callback_data="bet_even"), 
             InlineKeyboardButton("2x فرد", callback_data="bet_odd")],
            [InlineKeyboardButton("1 6x", callback_data="bet_1"), 
             InlineKeyboardButton("2 6x", callback_data="bet_2")],
            [InlineKeyboardButton("3 6x", callback_data="bet_3"), 
             InlineKeyboardButton("4 6x", callback_data="bet_4")],
            [InlineKeyboardButton("5 6x", callback_data="bet_5"), 
             InlineKeyboardButton("6 6x", callback_data="bet_6")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("آپشنت چیه؟؟؟", reply_markup=reply_markup)
        
    elif query.data.startswith("bet_"):
        context.user_data['bet_type'] = query.data.split("_")[1]
        await query.edit_message_text("مبلغ شرط خود را وارد کنید (حداقل 5000 تومان):")
        
    elif query.data == "deposit":
        await query.edit_message_text(
            "چقدر باشه؟؟\nبیشتر از 100,000 هزار تومان باشه :)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", callback_data="back")]])
        )
        context.user_data['awaiting_deposit_amount'] = True
        
    elif query.data == "withdrawal":
        await query.edit_message_text(
            "چقدر باشه؟؟\nبیشتر از 500,000 هزار تومان باشه :)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", callback_data="back")]])
        )
        context.user_data['awaiting_withdrawal_amount'] = True
        
    elif query.data.startswith("deposit_"):
        method = query.data.split("_")[1]
        wallet_data = load_json(WALLET_DB)[0]
        
        if method in ["TRC20", "POL"]:
            address = wallet_data.get(method, "Address not found")
            await query.edit_message_text(
                f"آدرس کیف پول {method}:\n{address}\n\nلطفا اسکرین‌شات، هش تراکنش و لینک تراکنش را ارسال کنید."
            )
        else:  # Utopia
            await query.edit_message_text("لطفا کد فعال‌ساز واچر را ارسال کنید.")
            
        context.user_data['deposit_method'] = method
        context.user_data['awaiting_deposit_info'] = True
        
    elif query.data.startswith("withdrawal_"):
        method = query.data.split("_")[1]
        
        if method in ["TRC20", "POL"]:
            await query.edit_message_text(f"آدرس کیف پول {method} خود را ارسال کنید:")
        else:  # Utopia
            await query.edit_message_text("درخواست شما برای ادمین ارسال شد.")
            
        context.user_data['withdrawal_method'] = method
        context.user_data['awaiting_withdrawal_info'] = True
        
    elif query.data == "leaderboard":
        await query.edit_message_text("رتبه‌بندی بروزرسانی شد!")
        
    elif query.data == "guide":
        await query.edit_message_text("راهنما بروزرسانی شد!")
        
    elif query.data == "support":
        keyboard = [[InlineKeyboardButton("پشتیبانی", url="https://t.me/TopTasSupportBot")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "برای ارتباط با پشتیبانی از آیدی زیر استفاده کنید\n@TopTasSupportBot",
            reply_markup=reply_markup
        )
        
    elif query.data == "back":
        await start_menu(query)

async def start_menu(query):
    keyboard = [
        [InlineKeyboardButton("شروع بازی", callback_data="play")],
        [InlineKeyboardButton("واریز", callback_data="deposit"), 
         InlineKeyboardButton("برداشت", callback_data="withdrawal")],
        [InlineKeyboardButton("رتبه", callback_data="leaderboard"), 
         InlineKeyboardButton("راهنما", callback_data="guide")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("منوی اصلی:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if not await check_membership(context, user_id):
        await update.message.reply_text("لطفا ابتدا عضو کانال‌های مورد نیاز شوید.")
        return
    
    # Handle bet amount
    if 'bet_type' in context.user_data and text.isdigit():
        bet_amount = int(text)
        if bet_amount < 5000:
            await update.message.reply_text("حداقل مبلغ شرط 5000 تومان است.")
            return
            
        user = get_user(user_id)
        if user['Balance'] < bet_amount:
            await update.message.reply_text("موجودی شما کافی نیست.")
            return
            
        # Play game
        dice_result = random.randint(1, 6)
        bet_type = context.user_data['bet_type']
        
        win = False
        multiplier = 1
        
        if bet_type == "even" and dice_result % 2 == 0:
            win = True
            multiplier = 2
        elif bet_type == "odd" and dice_result % 2 == 1:
            win = True
            multiplier = 2
        elif bet_type.isdigit() and int(bet_type) == dice_result:
            win = True
            multiplier = 6
            
        if win:
            profit = bet_amount * multiplier - bet_amount
            update_user_balance(user_id, profit)
            result_text = f"🎉 برنده شدید!\nعدد: {dice_result}\nسود: {profit} تومان"
        else:
            update_user_balance(user_id, -bet_amount)
            result_text = f"😞 باختید!\nعدد: {dice_result}\nضرر: {bet_amount} تومان"
            
        # Save game record
        games = load_json(GAME_DB)
        new_game = {
            "ID": len(games) + 1,
            "ID-Telegram": user_id,
            "Username": update.effective_user.username or "Unknown",
            "bet": bet_amount,
            "status": "win" if win else "lose",
            "date": datetime.now().isoformat(),
            "profit": profit if win else -bet_amount
        }
        games.append(new_game)
        save_json(GAME_DB, games)
        
        await update.message.reply_dice("🎲")
        await update.message.reply_text(result_text)
        
        del context.user_data['bet_type']
        
    # Handle deposit amount
    elif context.user_data.get('awaiting_deposit_amount') and text.isdigit():
        amount = int(text)
        if amount < 100000:
            await update.message.reply_text("حداقل مبلغ واریز 100,000 تومان است.")
            return
            
        keyboard = [
            [InlineKeyboardButton("USDT-POL", callback_data="deposit_POL"),
             InlineKeyboardButton("USDT-TRC20", callback_data="deposit_TRC20")],
            [InlineKeyboardButton("Utopia voucher", callback_data="deposit_Utopia")],
            [InlineKeyboardButton("برگشت", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("روش واریز را انتخاب کنید:", reply_markup=reply_markup)
        
        context.user_data['deposit_amount'] = amount
        del context.user_data['awaiting_deposit_amount']
        
    # Handle withdrawal amount
    elif context.user_data.get('awaiting_withdrawal_amount') and text.isdigit():
        amount = int(text)
        if amount < 500000:
            await update.message.reply_text("حداقل مبلغ برداشت 500,000 تومان است.")
            return
            
        user = get_user(user_id)
        if user['Balance'] < amount:
            await update.message.reply_text("موجودی شما کافی نیست.")
            return
            
        keyboard = [
            [InlineKeyboardButton("USDT-POL", callback_data="withdrawal_POL"),
             InlineKeyboardButton("USDT-TRC20", callback_data="withdrawal_TRC20")],
            [InlineKeyboardButton("Utopia voucher", callback_data="withdrawal_Utopia")],
            [InlineKeyboardButton("برگشت", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("روش برداشت را انتخاب کنید:", reply_markup=reply_markup)
        
        context.user_data['withdrawal_amount'] = amount
        del context.user_data['awaiting_withdrawal_amount']
        
    # Handle deposit info
    elif context.user_data.get('awaiting_deposit_info'):
        deposits = load_json(DEPOSIT_DB)
        new_deposit = {
            "ID": len(deposits) + 1,
            "ID-Telegram": user_id,
            "Username": update.effective_user.username or "Unknown",
            "amount": context.user_data.get('deposit_amount', 0),
            "side": context.user_data.get('deposit_method', ''),
            "information": text,
            "status": "Pending"
        }
        deposits.append(new_deposit)
        save_json(DEPOSIT_DB, deposits)
        
        await update.message.reply_text("درخواست واریز شما ثبت شد و در انتظار بررسی است.")
        
        del context.user_data['awaiting_deposit_info']
        del context.user_data['deposit_amount']
        del context.user_data['deposit_method']
        
    # Handle withdrawal info
    elif context.user_data.get('awaiting_withdrawal_info'):
        withdrawals = load_json(WITHDRAWAL_DB)
        new_withdrawal = {
            "ID": len(withdrawals) + 1,
            "ID-Telegram": user_id,
            "Username": update.effective_user.username or "Unknown",
            "amount": context.user_data.get('withdrawal_amount', 0),
            "side": context.user_data.get('withdrawal_method', ''),
            "wallet-code": text,
            "status": "Pending"
        }
        withdrawals.append(new_withdrawal)
        save_json(WITHDRAWAL_DB, withdrawals)
        
        # Deduct balance
        update_user_balance(user_id, -context.user_data.get('withdrawal_amount', 0))
        
        await update.message.reply_text("درخواست برداشت شما ثبت شد و از موجودی شما کسر گردید.")
        
        del context.user_data['awaiting_withdrawal_info']
        del context.user_data['withdrawal_amount']
        del context.user_data['withdrawal_method']

def main():
    init_json_files()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
