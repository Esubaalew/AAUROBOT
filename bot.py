import re
import random
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardRemove,
    ChatAction
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    Updater,
    CallbackQueryHandler,
    ConversationHandler
)
from database import search_table_by_tg_id, insert_data, create_table, delete_from_table
from datetime import date
from portal import login_to_portal, get_profile, get_grades

aait = 'AAIT'
aau = 'AAU'
eiabc = 'EIABC'


loged_buttons = [
    [KeyboardButton("Grade Report")],
    [KeyboardButton("View Profile")],
    [KeyboardButton("Privacy Policy"), KeyboardButton("Delete Account")],
    [KeyboardButton("Help"), KeyboardButton("About This Bot")],
    [KeyboardButton("Statistics")]
]
logged_in_inline_buttons = [
    [InlineKeyboardButton("View Profile", callback_data="view_profile")],
    [InlineKeyboardButton("View Grade Report",
                          callback_data="view_grade_report")],
    [InlineKeyboardButton("Delete Account", callback_data="delete_account")]
]

AGREE, DISAGREE, CAMPUS, STUDENT_ID = range(4)
GRADE_REPORT = range(4, 8)

CONFIRM_DELETE = range(8)

# Handler to initiate the account deletion process
def delete_account(update: Update, context: CallbackContext) -> int:
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)

    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(tg_id)

        # Generate a random math question and answer options
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operator = random.choice(["+", "-", "*", "/"])
        correct_answer = eval(f"{num1}{operator}{num2}")
        
        # Create three possible answer options with one correct answer
        answer_options = [correct_answer]
        while len(answer_options) < 3:
            random_answer = random.randint(1, 100)
            if random_answer not in answer_options:
                answer_options.append(random_answer)

        random.shuffle(answer_options)
        options = [str(option) for option in answer_options]

        # Create an inline keyboard with answer options
        keyboard = [[InlineKeyboardButton(option, callback_data=option) for option in options]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Ask the math question
        question = f"What is {num1} {operator} {num2}?"
        update.message.reply_text(question, reply_markup=reply_markup)

        # Store the correct answer in user_data for later comparison
        context.user_data['correct_answer'] = correct_answer
        return CONFIRM_DELETE
    else:
        update.message.reply_text(
            "Deleting account is not available for unregistered users. Register using /start first.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

# Handler to confirm the account deletion
def confirm_delete(update: Update, context: CallbackContext) -> int:
    user_answer = int(update.callback_query.data)
    correct_answer = context.user_data['correct_answer']

    if user_answer == correct_answer:
        tg_id = update.callback_query.message.chat_id
        delete_from_table(tg_id)
        update.callback_query.answer("Account deleted successfully.")
    else:
        update.callback_query.answer("Incorrect answer. Please try again later.")
    
    return ConversationHandler.END  # End the conversation

def is_user_id_valid(user_id):
    user_id = user_id.upper()

    pattern = r'^[A-Z]{3}/\d{4}/\d{2}$'

    if re.match(pattern, user_id):
        return True
    else:
        return False


def ask_for_password(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Please enter your password to view the grade report:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GRADE_REPORT


def get_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)

    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)

        # Send a "Working on it" message

        working_on_it_msg = update.message.reply_text("Working on it...")
        update.message.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Perform the actual processing in the background
        profile = get_profile(
            campus=reg_campus, student_id=reg_id, password=password)
        grades = get_grades(campus=reg_campus,
                            student_id=reg_id, password=password)

        if isinstance(profile, tuple):
            # Send the photo
            update.message.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=profile[0],
                caption=profile[1]
            )
            grades_length: int = len(grades)
            count: int = 0
            result: str = ''
            for string in grades:
                count = count + 1
                if count == grades_length:
                    string: str = string + '\n\n  This bot was Made by @Esubaalew'
                result += string + "\n"
                if "Academic Year" in string:
                    result += """\n

   __________________________________________\n\n"""
                if "Academic Status" in string:
                    update.message.reply_text(result)
                    result = ''
        else:
            # Edit the "Working on it" message with the error message
            update.message.bot.edit_message_text(
                text=profile,
                chat_id=update.effective_chat.id,
                message_id=working_on_it_msg.message_id
            )
    else:
        update.message.reply_text(
            "Viewing grade report is not available for unregistered users.",
            reply_markup=ReplyKeyboardRemove())

    # Return to the main state
    reply_markup = ReplyKeyboardMarkup(
        loged_buttons, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "Please choose an option:", reply_markup=reply_markup)
    return ConversationHandler.END


def view_profile(update: Update, context: CallbackContext) -> int:
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)

    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)
        data = [
            [1, "Telegram ID", reg_tg_id],
            [2, "Portal ID", reg_id],
            [3, "Telegram Name", reg_name],
            [4, "Portal Name", reg_campus]
        ]

        # Create a formatted message with the user's profile information
        message = "Your Profile Information:\n"
        for item in data:
            message += f"{item[1]}: {item[2]}\n"

        update.message.reply_text(message)
    else:
        update.message.reply_text(
            "Viewing profile is not available for unregistered users. Please Register using /start.",
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END  # End the conversation


def start(update: Update, context: CallbackContext) -> int:
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)
    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)
        update.message.reply_text(
            "Welcome back %s!!\nSend your password to see your report or click the button of your choice!" % reg_name,
            reply_markup=ReplyKeyboardMarkup(
                loged_buttons,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder='What do you want?'
            )
        )
        return ConversationHandler.END
    else:
        message = '''Welcome to AAU Robot! Before you can use the bot, please read and agree to our terms and conditions.
        '''
        keyboard = [[InlineKeyboardButton("AGREE", callback_data="agree")],
                    [InlineKeyboardButton("DISAGREE", callback_data="disagree")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return AGREE


def registration(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    if query.data == "agree":
        message = '''Before you can use AAU Robot, please choose your campus.
        '''
        keyboard = [
            [InlineKeyboardButton(aait, callback_data=aait),
             InlineKeyboardButton(aau, callback_data=aau),
             InlineKeyboardButton(eiabc, callback_data=eiabc)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(
            message,
            chat_id=chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return CAMPUS
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, you must agree to the terms to use AAU Robot. Registration cannot proceed without agreement."
        )
        return ConversationHandler.END


def choose_campus(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    context.user_data['campus'] = query.data
    message = '''Please enter your student ID.
    '''
    context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=ReplyKeyboardRemove()
    )
    return STUDENT_ID


def get_student_id(update: Update, context: CallbackContext) -> int:
    student_id = update.message.text
    context.user_data['student_id'] = student_id
    tg_id = update.message.from_user.id
    username = update.message.from_user.first_name
    campus = context.user_data['campus']
    date_joined = date.today().strftime("%d/%m/%Y")

    if is_user_id_valid(student_id):
        # Perform registration and database insertion here
        insert_data((str(tg_id), student_id, username, campus, date_joined))
        message = f"Registration successful for {username} at {campus} with student ID {student_id}. You can now use AAU Robot."
        update.message.reply_text(message)

        # Show loged_buttons keyboard
        reply_markup = ReplyKeyboardMarkup(
            loged_buttons, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Please choose an option:", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        message = "Invalid student ID format. Please use the format: UGR/XXXX/YY"
        update.message.reply_text(message)
        return STUDENT_ID


def main() -> None:
    create_table()
    TOKEN = '6896362614:AAHoIIltg_jK5BUzU6Q_E40JsSd1ZmQMM2c'
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGREE: [CallbackQueryHandler(registration, pattern="^(agree|disagree)$")],
            CAMPUS: [CallbackQueryHandler(choose_campus, pattern="^(AAIT|AAU|EIABC)$")],
            STUDENT_ID: [MessageHandler(Filters.text & ~Filters.command, get_student_id)],
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)
    conv_handler_grade_report = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(
            "^Grade Report$"), ask_for_password)],
        states={
            GRADE_REPORT: [MessageHandler(Filters.text & ~Filters.command, get_password)],
        },
        fallbacks=[]
    )
    # conv_handler_delete_account = ConversationHandler(
    #     entry_points=[MessageHandler(Filters.regex(
    #         "^Delete Account$"), delete_account)],
    #     states={
    #         CONFIRM_DELETE: [MessageHandler(Filters.text & ~Filters.command, confirm_delete)],
    #     },
    #     fallbacks=[]
    # )
    # dp.add_handler(conv_handler_delete_account)
    dp.add_handler(conv_handler_grade_report)
    dp.add_handler(MessageHandler(
        Filters.regex("^View Profile$"), view_profile))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
