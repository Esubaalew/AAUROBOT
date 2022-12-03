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
import logging
from datetime import date, timedelta
import requests
from bs4 import (
    BeautifulSoup,
    Tag)
from database import (
    InsertData,
    createTable,
    deleteFromTable,
    deleteTableData,
    readTable,
    registedcount,
    searchTable,
    searchTable2,
    registedtoday
)
from mechanize import Browser
from requests import Response
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

aait = 'AAiT'
aau = 'AAU'


loged_buttons = [
    [KeyboardButton("Grade Report")],
    [KeyboardButton("View Profile")],
    [KeyboardButton("Privacy Policy"), KeyboardButton("Delete-Account")],
    [KeyboardButton("Help"), KeyboardButton("About This Bot")],
    [KeyboardButton("Statistics")]
]
unloged_buttons = [
    [KeyboardButton("Feedback")],
    [KeyboardButton('Statistics')]
]


def detect_campus(campus: str) -> str:
    '''identifies which campus portal user wil select'''

    if campus == aau:
        return aau
    elif campus == aait:
        return aait


def grade_aait(update: Update, context: CallbackContext) -> None:
    """
    This function is is about scrping the AAit Portal.
    This function is the main part of @AAU_Robot.
    It gets the grade report and profile information of AAU student. This function
    will be invoked anytime the user sends a text message.
    The function though will be happy only if it gets text like-
    UGR/blana/12&1234.
     Note:
    The bot will understand the above input as:

    ID No: UGR/blana/12
    Password: 1234

     Easy problems:
    These problems are problems that make robot reject the input before accessing
    the website.
    If user send shorter or longer ID&password combination than needed, or if user omitted /  and/or
    & sign and /or mis position them, different warnings will arrive.

     Hard Problems:
    The problems are problems that terminate the login process after the robtot
    tried to log in the website.

    The login request may fail due to many resons. If the ID No is correct and
    the password is wrong, the user will be  warned four times and the account will get
    locked after four wrong  attempts totaly with 5 worng inputs.
    If the username is wrong(not found, expired), user will get 'Incorrect username or password.'
    warning message.
    And more badly if the website stopped working, the login failed message will arrive.

    "Your Grade Report was not found!" message may also arrive if the grade report field is
    empty.(May be this is on the first year first semester)

    """

    user = update.message.from_user
    user_input = update.message.text.strip()
    tg_id: int = user.id
    if user_input == 'Feedback':
        feedback(update, context)
        return
    if user_input == 'Statistics':
        stat(update, context)
        return
    registerd = searchTable2(tg_id)
    if registerd:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = searchTable2(
            tg_id)
        if user_input == 'Statistics':
            stat(update, context)
            return
        if user_input == "Help":
            help(update, context)
            return
        if user_input == "About This Bot":
            about(update, context)
            return
        if user_input == "Grade Report":
            grade(update, context)
            return
        if user_input == 'Privacy Policy':
            policy(update, context)
            return
        if user_input == "Delete-Account":
            delete(update, context)
            return
        if user_input == "View Profile":
            profile(update, context)
            return
        user_input = user_input.lower()
        if 'grade' in user_input:
            password = user_input.replace("grade", '')
        else:
            update.message.reply_text(
                "Prefxing your password with grade is a must")
            return

        try:
            url: str = 'https://portal.aait.edu.et/Grade/GradeReport'
            browser: Browser = Browser()
            browser.set_handle_redirect(True)
            browser.set_handle_robots(False)
            update.message.reply_text('I am acessing the aait portal',
                                      quote=True)

            browser.open(url)
            browser.select_form(nr=0)
            browser.addheaders: list = [('User-agent', 'Mozilla/104.0.2')]
            browser["UserName"] = reg_id
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
        This is most probably the website's own problem!
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
                pre_text: str = 'https://portal.aait.edu.et/'
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
                unwanted_strings: tuple = ('1', '2', '3', '4', '5', '6',
                                           '7', '8', '9', '2.00', '3.00', '4.00', '5.00')
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
            update.message.reply_text(
                'Something went wrong! Please try later.')
        return

    userP: str = update.message.text
    userP = userP.strip().upper()
    prefix = "AAIT"
    userP = userP.replace(prefix, '')
    userP = userP.strip()
    space: str = ' '
    if space in userP:
        userP = userP.replace(space, '')
    else:
        pass
    if len(userP) < 11:
        update.message.reply_text(
            f"The length of your ID No '{userP}' is too short. {11-len(userP)} chars omitted"
        )
        return
    if len(userP) > 11:
        update.message.reply_text(
            f"The length of your ID No '{userP}' is too long. {len(userP)-11} chars mis-added"
        )
        return
    if not '/' in userP:
        update.message.reply_text(
            "You omitted and '/'"
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

    userId: str = userP
    user = update.message.from_user
    tg_id: int = user.id
    id_num = userId
    tg_name: str = user.first_name
    campus: str = 'aait'
    datejoined: date = date.today()
    datejoined = datejoined.strftime("%d/%m/%Y")
    aait_profile = (tg_id, id_num, tg_name, campus, datejoined)
    createTable()
    InsertData(aait_profile)
    update.message.reply_text(
        """You have succesfully registered your account! Please /start me Again! 
You can see your profile info using /profile """,
        reply_markup=ReplyKeyboardRemove())
    return


def stat(update: Update, context: CallbackContext):
    tg_id = update.message.from_user.id
    users = registedcount()
    users_today = registedtoday()
    update.message.reply_text(
        f"""
REGISTERED TODAY:
{users_today}

ALL USERS:
{users}

Note that the above number do not include peoples who register and delete thier account.
        """
    )


def feedback(update: Update, context: CallbackContext):
    '''Responds to the feedback keyboard. This is invoked when user enters feedback text'''

    update.message.reply_text(
        "If you are not happy, by what this bot is performing, send your comment at https://esubechekol.wordpress.com/contact/.\n\nUse /start to register",
    )
    return


def grade(update: Update, context: CallbackContext) -> None:
    '''Requests user to enter their password to access grade report'''

    tg_id = update.message.from_user.id
    registerd = searchTable2(tg_id)
    if registerd:
        update.message.reply_text(
            "To see your garde report please send your Password prefixed with grade. \nExample:\ngrade1234")
        return
    elif not registerd:
        update.message.reply_text(
            "Viewing grade report is not available for unregisterd users. ",
            reply_markup=ReplyKeyboardRemove())
        return


def delete(update: Update, context: CallbackContext) -> None:
    '''deletes the registered user from'''

    tg_id = update.message.from_user.id
    registerd = searchTable2(tg_id)
    if registerd:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = searchTable2(
            tg_id)
        deleteFromTable(tg_id)
        update.message.reply_text(
            f"""
Account with following details has succesufully deleted, If you have feedback please use the feedback keyboard!

TelegramID={reg_tg_id}
PortalID={reg_id}
TelegramName={reg_name}
PortalName={reg_campus}
DateJoined={reg_date}

You can register again by using /start command !
    """,
            reply_markup=ReplyKeyboardMarkup(
                unloged_buttons,
                resize_keyboard=True,
                one_time_keyboard=True)
        )
        return
    elif not registerd:
        update.message.reply_text(
            "Deleting account  is not available for unregistered users. Register using /start first. ",
            reply_markup=ReplyKeyboardRemove()
        )
        return


def profile(update: Update, context: CallbackContext) -> None:
    '''Shows the details of registered user'''

    tg_id = update.message.from_user.id
    registerd = searchTable2(tg_id)
    if registerd:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = searchTable2(
            tg_id)
        update.message.reply_text(
            f"""
Your account informations are as shown below: 

TelegramID={reg_tg_id}
PortalID={reg_id}
TelegramName={reg_name}
PortalName={reg_campus}
DateJoined={reg_date}

If the informations above are incorrect, please use /delete to delete your account. 
    """,  reply_markup=ReplyKeyboardMarkup(
                loged_buttons,
                resize_keyboard=True,
                one_time_keyboard=True,
                input_field_placeholder='What do you want?'
            )
        )
        return
    elif not registerd:
        update.message.reply_text(
            "Viewing profile is not available for unregistered users. Please Register using /start .",
            reply_markup=ReplyKeyboardRemove()
        )
        return


def get_aau_report(update: Update, context: CallbackContext) -> None:
    """
    This function is is about scraping the AAU Portal.
    This function is the main part of @AAU_Robot.
    It gets the grade report and profile information of AAU student. This function
    will be invoked anytime the user sends a text message.
    The function though will be happy only if it gets text like-
    UGR/blana/12&1234.
     Note:
    The bot will understand the above input as:

    ID No: UGR/blana/12
    Password: 1234

     Easy problems:
    These problems are problems that make robot reject the input before accessing
    the website.
    If user send shorter or longer ID&password combination than needed, or if user omitted /  and/or
    & sign and /or mis position them, different warnings will arrive.

     Hard Problems:
    The problems are problems that terminate the login process after the robtot
    tried to log in the website.

    The login request may fail due to many resons. If the ID No is correct and
    the password is wrong, the user will be  warned four times and the account will get
    locked after four wrong  attempts totaly with 5 worng inputs.
    If the username is wrong(not found, expired), user will get 'Incorrect username or password.'
    warning message.
    And more badly if the website stopped working, the login failed message will arrive.

    "Your Grade Report was not found!" message may also arrive if the grade report field is
    empty.(May be this is on the first year first semester)

    """

    user = update.message.from_user
    user_input = update.message.text.strip()
    tg_id: int = user.id
    registerd = searchTable2(tg_id)
    if user_input == 'Feedback':
        feedback(update, context)
        return
    if user_input == 'Statistics':
        stat(update, context)
        return
    if registerd:

        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = searchTable2(
            tg_id)

        if str(reg_campus) == 'aait':
            grade_aait(update, context)
            return
        if user_input == 'Statistics':
            stat(update, context)
            return
        if user_input == "Help":
            help(update, context)
            return
        if user_input == "About This Bot":
            about(update, context)
            return
        if user_input == "Grade Report":
            grade(update, context)
            return
        if user_input == 'Privacy Policy':
            policy(update, context)
            return
        if user_input == "Delete-Account":
            delete(update, context)
            return
        if user_input == "View Profile":
            profile(update, context)
            return
        user_input = user_input.lower()
        if 'grade' in user_input:
            password = user_input.replace("grade", '')
        else:
            update.message.reply_text(
                "Prefxing your password with grade is must. If you don't understand me use /start")
            return

        try:
            url: str = 'https://portal.aau.edu.et/Grade/GradeReport'
            browser: Browser = Browser()
            browser.set_handle_redirect(True)
            browser.set_handle_robots(False)
            update.message.reply_text('I am acessing the aau portal',
                                      quote=True)

            browser.open(url)
            browser.select_form(nr=0)
            browser.addheaders: list = [('User-agent', 'Mozilla/104.0.2')]
            browser["UserName"] = reg_id
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
        This is most probably the website's own problem!
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
                unwanted_strings: tuple = ('1', '2', '3', '4', '5', '6',
                                           '7', '8', '9', '2.00', '3.00', '4.00', '5.00')
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
            update.message.reply_text(
                'Something went wrong! Please try later.')
        return

    tg_name: str = user.first_name
    datejoined: date = date.today()
    datejoined = datejoined.strftime("%d/%m/%Y")
    campus = detect_campus(update.message.text)
    if campus == aait:
        aait_pict: str = 'aau.edu.et/aait/wp-content/uploads/sites/17/2014/08/5killo.jpg'
        update.message.reply_photo(
            aait_pict,
            f"""Dear AAiT student, {tg_name}!

To see your Profile and Grade report enter your ID as 'aaityourid'.

Example:

If your Id No is 'UGR/xyzw/11',\
 you must send it as aaitUGR/xyzw/11.

            """
        )
        return
    if campus == aau:
        aau_logo = 'http://www.aau.edu.et/wp-content/uploads/2017/06/wallnew2.png'
        update.message.reply_photo(
            aau_logo,
            f"""Dear AAU student, {tg_name}!

To see your Profile and Grade report enter your ID.


            """
        )
        return

    userP: str = update.message.text
    if 'aait' in userP.lower():
        grade_aait(update, context)
        return
    else:
        pass
    userP = userP.strip().upper()
    space: str = ' '
    if space in userP:
        userP = userP.replace(space, '')
    else:
        pass
    if len(userP) < 11:
        update.message.reply_text(
            f"The length of your ID No '{userP}' is too short. {11-len(userP)} chars omitted"
        )
        return
    if len(userP) > 11:
        update.message.reply_text(
            f"The length of your ID No '{userP}' is too large. {len(userP)-11} chars mis-added!"
        )
        return

    if not '/' in userP:
        update.message.reply_text(
            "You omitted  '/'"
        )
        return

    else:
        pass
    if not userP[3] == '/':
        update.message.reply_text(
            '/ is not in its legal position. Please re-enter...',
            quote=True
        )
        return
    else:
        pass
    if not userP[8] == '/':
        update.message.reply_text(
            '/ is not in its legal position. Please re-enter...',
            quote=True
        )
        return
    else:
        pass
    userId: str = userP
    id_num = userId
    campus: str = 'aau'
    aau_profile = (tg_id, id_num, tg_name, campus, datejoined)
    InsertData(aau_profile)
    update.message.reply_text(
        """You have succesfully registered your account! Please /start me Again! 
You can see your profile info using /profile """, reply_markup=ReplyKeyboardRemove())
    return


def help(update: Update, context: CallbackContext):
    """Show the some help the uset may refer to"""

    update.message.reply_text(
        "You can read help article here https://telegra.ph/HELP-for-AAU-Robot-12-03 ")
    return


def about(update: Update, context: CallbackContext):
    '''Shows some message from bit writter'''

    update.message.reply_text(
        "Please read about the bot here https://telegra.ph/About-AAU-ROBOT-12-03")
    return


def policy(update: Update, context: CallbackContext) -> None:
    """Tells user a message about how the bot handels user data"""

    user: str = update.message.from_user.first_name
    url = 'https://website.informer.com/portal.eiabc.edu.et'
    web_content: Response = requests.get(url)
    beauty: BeautifulSoup = BeautifulSoup(web_content.content, 'html.parser')
    photo_conatiner: Tag = beauty.find(
        'img',
        {"class": "screenshotDefaultSize screenshotLoading",
         'title': "Portal.eiabc.edu.et thumbnail",
         "alt": "Portal.eiabc.edu.et thumbnail"
         })
    photo_address: str = photo_conatiner['src']
    update.message.reply_photo(
        photo_address,
        f"""Hello dear {user}, 
As the age is technological, most of us are the users of the technology. 
It is clear that as technology becomes more sophisticated, so does theft and fraud.
However, @AAU_Robot aims to send student information the moment the student ID 
and password are sent to it, and cannot remember and/or store any information.
Therefore, we remind you that anyone can freely send his/her ID and password and view Grade Report.
If you want to be sure that @AAU_Robot doesn't store your data, you can ask for the source code
from BOT DEVELOPER."""
    )


def start(update: Update, context: CallbackContext) -> None:
    """Starts the conversation with effective user.
    this function will be invoked everytime user hits /start
    """
    tg_id = update.message.from_user.id
    registerd = searchTable2(tg_id)
    if registerd:
        reg_tg_id, reg_id, reg_name, reg_campus, reg_date = searchTable2(
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
        return

    username: str = update.message.from_user.first_name
    start_buttons = [[KeyboardButton(aait), KeyboardButton(aau)]]
    greet: str = f'Selam, {username}🤗!!'
    update.message.reply_text(
        f'''{greet}\n\nI am AAU Robot, made to get your Profile and Grade report from THE AAU PORTAL!

Which CAMPUS are you from?

''',
        reply_markup=ReplyKeyboardMarkup(
            start_buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder='Select Your Campus 👇')
    )


def bad_command(update: Update, context: CallbackContext) -> None:
    '''Detects unkown commands and tells user that robot don't understand '''
    update.message.reply_text(
        "Sorry,  '%s' is not a valid command! use /start to restart me or /policy to know how I use your data!"
        % update.message.text
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
    # createTable()
    TOKEN: str = 'TOKEN'
    updater = Updater(TOKEN,
                      use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & (~Filters.command), get_aau_report))
    updater.dispatcher.add_handler(CommandHandler('policy', policy))
    updater.dispatcher.add_handler(CommandHandler('profile', profile))
    updater.dispatcher.add_handler(CommandHandler('delete', delete))
    updater.dispatcher.add_handler(CommandHandler('about', about))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('feedback', feedback))
    updater.dispatcher.add_handler(CommandHandler('stat', stat))
    updater.dispatcher.add_handler(CommandHandler('grade', grade))
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
