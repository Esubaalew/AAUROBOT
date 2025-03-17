import re
import random
from cryptography.fernet import Fernet
import os
import logging
import asyncio
from decouple import config
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,  # Updated filters
    Application,  # Replaces Updater
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence
)
from bott.database import (
    search_table_by_tg_id,
    insert_data,
    create_table,
    delete_from_table,
    modify_idno)
from datetime import date
from bott.portal import (
    login_to_portal,
    get_profile,
    get_grades)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

persistence = PicklePersistence(filepath='bot_dat')

# Global Application instance
application = Application.builder().token(config('TELEGRAM_BOT_TOKEN')).persistence(persistence).build()


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
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    operation = random.choice(["+", "-", "*", "/"])
    if operation == "+": result = a + b
    elif operation == "-": result = a - b
    elif operation == "*": result = a * b
    elif operation == "/": result = a // b
    return f"What is {a} {operation} {b}?", result



async def math_question(update: Update, context: CallbackContext) -> int:
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

    keyboard = [
        [InlineKeyboardButton(str(answers[0]), callback_data=f"answer_{answers[0]}")],
        [InlineKeyboardButton(str(answers[1]), callback_data=f"answer_{answers[1]}")],
        [InlineKeyboardButton(str(answers[2]), callback_data=f"answer_{answers[2]}")]
    ]
    await update.message.reply_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data['correct_answer'] = correct_answer
    return ACCOUNT_DELETED


async def handle_math_answer(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's answer to a math question.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """

    query = update.callback_query
    await query.answer()
    user_answer = int(query.data.split('_')[1])
    correct_answer = context.user_data.get('correct_answer')

    if user_answer == correct_answer:
        delete_from_table(query.from_user.id)
        await query.edit_message_text("✅ Account deleted successfully!")
        return ConversationHandler.END

    # Generate new question
    question, new_answer = generate_math_question()
    answers = [new_answer, new_answer + 1, new_answer - 1]
    random.shuffle(answers)
    
    keyboard = [
        [InlineKeyboardButton(str(answers[0]), callback_data=f"answer_{answers[0]}")],
        [InlineKeyboardButton(str(answers[1]), callback_data=f"answer_{answers[1]}")],
        [InlineKeyboardButton(str(answers[2]), callback_data=f"answer_{answers[2]}")]
    ]
    await query.edit_message_text(
        text="❌ Incorrect answer. Try again:\n\n" + question,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['correct_answer'] = new_answer
    return ACCOUNT_DELETED



async def ask_for_password(update: Update, context: CallbackContext) -> int:
    """
    Initiates the process of asking the user to enter a password to view the grade report.

    Args:
        update (telegram.Update): The incoming update from Telegram.
        context (telegram.ext.CallbackContext): The context for the conversation.

    Returns:
        int: The next state of the conversation.
    """
    msg = await update.message.reply_text(
        "🔒 Please enter your password to view the grade report:",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['password_msg_id'] = msg.message_id
    return GRADE_REPORT

async def get_password(update: Update, context: CallbackContext) -> int:
    """
    Handles password input and initiates grade report retrieval with pagination.
    For graduates, it congratulates them and skips fetching grades.
    """
    try:
        password = update.message.text
        tg_id = update.message.from_user.id
        registered = search_table_by_tg_id(tg_id)

        if not registered:
            await update.message.reply_text(
                "Viewing grade report is not available for unregistered users.\n/start here",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

        # Existing registration check and data retrieval
        reg_data = search_table_by_tg_id(tg_id)
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = reg_data

        working_on_it_msg = await update.message.reply_text("Working on it...")
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

        # Profile handling
        profile = get_profile(
            campus=decrypt_data(reg_campus, KEY),
            student_id=decrypt_data(reg_id, KEY),
            password=password
        )

        # Check if the user is a graduate
        if profile == "It seems you are a graduate, so I am skipping your profile and showing your grade report below.":
            await update.message.reply_text(
                "🎓 Congratulations! You are a graduate. 🎓\n\n"
                "As a graduate, I can no longer provide your grade report. "
                "This feature is only available for active students.\n\n"
                "Thank you for using AAU Robot! 🎉"
            )
            return ConversationHandler.END  # End the conversation for graduates

        # If the user is not a graduate, proceed with fetching and displaying the profile
        elif isinstance(profile, tuple):
            await context.bot.send_photo(
                update.effective_chat.id,
                photo=profile[0],
                caption=profile[1]
            )

        # Get grades and split into semesters (only for active students)
        grades = get_grades(
            campus=decrypt_data(reg_campus, KEY),
            student_id=decrypt_data(reg_id, KEY),
            password=password
        )

        # Parse semesters and store in context
        semesters = []
        current_semester = []

        for line in grades:
            current_semester.append(line)
            if "Academic Status" in line:
                semesters.append("\n".join(current_semester))
                current_semester = []

        # Add footer to last semester
        if semesters:
            semesters[-1] += "\n\nThis bot was Made by @Esubaalew"

        context.user_data['semesters'] = semesters
        context.user_data['current_page'] = 0

        # Send first semester with pagination
        await send_semester(update, context)
        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Error in get_password: {e}")
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )
        return ConversationHandler.END


async def send_semester(update: Update, context: CallbackContext) -> None:
    """Send a semester with pagination buttons"""
    semesters = context.user_data.get('semesters', [])
    current_page = context.user_data.get('current_page', 0)
    total_pages = len(semesters)

    if not semesters:
        await update.message.reply_text("No grade information available")
        return

    # Create pagination buttons
    buttons = []
    if total_pages > 1:
        if current_page > 0:
            buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data="prev"))
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton("Next ➡️", callback_data="next"))

    # Add footer with page numbers
    footer = f"\n\n📄 Page {current_page + 1} of {total_pages}"
    message_text = semesters[current_page] + footer

    # Edit existing message if possible, else send new
    if 'semester_message_id' in context.user_data:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['semester_message_id'],
                text=message_text,
                reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None
            )
            return
        except Exception as e:
            print(f"Error editing message: {e}")

    msg = await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None
    )
    context.user_data['semester_message_id'] = msg.message_id

async def handle_page_navigation(update: Update, context: CallbackContext) -> None:
    """Handle pagination button presses"""
    query = update.callback_query
    await query.answer()

    current_page = context.user_data.get('current_page', 0)

    if query.data == "prev" and current_page > 0:
        context.user_data['current_page'] -= 1
    elif query.data == "next":
        context.user_data['current_page'] += 1

    await send_semester(update, context)

async def view_profile(update: Update, context: CallbackContext) -> int:
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
        # Fetch user data
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = search_table_by_tg_id(tg_id)

        # Decrypt data
        portal_id = decrypt_data(reg_id, KEY)
        telegram_name = decrypt_data(reg_name, KEY)
        portal_name = decrypt_data(reg_campus, KEY)
        registration_date = decrypt_data(reg_date, KEY)

        # Build profile message with emojis and formatting
        profile_message = (
            "📄 **Your Profile Information**\n\n"
            f"🆔 **Telegram ID**: `{reg_tg_id}`\n"
            f"📋 **Portal ID**: `{portal_id}`\n"
            f"👤 **Telegram Name**: {telegram_name}\n"
            f"🏫 **Campus**: {portal_name}\n"
            f"📅 **Date of Registration**: {registration_date}\n\n"
            "You can use the buttons below to explore more features!"
        )

        # Send profile message
        await update.message.reply_text(
            profile_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                LOGED_BUTTONS,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    else:
        # User is not registered
        unregistered_message = (
            "❌ **Profile Unavailable**\n\n"
            "You are not registered with AAU Robot.\n"
            "To register, use the /start command and follow the instructions.\n\n"
            "If you need help, use /help."
        )
        await update.message.reply_text(
            unregistered_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END


async def start(update: Update, context: CallbackContext) -> int:
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

    # Welcome image URLs
    WELCOME_IMAGE_URL = "https://www.aau.edu.et/_next/image?url=https%3A%2F%2Fvolume.aau.edu.et%2F5%2C065372f0f56e.jpg&w=1920&q=75"
    NEW_USER_IMAGE_URL = "https://www.aau.edu.et/_next/image?url=https%3A%2F%2Fvolume.aau.edu.et%2F6%2C06570a81d169.jpg&w=1920&q=75"

    try:
        # Send chat action (uploading photo)
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO
        )

        if registered:
            # User is registered
            reg_tg_id, reg_id, reg_name, reg_campus, reg_date = registered
            welcome_message = (
                f"👋 Welcome back, {decrypt_data(reg_name, KEY)}!\n\n"
                "Send your password to see your report or click the button of your choice!"
            )

            # Try to send the welcome image with caption
            try:
                await update.message.reply_photo(
                    WELCOME_IMAGE_URL,
                    caption=welcome_message,
                    reply_markup=ReplyKeyboardMarkup(
                        LOGED_BUTTONS,
                        resize_keyboard=True,
                        one_time_keyboard=True,
                        input_field_placeholder='What do you want?'
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send welcome image: {e}")
                # Fallback: Send text message if image fails
                await update.message.reply_text(
                    welcome_message,
                    reply_markup=ReplyKeyboardMarkup(
                        LOGED_BUTTONS,
                        resize_keyboard=True,
                        one_time_keyboard=True,
                        input_field_placeholder='What do you want?'
                    )
                )
            return ConversationHandler.END

        else:
            # New user
            welcome_message = (
                "👋 Welcome to AAU Robot!\n\n"
                "Before you can use the bot, please read /policy and agree to our terms and conditions."
            )
            keyboard = [
                [InlineKeyboardButton("✅ AGREE", callback_data="agree")],
                [InlineKeyboardButton("❌ DISAGREE", callback_data="disagree")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Try to send the new user image with caption
            try:
                await update.message.reply_photo(
                    NEW_USER_IMAGE_URL,
                    caption=welcome_message,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to send new user image: {e}")
                # Fallback: Send text message if image fails
                await update.message.reply_text(
                    welcome_message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            return AGREE

    except Exception as e:
        logger.error(f"Error in start function: {e}")
        # Fallback for critical errors
        await update.message.reply_text(
            "👋 Welcome to AAU Robot!\n\n"
            "Something went wrong. Please try again or contact support."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
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
    # Clear user data to reset the registration process
    context.user_data.clear()

    # Send cancellation message with emojis and clear instructions
    cancellation_message = (
        "❌ **Registration Canceled**\n\n"
        "The registration process has been canceled.\n\n"
        "You can start over by typing /start or use /help for assistance."
    )

    await update.message.reply_text(
        cancellation_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def leave(update: Update, context: CallbackContext) -> int:
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
    # Clear user data to reset the account deletion process
    context.user_data.clear()

    # Send cancellation message with emojis and clear instructions
    cancellation_message = (
        "❌ **Account Deletion Canceled**\n\n"
        "The account deletion process has been canceled.\n\n"
        "You can start over by typing /start or use /help for assistance."
    )

    await update.message.reply_text(
        cancellation_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def registration(update: Update, context: CallbackContext) -> int:
    """Handles the registration process."""
    query = update.callback_query
    await query.answer()

    if query.data == "agree":
        # User agreed to terms
        campus_selection_message = (
            "🏫 **Choose Your Campus**\n\n"
            "Please select your campus from the options below:"
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=campus_selection_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(aait, callback_data=aait)],
                [InlineKeyboardButton(aau, callback_data=aau)],
                [InlineKeyboardButton(eiabc, callback_data=eiabc)]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )

        context.user_data['campus'] = query.data
        return CAMPUS
    elif query.data == "disagree":
        # User disagreed with terms
        disagreement_message = (
            "❌ **Registration Canceled**\n\n"
            "You must agree to the terms and conditions to use this bot.\n\n"
            "If you change your mind, you can start over by typing /start."
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=disagreement_message,
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    else:
        return CAMPUS


async def choose_campus(update: Update, context: CallbackContext) -> int:
    """Handles the selection of a campus during registration."""
    query = update.callback_query
    await query.answer()
    context.user_data['campus'] = query.data

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"🏫 Selected campus: {query.data}\n\n📝 Please enter your student ID in UGR/XXXX/YY format:"
    )

    return STUDENT_ID


async def get_student_id(update: Update, context: CallbackContext) -> int:
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

    try:
        if is_user_id_valid(student_id):
            # Perform registration and database insertion
            insert_data((
                str(tg_id),
                encrypt_data(student_id, KEY),
                encrypt_data(username, KEY),
                encrypt_data(campus, KEY),
                encrypt_data(date_joined, KEY)
            ))

            # Success message with emojis
            success_message = (
                f"✅ Registration successful!\n\n"
                f"👤 Name: {username}\n"
                f"🏫 Campus: {campus}\n"
                f"🆔 Student ID: {student_id}\n\n"
                f"You can now use AAU Robot. Choose an option below to get started!"
            )

            await update.message.reply_text(
                success_message,
                reply_markup=ReplyKeyboardMarkup(
                    LOGED_BUTTONS,
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            return ConversationHandler.END

        else:
            # Invalid student ID format
            error_message = (
                "❌ Invalid student ID format.\n\n"
                "Please use the correct format: `UGR/XXXX/YY`\n\n"
                "For example: `UGR/1234/12`\n\n"
                "If you want to cancel registration, use /cancel."
            )
            await update.message.reply_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=ReplyKeyboardRemove()
            )
            return STUDENT_ID

    except Exception as e:
        logger.error(f"Error in get_student_id: {e}")
        # Fallback for unexpected errors
        await update.message.reply_text(
            "❌ An error occurred during registration. Please try again later or contact support."
        )
        return ConversationHandler.END


async def filter_photos(update: Update, context: CallbackContext) -> None:
    """Detects photos from user and informs them that the bot cannot process photos."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📸 Dear {user}, I currently don't support searching or processing photos. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_videos(update: Update, context: CallbackContext) -> None:
    """Detects videos from user and informs them that the bot cannot process videos."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🎥 Dear {user}, I currently don't support searching or processing videos. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_contacts(update: Update, context: CallbackContext) -> None:
    """Detects contacts from user and informs them that the bot cannot process contacts."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📇 Dear {user}, I currently don't support processing contacts. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_polls(update: Update, context: CallbackContext) -> None:
    """Detects polls from user and informs them that the bot cannot process polls."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📊 Dear {user}, I currently don't support processing polls. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_captions(update: Update, context: CallbackContext) -> None:
    """Detects captions from user and informs them that the bot cannot process captions."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📝 Dear {user}, I currently don't support processing captions. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_stickers(update: Update, context: CallbackContext) -> None:
    """Detects stickers from user and informs them that the bot cannot process stickers."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🖼️ Dear {user}, I currently don't support processing stickers. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_animations(update: Update, context: CallbackContext) -> None:
    """Detects animations from user and informs them that the bot cannot process animations."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🎞️ Dear {user}, I currently don't support processing animations. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_attachments(update: Update, context: CallbackContext) -> None:
    """Detects attachments from user and informs them that the bot cannot process attachments."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📎 Dear {user}, I currently don't support processing attachments. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_audios(update: Update, context: CallbackContext) -> None:
    """Detects audios from user and informs them that the bot cannot process audios."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🎵 Dear {user}, I currently don't support processing audios. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_dice(update: Update, context: CallbackContext) -> None:
    """Detects dice from user and informs them that the bot cannot process dice."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🎲 Dear {user}, I currently don't support processing dice. "
        "Please use text-based commands instead!",
        quote=True
    )


async def filter_documents(update: Update, context: CallbackContext) -> None:
    """Detects documents from user and informs them that the bot cannot process documents."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"📄 Dear {user}, I currently don't support processing documents. "
        "Please use text-based commands instead!",
        quote=True
    )


async def policy(update: Update, context: CallbackContext) -> None:
    """Informs the user about how the bot handles user data."""
    user: str = update.message.from_user.first_name
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        f"🔒 **Privacy Policy**\n\n"
        f"Hello {user},\n\n"
        "At AAU Robot, we take your privacy seriously. Here's how we handle your data:\n\n"
        "1. **No Data Storage**: We do not store your student ID, password, or any personal information.\n"
        "2. **Secure Communication**: All data is transmitted securely using encryption.\n"
        "3. **Transparency**: You can review our full privacy policy here: "
        "https://aau-robot.esubalew.et/\n\n"
        "If you have any concerns, feel free to reach out to the bot developer.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN
    )


async def about(update: Update, context: CallbackContext) -> None:
    """Provides information about the bot."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        "🤖 **About AAU Robot**\n\n"
        "AAU Robot is designed to help students at Addis Ababa University access their "
        "academic information quickly and securely.\n\n"
        "For more details, visit: https://aau-robot.esubalew.et/",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN
    )
    return


async def help(update: Update, context: CallbackContext) -> None:
    """Provides help information to the user."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    await update.message.reply_text(
        "🆘 **Help**\n\n"
        "Here are some commands you can use:\n\n"
        "- /start: Start the bot and register.\n"
        "- /help: Get help and instructions.\n"
        "- /policy: Learn about our privacy policy.\n"
        "- /about: Learn more about AAU Robot.\n\n"
        "For detailed instructions, visit: https://aau-robot.esubalew.et/",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN
    )
    return



async def bot_tele(text):
    # Create application
    application = (
        Application.builder().token(config('TELEGRAM_BOT_TOKEN')).persistence(persistence).build()
    )

    

    
    # Register handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGREE: [CallbackQueryHandler(registration, pattern="^(agree|disagree)$")],
            CAMPUS: [CallbackQueryHandler(choose_campus, pattern="^(AAIT|AAU|EIABC)$")],
            STUDENT_ID: [MessageHandler(filters.TEXT, get_student_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        persistent=True,
        name="registration",
    )
    application.add_handler(conv_handler)

    conv_handler_grade_report = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Grade Report$"), ask_for_password)],
        states={
            GRADE_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        persistent=True,
        name="grade_report",
    )
    application.add_handler(conv_handler_grade_report)

    conv_handler_account_deletion = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Delete Account$"), math_question)],
        states={
            ACCOUNT_DELETED: [CallbackQueryHandler(handle_math_answer, pattern="^answer_")],
            ACCOUNT_NOT_DELETED: [MessageHandler(filters.ALL, lambda update, context: ConversationHandler.END)],
        },
        fallbacks=[CommandHandler('leave', cancel)],
        persistent=True,
        name="account_deletion",
    )
    application.add_handler(conv_handler_account_deletion)

    application.add_handler(CallbackQueryHandler(handle_page_navigation, pattern="^(prev|next)$"))
    application.add_handler(MessageHandler(filters.Regex("^View Profile$"), view_profile))
    application.add_handler(CommandHandler('policy', policy))
    application.add_handler(CommandHandler('about', about))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(MessageHandler(filters.PHOTO, filter_photos))
    application.add_handler(MessageHandler(filters.VIDEO, filter_videos))
    application.add_handler(MessageHandler(filters.CONTACT, filter_contacts))
    application.add_handler(MessageHandler(filters.POLL, filter_polls))
    application.add_handler(MessageHandler(filters.CAPTION, filter_captions))
    application.add_handler(MessageHandler(filters.Sticker.ALL, filter_stickers))
    application.add_handler(MessageHandler(filters.ANIMATION, filter_animations))
    application.add_handler(MessageHandler(filters.Document.ALL, filter_documents))
    application.add_handler(MessageHandler(filters.AUDIO, filter_audios))
    application.add_handler(MessageHandler(filters.Dice.ALL, filter_dice))
    application.add_handler(MessageHandler(filters.ATTACHMENT, filter_attachments))


    
    await application.run.polling()
