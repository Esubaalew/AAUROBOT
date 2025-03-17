# portal.py
"""
A telegram client for safely commuicating with AAU Portal.
"""
import mechanize
from mechanize import Browser
from bs4 import BeautifulSoup, Tag
from enum import Enum
from typing import Union, Tuple, List

AAIT = 'AAIT'
AAU = 'AAU'
EIABC = "EIABC"


class Campus(Enum):
    AAIT = 'https://portal.aait.edu.et/'
    AAU = 'https://portal.aau.edu.et/'
    EIABC = 'https://portal.eiabc.edu.et/'


def login_to_portal(campus: str, student_id: str, password: str)-> Union[str, Tuple[str, Browser]]:
    """
    Log in to the campus portal with the given credentials and return either a successful login response or an error message.

    Args:
        campus (str): The campus code, e.g., 'AAIT', 'AAU', or 'EIABC'.
        student_id (str): The student's ID.
        password (str): The student's password.

    Returns:
        Union[str, Tuple[str, Browser]]: Either a successful login response (tuple) or an error message (string).
    """
    try:
        campus = campus.upper()

        url: str
        if campus == AAIT:
            url = Campus.AAIT.value
        elif campus == EIABC:
            url = Campus.EIABC.value
        else:
            url = Campus.AAU.value

        login_response = ""
        browser: Browser = Browser()
        browser.set_handle_redirect(True)
        browser.set_handle_robots(False)
        browser.open(url)
        browser.select_form(nr=0)
        browser.addheaders = [('User-agent', 'Mozilla/104.0.2')]
        browser["UserName"] = student_id
        browser["Password"] = password
        response = browser.submit()
        requested_url = response.geturl()
        loged = browser.response().read()
        soup: BeautifulSoup = BeautifulSoup(loged, 'html.parser')
        if requested_url == f"{url}Home":
            return (loged, browser, False)
        if requested_url == f"{url}Grade/GradeReport":
            return (loged, browser, True)
        elif 'Incorrect username or password.' in soup.text:
            login_response = 'Incorrect username or password.'
        elif 'Invalid credentials. You have 4 more attempt(s) before your account gets locked out.' in soup.text:
            login_response = 'Invalid credentials. You have 4 more attempt(s) before your account gets locked out.'
        elif 'Invalid credentials. You have 3 more attempt(s) before your account gets locked out.' in soup.text:
            login_response = 'Invalid credentials. You have 3 more attempt(s) before your account gets locked out.'
        elif 'Invalid credentials. You have 2 more attempt(s) before your account gets locked out.' in soup.text:
            login_response = 'Invalid credentials. You have 2 more attempt(s) before your account gets locked out.'
        elif 'Invalid credentials. You have 1 more attempt(s) before your account gets locked out.' in soup.text:
            login_response = 'Invalid credentials. You have 1 more attempt(s) before your account gets locked out.'
        elif 'Your account has been locked out for 15 minutes due to multiple failed login attempts.' in soup.text:
            login_response = 'Your account has been locked out for 15 minutes due to multiple failed login attempts.'
        elif 'Your account has been locked out due to multiple failed login attempts.' in soup.text:
            login_response = 'Your account has been locked out due to multiple failed login attempts.'
        else:
            login_response = 'An unknown error occurred during login.'

        return (login_response)
    except mechanize.URLError as e:
        return "Failed to connect to the portal: " + str(e)
    except mechanize.FormNotFoundError as e:
        return "Login form not found."


def get_profile(campus: str, student_id: str, password: str)-> Union[str, Tuple[str, str]]:
    """
    Get the user profile information from the campus portal after a successful login.

    Args:
        campus (str): The campus code, e.g., 'AAIT', 'AAU', or 'EIABC'.
        student_id (str): The student's ID.
        password (str): The student's password.

    Returns:
        Union[str, Tuple[str, str]]: Either the user profile information (tuple) or an error message (string).
    """

    login_response = login_to_portal(campus, student_id, password)
    if isinstance(login_response, tuple):
        if login_response[-1]:
            return "It seems you are a graduate, so I am skipping your profile and showing your grade report below."
        
        html = login_response[0]
        soup = BeautifulSoup(html, 'html.parser')
        datas: list = [row.text.strip() for row in soup.table]
        free_list: list = [data for data in datas if not data == '']
        arr: list = [string.split('\n') for string in free_list]
        dictionary: dict = {}
        for sub_array in arr:
            dictionary[sub_array[0]] = sub_array[1]

        image: Tag = soup.find('img', {'class': 'img-rounded'})
        image: str = image['src']
        pre_text: str = f'https://portal.{campus.lower()}.edu.et/'
        image: str = pre_text+image

        user_name: str = dictionary['Full Name ']
        user_id: str = dictionary['ID No. ']
        department: str = dictionary['Department ']
        year: str = dictionary["Year "]

        return (
            image,
            'Full Name : '+user_name+'\n'+'ID No. : '+user_id +
            '\n'+'Department : '+department+'\n'+"Year : "+year
        )
    else:
        return login_response


def get_grades(campus: str, student_id: str, password: str)-> Union[str, List[str]]:
    """
    Get the student's grades from the campus portal after a successful login.

    Args:
        campus (str): The campus code, e.g., 'AAIT', 'AAU', or 'EIABC'.
        student_id (str): The student's ID.
        password (str): The student's password.

    Returns:
        Union[str, List[str]]: Either a list of grades or an error message (string).
    """
    
    login_response = login_to_portal(campus, student_id, password)
    if isinstance(login_response, tuple):
        browser = login_response[1]
        grade_url = browser.click_link(url="/Grade/GradeReport")
        browser.open(grade_url)
        html: bytes = (browser.response().read())
        soup = BeautifulSoup(html, 'html.parser')
        all_texts_list: list = [
            value.text.strip() for value in soup.find_all('td')
        ]
        clean_list: list = [
            content.strip() for content in all_texts_list
            if not 'Assessment' in content
        ]
        unwanted_strings: tuple = ('1', '2', '3', '4', '5', '6', '7', '8', '9',
                                   '2.00', '3.00', '4.00', '5.00')
        very_clean_list: list = [
            value for value in clean_list if not value in unwanted_strings
        ]
        return very_clean_list
    else:
        return login_response
