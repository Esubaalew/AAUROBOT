import re
import random
import math
import requests
from cryptography.fernet import Fernet
from decouple import config
from bs4 import BeautifulSoup
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
from database import (
    search_table_by_tg_id,
    insert_data,
    create_table,
    delete_from_table,
    modify_idno)
from datetime import date
from portal import (
    login_to_portal,
    get_profile,
    get_grades)

aait = 'AAIT'
aau = 'AAU'
eiabc = 'EIABC'

KEY = config('SECRET_KEY').encode()

LOGED_BUTTONS: list = [
    [KeyboardButton("Grade Report")],
    [KeyboardButton("View Profile")],
    [KeyboardButton("Delete Account")],

]
AGREE, DISAGREE, CAMPUS, STUDENT_ID = range(4)
GRADE_REPORT = range(4, 8)
MATH_QUESTION, ACCOUNT_DELETED, ACCOUNT_NOT_DELETED = range(8, 11)


def encrypt_data(data: str, key: bytes) -> bytes:
    """
    Encrypts the input data using Fernet symmetric encryption.

    Args:
        data (str): The data to be encrypted as a string.
        key (bytes): The encryption key as bytes.

    Returns:
        bytes: The encrypted data as bytes.
    """
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data


def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """
    Decrypts the encrypted data using the Fernet symmetric encryption key.

    Args:
        encrypted_data (bytes): The data to be decrypted as bytes.
        key (bytes): The encryption key as bytes.

    Returns:
        str: The decrypted data as a string.
    """
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data


def is_user_id_valid(user_id: str) -> bool:
    """
    Checks if a user ID is valid based on a specific pattern.

    Args:
        user_id (str): The user ID to be validated.

    Returns:
        bool: True if the user ID is valid, False otherwise.
    """
    user_id: str = user_id.upper()
    pattern: str = r'^[A-Z]{3}/\d{4}/\d{2}'
    if re.match(pattern, user_id):
        return True
    else:
        return False


def generate_math_question() -> tuple:
    """
    Generates a random math question with two random numbers and an arithmetic operation.

    Returns:
        tuple: A tuple containing the math question (str) and the correct answer (int).
    """
    a: int = random.randint(1, 10)
    b: int = random.randint(1, 10)
    operation: str = random.choice(["+", "-", "*", "/"])
    if operation == "+":
        result: int = a + b
    elif operation == "-":
        result: int = a - b
    elif operation == "*":
        result: int = a * b
    elif operation == "/":
        result: int = a // b  # Integer division for simplicity
    question: str = f"What is {a} {operation} {b}?"
    return question, result


def math_question(update: Update, context: CallbackContext) -> int:
    """
    Generates a math question and sends it to the user with answer options.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    question, correct_answer = generate_math_question()
    answers = [correct_answer, correct_answer + 1, correct_answer - 1]
    random.shuffle(answers)
    keyboard = [[InlineKeyboardButton(str(answers[0]), callback_data="answer_" + str(answers[0])),
                InlineKeyboardButton(
                    str(answers[1]), callback_data="answer_" + str(answers[1])),
                InlineKeyboardButton(str(answers[2]), callback_data="answer_" + str(answers[2]))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(question, reply_markup=reply_markup)
    context.user_data['correct_answer'] = correct_answer

    return ACCOUNT_DELETED


def handle_math_answer(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's answer to a math question.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    user_answer = int(update.callback_query.data.split('_')[1])
    correct_answer = context.user_data.get('correct_answer')

    if user_answer == correct_answer:
        tg_id = update.callback_query.from_user.id
        delete_from_table(tg_id)
        update.callback_query.answer("Account deleted successfully!")
        update.callback_query.message.reply_text(
            "Your account has been deleted.", reply_markup=ReplyKeyboardRemove())
        return ACCOUNT_DELETED
    else:
        update.callback_query.answer("Incorrect answer. Please try again. or /leave")

        # Generate a new math question and send it to the user
        question, correct_answer = generate_math_question()
        answers = [correct_answer, correct_answer + 1, correct_answer - 1]
        random.shuffle(answers)
        keyboard = [[InlineKeyboardButton(str(answers[0]), callback_data="answer_" + str(answers[0])),
                    InlineKeyboardButton(
                        str(answers[1]), callback_data="answer_" + str(answers[1])),
                    InlineKeyboardButton(str(answers[2]), callback_data="answer_" + str(answers[2]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(
            question, reply_markup=reply_markup)
        context.user_data['correct_answer'] = correct_answer

        return ACCOUNT_DELETED


def ask_for_password(update: Update, context: CallbackContext) -> int:
    """
    Initiates the process of asking the user to enter a password to view the grade report.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    update.message.reply_text(
        "Please enter your password to view the grade report:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GRADE_REPORT


def get_password(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's input of a password and initiates the process of retrieving and displaying the grade report.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    password = update.message.text
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)
    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)

        working_on_it_msg = update.message.reply_text("Working on it...")
        update.message.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        profile = get_profile(
            campus=decrypt_data(reg_campus, KEY),
            student_id=decrypt_data(reg_id, KEY),
            password=password
        )
        grades = get_grades(campus=decrypt_data(reg_campus, KEY),
                            student_id=decrypt_data(reg_id, KEY),
                            password=password
                            )

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
            reply_markup = ReplyKeyboardMarkup(
                LOGED_BUTTONS,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder='What do you want?')
            update.message.reply_text(
                "Please choose an option:", reply_markup=reply_markup)

            return ConversationHandler.END
        else:
            # Edit the "Working on it" message with the error message
            update.message.bot.edit_message_text(
                text=profile,
                chat_id=update.effective_chat.id,
                message_id=working_on_it_msg.message_id,
            )
    else:
        update.message.reply_text(
            "Viewing grade report is not available for unregistered users.\n /start here",
            reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def view_profile(update: Update, context: CallbackContext) -> int:
    """
    Displays the user's profile information.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)

    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)
        data = [
            [1, "Telegram ID", reg_tg_id],
            [2, "Portal ID", decrypt_data(reg_id, KEY)],
            [3, "Telegram Name", decrypt_data(reg_name, KEY)],
            [4, "Portal Name", decrypt_data(reg_campus, KEY)],
            [5, "Date of Registartion", decrypt_data(reg_date, KEY)],

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

    return ConversationHandler.END


def start(update: Update, context: CallbackContext) -> int:
    """
    Handles the start of the conversation and user registration.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    tg_id = update.message.from_user.id
    registered = search_table_by_tg_id(tg_id)
    if registered:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(
            tg_id)
        update.message.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        update.message.reply_photo(
            "http://www.aau.edu.et/wp-content/uploads/2017/06/wallnew2.png",
            caption="Welcome back %s!!\nSend your password to see your report or click the button of your choice!" % decrypt_data(
                reg_name, KEY),
            reply_markup=ReplyKeyboardMarkup(
                LOGED_BUTTONS,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder='What do you want?'
            )
        )
        return ConversationHandler.END
    else:
        message = '''Welcome to AAU Robot!\n Before you can use the bot, please read /policy and agree to our terms and conditions.
        '''
        keyboard = [[InlineKeyboardButton("AGREE", callback_data="agree")],
                    [InlineKeyboardButton("DISAGREE", callback_data="disagree")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        update.message.reply_photo(
            "http://www.aau.edu.et/wp-content/uploads/2017/06/wallnew2.png")
        update.message.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return AGREE


def cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancel the registration process and reset the conversation.

    This function handles the '/cancel' command, which allows the user to cancel
    the ongoing registration process and reset the conversation to its initial state.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The final state of the conversation, which is ConversationHandler.END.
    """
    user = update.message.from_user
    context.user_data.clear()  # Clear user data to reset the registration process
    update.message.reply_text(
        "Registration process has been canceled. You can start over by typing /start.")
    return ConversationHandler.END

def leave(update: Update, context: CallbackContext) -> int:
    """
    Cancel the account deletion process and reset the conversation.

    This function handles the '/leave' command, which allows the user to cancel
    the ongoing account deletion process and reset the conversation to its initial state.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The final state of the conversation, which is ConversationHandler.END.
    """
    user = update.message.from_user
    context.user_data.clear()  # Clear user data to reset the registration process
    update.message.reply_text(
        "Registration process has been canceled. You can start over by typing /start.")
    return ConversationHandler.END


def registration(update: Update, context: CallbackContext) -> int:
    """
    Handles the registration process, prompting the user to agree to terms and choose a campus.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
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
    """
    Handles the selection of a campus during registration.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
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
    """
    Handles the user input of their student ID during registration.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    student_id = update.message.text
    context.user_data['student_id'] = student_id
    tg_id = update.message.from_user.id
    username = update.message.from_user.first_name
    campus = context.user_data['campus']
    date_joined = date.today().strftime("%d/%m/%Y")

    if is_user_id_valid(student_id):
        # Perform registration and database insertion here
        insert_data((str(tg_id),
                     encrypt_data(student_id, KEY),
                     encrypt_data(username, KEY),
                     encrypt_data(campus, KEY),
                     encrypt_data(date_joined, KEY)))
        message = f"Registration successful for {username} at {campus} with student ID {student_id}. You can now use AAU Robot."
        update.message.reply_text(message)

        # Show loged_buttons keyboard
        reply_markup = ReplyKeyboardMarkup(
            LOGED_BUTTONS,
            resize_keyboard=True,
            one_time_keyboard=True)
        update.message.reply_text(
            "Please choose an option:", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        message = "Invalid student ID format. Please use the format: UGR/XXXX/YY or /cancel to stop registration."
        update.message.reply_text(message)
        return STUDENT_ID


def filter_photos(update: Update, context: CallbackContext) -> None:
    """Detects photos from user and tells to user that robot can not search
    for photos"""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Photos/Images!",
        quote=True
    )


def filter_videos(update: Update, context: CallbackContext) -> None:
    """Detects videos received from user and tells to user that robot can not search
    for videos"""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Videos",
        quote=True
    )


def filter_contacts(update: Update, context: CallbackContext) -> None:
    """Detects contacts received from user and tells to user that robot can not search
    for contats"""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Contacts or Contacts are useless for me",
        quote=True
    )


def filter_polls(update: Update, context: CallbackContext) -> None:
    """Detects polls received from user and tells to user that robot can not search
    for polls"""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need polls or i don't search for them!",
        quote=True
    )


def filter_captions(update: Update, context: CallbackContext) -> None:
    """Detects captions received from user and tells to user that robot can not search
    for captions."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need captions for my work or i don't search for them!",
        quote=True
    )


def filter_stickers(update: Update, context: CallbackContext) -> None:
    """Detects stickers received from user and tells to user that robot can not search
    for stickers."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Stickers!",
        quote=True
    )


def filter_animations(update: Update, context: CallbackContext) -> None:
    """Detects animations received from user and tells to user that robot can not search
    for animations."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for animations!",
        quote=True
    )


def filter_attachments(update: Update, context: CallbackContext) -> None:
    """Detects attachiments received from user and tells to user that robot can not search
    for attachments."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for attachments!",
        quote=True
    )


def filter_audios(update: Update, context: CallbackContext) -> None:
    """Detects audios received from user and tells to user that robot can not search
    for audios."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Audios!",
        quote=True
    )


def filter_dice(update: Update, context: CallbackContext) -> None:
    """Detects dice received from user and tells to user that robot can not search
    for dice."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Dice is beyound my knowlege!",
        quote=True
    )


def filter_documents(update: Update, context: CallbackContext) -> None:
    """Detects documents received from user and tells to user that the robot can not search
    for documents."""

    user: str = update.message.from_user.first_name
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        f"Dear {user}, Currently I am incapable of searching documents!",
        quote=True
    )


def policy(update: Update, context: CallbackContext) -> None:
    """Tells user a message about how the bot handels user data"""

    user: str = update.message.from_user.first_name
    url = 'http://www.aau.edu.et/wp-content/uploads/2017/06/wallnew2.png'
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.UPLOAD_PHOTO)
    update.message.reply_photo(
        url,
        f"""Hello dear {user}, 
As the age is technological, most of us are the users of the technology. 
It is clear that as technology becomes more sophisticated, so does theft and fraud.
However, @AAU_Robot aims to send student information the moment the student ID 
and password are sent to it, and cannot remember and/or store any information.
Therefore, we remind you that anyone can freely send his/her ID and password and view Grade Report.
If you want to be sure that @AAU_Robot doesn't store your data, you can ask for the source code
from BOT DEVELOPER.""",
        reply_markup=ReplyKeyboardRemove()
    )


def about(update: Update, context: CallbackContext):
    '''Shows some message from bit writter'''
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        "Please read about the bot here https://telegra.ph/About-AAU-ROBOT-12-03",
        reply_markup=ReplyKeyboardRemove())
    return


def help(update: Update, context: CallbackContext):
    """Show the some help the uset may refer to"""
    update.message.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(
        "You can read help article here https://telegra.ph/HELP-for-AAU-Robot-12-03 ",
        reply_markup=ReplyKeyboardRemove())
    return


def main() -> None:
    """
    Entry point to the program. 

    """
    create_table()
    TOKEN = config('TELEGRAM_BOT_TOKEN')
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGREE: [CallbackQueryHandler(registration, pattern="^(agree|disagree)$")],
            CAMPUS: [CallbackQueryHandler(choose_campus, pattern="^(AAIT|AAU|EIABC)$")],
            STUDENT_ID: [MessageHandler(Filters.text & ~Filters.command, get_student_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
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
    conv_handler_account_deletion = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(
            "^Delete Account$"), math_question)],
        states={
            ACCOUNT_DELETED: [CallbackQueryHandler(handle_math_answer, pattern="^answer_")],
            ACCOUNT_NOT_DELETED: [MessageHandler(Filters.all, lambda update, context: ConversationHandler.END)],
        },
        fallbacks=[
            CommandHandler('leave', cancel)  # /cancel as a fallback
        ]
    )

    dp.add_handler(conv_handler_account_deletion)
    dp.add_handler(conv_handler_grade_report)
    dp.add_handler(MessageHandler(
        Filters.regex("^View Profile$"), view_profile))
    dp.add_handler(CommandHandler('policy', policy))
    dp.add_handler(CommandHandler('about', about))
    dp.add_handler(CommandHandler('help', help))

    dp.add_handler(MessageHandler(Filters.photo, filter_photos))
    dp.add_handler(MessageHandler(Filters.video, filter_videos))
    dp.add_handler(MessageHandler(Filters.contact, filter_contacts))
    dp.add_handler(MessageHandler(Filters.poll, filter_polls))
    dp.add_handler(MessageHandler(Filters.caption, filter_captions))
    dp.add_handler(MessageHandler(Filters.sticker, filter_stickers))
    dp.add_handler(MessageHandler(Filters.animation, filter_animations))
    dp.add_handler(MessageHandler(Filters.document, filter_documents))
    dp.add_handler(MessageHandler(Filters.audio, filter_audios))
    dp.add_handler(MessageHandler(Filters.dice, filter_dice))
    dp.add_handler(MessageHandler(Filters.attachment, filter_attachments))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
