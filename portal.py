#portal.py
"""
This module is all about AAU University students who want to know thier grade 
reports faster than normal.
From my experiance of using the AAU Portal, it is bulky to open browser and look for
grade report using a fair network connection. The content can't load faster and
some say the portal gets worse as we get far from the campus i don't buy their
idea though. So i decided to find a way  for a faster and easy GRADE REPORT.
this module  is about creatin a telegram bot that  opens and extacts the relevant 
data from the portal.
This robot will add new feautures evey day.
"""
from mechanize import Browser
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)
from telegram.ext.updater import Updater


def grade(update: Update, context: CallbackContext) -> None:
    """Gets the grade report and profile information of AAU student
    This function first will be invoked anytime the user enters a text message
    The function though will be happy only if it gets text like-
    UGR/1234/12&1234
    """

    userP: str = update.message.text
    userP: str = userP.strip()
    space = ' '
    if space in userP:
        userP = userP.replace(space, '')
    if not len(userP) == 16:
        if len(userP) < 16:
            update.message.reply_text(
                str(16-len(userP)) + ' char/s omitted. Coud you please re-enter?',
                quote=True)
            return
        elif len(userP) > 16:
            update.message.reply_text(
                str(len(userP)-16) +
                ' char/s are mis-included.Coud you please re-enter?',
                quote=True)
            return
    userPass: str = userP.split('&')
    username: str = userPass[0]
    password: str = userPass[1]
    try:
        url: str = 'https://portal.aau.edu.et/Grade/GradeReport'
        browser: Browser = Browser()
        browser.set_handle_redirect(True)
        browser.set_handle_robots(False)
        update.message.reply_text('Please wait...', quote=True)
        browser.open(url)
        browser.select_form(nr=0)
        browser.addheaders: list = [('User-agent', 'Generic user agent')]
        browser["UserName"] = username
        browser["Password"] = password
        loged = browser.submit()
        loged = browser.response().read()
        request = browser.click_link(url="/Grade/GradeReport")
        browser.open(request)
        content = (browser.response().read())
        soup: BeautifulSoup = BeautifulSoup(content, 'html.parser')
    except Exception:
        update.message.reply_text(
            "Loging In failed !!.Caused by incorrect username/password"
        )

    try:
        try:
            arra = [value.text.strip() for value in soup.find_all('td')]
            clean_array = [content.strip()
                           for content in arra if not 'Assessment' in content]
            unwanted_strings = ['1', '2', '3', '4', '5', '6',
                                '7', '9', '2.00', '3.00', '4.00', '5.00']
            clean_list = [
                value for value in clean_array if not value in unwanted_strings]
            for value in clean_list:
                update.message.reply_text(value)
        except Exception:
            update.message.reply_text(
                'Grade report was not found!')
        try:
            request = browser.click_link(url="/Home")
            browser.open(request)
            content = (browser.response().read())
            soup: BeautifulSoup = BeautifulSoup(content, 'html.parser')
            datas: list = [row.text.strip() for row in soup.table]
            free_list: list = [data for data in datas if not data == '']
            arr: list = [string.split('\n') for string in free_list]
            dictionary: dict = {}
            for sub_array in arr:
                dictionary[sub_array[0]] = sub_array[1]
            update.message.reply_text(
                dictionary
            )
        except Exception:
            update.message.reply_text(
                "Report was Not found!"
            )

    except Exception:
        update.message.text('Something went wrong! Please try later.')


def start(update: Update, context: CallbackContext) -> None:
    """Starts the conversation with effective user.
    this function will be invoked everytime user hits /start
    """
    username = update.message.from_user.first_name
    greet = 'Selam, '+username + "!!"

    update.message.reply_text(
        greet + '\nI am AAU Robot! I was made to get your Grade report from THE AAU PORTAL!'
    )
    update.message.reply_text(
        "Now, Send me the USERNAME and PASSWORD as USERNAME&PASSWORD\n \
        Example: UGR/1234/12&8921"
    )


def bad_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Sorry,  '%s' is not a valid command! use /start to restart me!" % update.message.text
    )


def filter_photos(update: Update, context: CallbackContext):
    """Detects photos from user and tells to user that robot can not search
    for photos"""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Photos/Images!", quote=True
    )


def filter_videos(update: Update, context: CallbackContext):
    """Detects videos received from user and tells to user that robot can not search
    for videos"""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Videos", quote=True
    )


def filter_contacts(update: Update, context: CallbackContext):
    """Detects contacts received from user and tells to user that robot can not search
    for contats"""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Contacts or Contacts are useless for me",
        quote=True
    )


def filter_polls(update: Update, context: CallbackContext):
    """Detects polls received from user and tells to user that robot can not search
    for polls"""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need polls or i don't search for them!",
        quote=True
    )


def filter_captions(update: Update, context: CallbackContext):
    """Detects captions received from user and tells to user that robot can not search
    for captions."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need captions for my work or i don't search for them!",
        quote=True
    )


def filter_stickers(update: Update, context: CallbackContext):
    """Detects stickers received from user and tells to user that robot can not search
    for stickers."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Stickers!",
        quote=True
    )


def filter_animations(update: Update, context: CallbackContext):
    """Detects animations received from user and tells to user that robot can not search
    for animations."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for animations!",
        quote=True
    )


def filter_attachments(update: Update, context: CallbackContext):
    """Detects attachiments received from user and tells to user that robot can not search
    for attachments."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for attachments!",
        quote=True
    )


def filter_audios(update: Update, context: CallbackContext):
    """Detects audios received from user and tells to user that robot can not search
    for audios."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Audios!",
        quote=True
    )


def filter_dice(update: Update, context: CallbackContext):
    """Detects dice received from user and tells to user that robot can not search
    for dice."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Dice is beyound my knowlege!",
        quote=True
    )


def filter_documents(update: Update, context: CallbackContext):
    """Detects documents received from user and tells to user that robot can not search
    for doucuments."""

    user = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently I am incapable of searching documents!",
        quote=True
    )


def main() -> None:
    TOKEN: str = 'TOKEN'
    updater = Updater(TOKEN,
                      use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & (~Filters.command), grade))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.contact, filter_contacts))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.video, filter_videos))
    updater.dispatcher.add_handler(MessageHandler(Filters.poll, filter_polls))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.photo, filter_photos))
    updater.dispatcher.add_handler(MessageHandler(Filters.dice, filter_dice))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.document, filter_documents))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.caption, filter_captions))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.sticker, filter_stickers))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.animation, filter_animations))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.attachment, filter_attachments))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.audio, filter_audios))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.command, bad_command))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
