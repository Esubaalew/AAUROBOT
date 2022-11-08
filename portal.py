# portal.py
"""
This code  is aimed at designing a telegram bot(@AAU_Robot) for getting Grade reports 
and Profile informations for AAU students in a more faster way.
This bot cosidered many mistakes students may make: like unwanted space, omitted / or &
and shorter or longer username&password. Considering these common mistakes the bot will
not try to log in with these input to avoid account lock. 
This code wasn't able to perform what it is now performing with out the presence of:
1. Mechanize: for sign in and returning the response object of the website.
2. BeautifulSoup4: for extracting the important datas from the html response.
3. Python-telegram-bot(PTB): for communicating with telegram servers.
You have no idea how much time PTB saved for me.
"""
from mechanize import Browser
from bs4 import (
    BeautifulSoup,
    Tag
)
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater
)


def grade(update: Update, context: CallbackContext) -> None:
    """
    This function is the main part of @AAU_Robot.
    It gets the grade report and profile information of AAU student. This function 
    will be invoked anytime the user sends a text message.
    The function though will be happy only if it gets text like-
    UGR/1234/12&1234.
     Note:
    The bot will understand the above input as:

    ID No: UGR/1234/12
    Password: 1234

     Easy problems:
    If user send shorter or longer ID&password combination than needed, or if user 

     Hard Problems:
    The login request may fail due to many resons. If the ID No is correct and
    the password is wrong, the user will be  warned four times and the account will get
    locked after four wrong  attempts totaly with 5 worng inputs.
    If the username is wrong(not found, expired), user will get 'Incorrect username or password.' 
    warning message.
    And more badly if the website stop working, the login failed message will arrive.

    "Your Grade Report was not found!" message may also arrive if the grade report field is
    empty.(May be this is on the first year first semester)



    """

    userP: str = update.message.text
    userP = userP.strip()
    space: str = ' '
    if space in userP:
        userP = userP.replace(space, '')
    if not len(userP) == 16:
        if len(userP) < 16:
            update.message.reply_text(
                str(16-len(userP)) +
                ' char(s) omitted. Coud you please re-enter?',
                quote=True)
            return
        elif len(userP) > 16:
            update.message.reply_text(
                str(len(userP)-16) +
                ' char(s) are mis-included.Coud you please re-enter?',
                quote=True)
            return
    if not '&' in userP:
        update.message.reply_text(
            '& is a must. re- enter with &. Example: UGR/1234/12&8921',
            quote=True
        )
        return
    else:
        pass
    if not '/' in userP:
        update.message.reply_text(
            '/ character is omitted. A student username is like UGR/1234/12.\
                re-enter.',
            quote=True
        )
        return
    else:
        pass
    if not userP[3] == '/':
        update.message.reply_text(
            '/ is not in its legal position. Please re-enter..',
            quote=True
        )
        return
    else:
        pass
    if not userP[8] == '/':
        update.message.reply_text(
            '/ is not in its legal position. Please re-enter..',
            quote=True
        )
        return
    else:
        pass
    if not userP[11] == '&':
        update.message.reply_text(
            '& is not in its legal position. Please Re-enter..',
            quote=True
        )
        return
    else:
        pass

    userPass: str = userP.split('&')
    username: str = userPass[0]
    password: str = userPass[1]
    try:
        url: str = 'https://portal.aau.edu.et/Grade/GradeReport'
        browser: Browser = Browser()
        browser.set_handle_redirect(True)
        browser.set_handle_robots(False)
        update.message.reply_text(
            'I am working on it. Please wait...',
            quote=True)
        browser.open(url)
        browser.select_form(nr=0)
        browser.addheaders: list = [('User-agent', 'Mozilla/104.0.2')]
        browser["UserName"] = username
        browser["Password"] = password
        loged = browser.submit()
        loged = browser.response().read()
        soup: BeautifulSoup = BeautifulSoup(loged, 'html.parser')
        if 'Incorrect username or password.' in soup.text:
            update.message.reply_text(
                'Incorrect username or password.',
                quote=True
            )
            return
        elif 'Invalid credentials. You have 4 more attempt(s) before your account gets locked out.' in soup.text:
            update.message.reply_text(
                'Invalid credentials. You have 4 more attempt(s) before your account gets locked out.',
                quote=True
            )
            return
        elif 'Invalid credentials. You have 3 more attempt(s) before your account gets locked out.' in soup.text:
            update.message.reply_text(
                'Invalid credentials. You have 3 more attempt(s) before your account gets locked out.',
                quote=True
            )
            return
        elif 'Invalid credentials. You have 2 more attempt(s) before your account gets locked out.' in soup.text:
            update.message.reply_text(
                'Invalid credentials. You have 2 more attempt(s) before your account gets locked out.',
                quote=True
            )
            return
        elif 'Invalid credentials. You have 1 more attempt(s) before your account gets locked out.' in soup.text:
            update.message.reply_text(
                'Invalid credentials. You have 1 more attempt(s) before your account gets locked out.',
                quote=True
            )
            return
        elif 'Your account has been locked out for 15 minutes due to multiple failed login attempts.' in soup.text:
            update.message.reply_text(
                'Your account has been locked out for 15 minutes due to multiple failed login attempts.',
                quote=True
            )
            return
        elif 'Your account has been locked out due to multiple failed login attempts.' in soup.text:
            update.message.reply_text(
                'Your account has been locked out due to multiple failed login attempts.',
                quote=True
            )
            return
        else:
            pass

    except Exception:
        update.message.reply_text('''
        Login Failed!
        This is most probably because:
        The website was crashed!
        ''')
        return
    try:
        try:
            soup = BeautifulSoup(loged, 'html.parser')
            datas: list = [row.text.strip() for row in soup.table]
            free_list: list = [data for data in datas if not data == '']
            arr: list = [string.split('\n') for string in free_list]
            dictionary: dict = {}
            for sub_array in arr:
                dictionary[sub_array[0]] = sub_array[1]
            image: Tag = soup.find('img', {'class': 'img-rounded'})
            image: str = image['src']
            pre_text: str = 'https://portal.aau.edu.et/'
            image: str = pre_text+image

            user_name: str = dictionary['Full Name ']
            user_id: str = dictionary['ID No. ']
            department: str = dictionary['Department ']
            year: str = dictionary["Year "]
            update.message.reply_text(f"{user_name}'s Profile 👇")
            update.message.reply_photo(
                image,
                'Full Name : '+user_name+'\n'+'ID No. : '+user_id +
                '\n'+'Department : '+department+'\n'+"Year : "+year
            )
        except Exception:
            update.message.reply_text(
                'Your profile was not found!'
            )
            return
        try:
            update.message.reply_text("Grade Report 👇")
            request = browser.click_link(url="/Grade/GradeReport")
            browser.open(request)
            content: bytes = (browser.response().read())
            soup = BeautifulSoup(content, 'html.parser')
            all_texts_list: list = [value.text.strip()
                                    for value in soup.find_all('td')]
            clean_list: list = [content.strip()
                                for content in all_texts_list if not 'Assessment' in content]
            unwanted_strings: list = ['1', '2', '3', '4', '5', '6',
                                      '7', '9', '2.00', '3.00', '4.00', '5.00']
            very_clean_list: list = [
                value for value in clean_list if not value in unwanted_strings]
            list_length: int = len(very_clean_list)
            count: int = 0
            for string in very_clean_list:
                count = count+1
                if count == list_length:
                    string: str = string+'\n\n  This bot was Made by @Esubaalew'
                update.message.reply_text(string)
        except Exception:
            update.message.reply_text(
                "Your Grade Report was not found!"
            )
            return

    except Exception:
        update.message.reply_text('Something went wrong! Please try later.')


def policy(update: Update, context: CallbackContext) -> None:
    user: str = update.message.from_user.first_name
    update.message.reply_text(f"""
Hello dear {user}, 
As the age is technological, most of us are the users of the technology. 
It is clear that as technology becomes more sophisticated, so does theft and fraud.
However, @AAU_Robot aims to send student information the moment the student ID 
and password are sent to it, and cannot remember and/or store any information.
Therefore, we remind you that anyone can freely send his/her ID and password and view Grade Report.
If you want to be sure that @AAU_Robot doesn't store your data, you can ask for the source code
at @Esubaalew.
    """
                              )


def start(update: Update, context: CallbackContext) -> None:
    """Starts the conversation with effective user.
    this function will be invoked everytime user hits /start
    """
    username: str = update.message.from_user.first_name
    greet: str = f'Selam, {username}!!'
    update.message.reply_text(
        f'{greet}\nI am AAU Robot! I was made to get your Grade report from THE AAU PORTAL!'
    )
    update.message.reply_text(
        "Now, Send me the USERNAME and PASSWORD as USERNAME&PASSWORD\n\
        Example: UGR/1234/12&8921"
    )


def bad_command(update: Update, context: CallbackContext) -> None:
    '''Detects unkown commands and tells user that robot don't understand '''
    update.message.reply_text(
        "Sorry,  '%s' is not a valid command! use /start to restart me or /policy to know how I use your data!" % update.message.text
    )


def filter_photos(update: Update, context: CallbackContext) -> None:
    """Detects photos from user and tells to user that robot can not search
    for photos"""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Photos/Images!",
        quote=True
    )


def filter_videos(update: Update, context: CallbackContext) -> None:
    """Detects videos received from user and tells to user that robot can not search
    for videos"""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Videos",
        quote=True
    )


def filter_contacts(update: Update, context: CallbackContext) -> None:
    """Detects contacts received from user and tells to user that robot can not search
    for contats"""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Contacts or Contacts are useless for me",
        quote=True
    )


def filter_polls(update: Update, context: CallbackContext) -> None:
    """Detects polls received from user and tells to user that robot can not search
    for polls"""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need polls or i don't search for them!",
        quote=True
    )


def filter_captions(update: Update, context: CallbackContext) -> None:
    """Detects captions received from user and tells to user that robot can not search
    for captions."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't need captions for my work or i don't search for them!",
        quote=True
    )


def filter_stickers(update: Update, context: CallbackContext) -> None:
    """Detects stickers received from user and tells to user that robot can not search
    for stickers."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Stickers!",
        quote=True
    )


def filter_animations(update: Update, context: CallbackContext) -> None:
    """Detects animations received from user and tells to user that robot can not search
    for animations."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for animations!",
        quote=True
    )


def filter_attachments(update: Update, context: CallbackContext) -> None:
    """Detects attachiments received from user and tells to user that robot can not search
    for attachments."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for attachments!",
        quote=True
    )


def filter_audios(update: Update, context: CallbackContext) -> None:
    """Detects audios received from user and tells to user that robot can not search
    for audios."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Currently, I don't search for Audios!",
        quote=True
    )


def filter_dice(update: Update, context: CallbackContext) -> None:
    """Detects dice received from user and tells to user that robot can not search
    for dice."""

    user: str = update.message.from_user.first_name
    update.message.reply_text(
        f"Dear {user}, Dice is beyound my knowlege!",
        quote=True
    )


def filter_documents(update: Update, context: CallbackContext) -> None:
    """Detects documents received from user and tells to user that the robot can not search
    for documents."""

    user: str = update.message.from_user.first_name
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
    updater.dispatcher.add_handler(CommandHandler('policy'))
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
