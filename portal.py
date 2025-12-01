# portal.py
"""
A telegram client for safely commuicating with AAU Portal.
"""

import requests
from bs4 import BeautifulSoup
from enum import Enum
from typing import Union, Tuple, List
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Campus(Enum):
    """Enumeration of supported campus portal base URLs."""
    AAIT = 'https://portal.aait.edu.et/'
    AAU = 'https://portal.aau.edu.et/'
    EIABC = 'https://portal.eiabc.edu.et/'

class PortalClient:
    """A client for interacting with the AAU Portal, maintaining a single session for efficiency."""
    
    def __init__(self, campus: str, student_id: str, password: str):
        """
        Initialize the client with campus, student credentials, and a requests session.
        
        Args:
            campus (str): The campus code ('AAIT', 'AAU', 'EIABC').
            student_id (str): The student's ID.
            password (str): The student's password.
        """
        self.campus = campus.upper()
        try:
            self.base_url = Campus[self.campus].value
        except KeyError:
            raise ValueError(f"Invalid campus code: {campus}. Must be 'AAIT', 'AAU', or 'EIABC'.")
        
        self.student_id = student_id
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
            'Referer': self.base_url
        })
        self.logged_in = False
        self.on_grade_page = False

    def login(self) -> Union[str, None]:
        """
        Log in to the portal and set session state.
        
        Returns:
            Union[str, None]: None if successful, error message if failed.
        """
        try:
            login_page_url = self.base_url
            response = self.session.get(login_page_url, verify=False, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')

            payload = {
                'UserName': self.student_id,
                'Password': self.password,
                'button': 'login'
            }

            for hidden in soup.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    payload[name] = value

            login_endpoint = self.base_url + 'Account/Login'
            resp = self.session.post(
                login_endpoint,
                data=payload,
                verify=False,
                timeout=20,
                allow_redirects=True
            )

            final_url = resp.url

            if '/Home' in final_url:
                self.logged_in = True
                self.on_grade_page = False
                return None
            elif '/Grade/GradeReport' in final_url:
                self.logged_in = True
                self.on_grade_page = True
                return None

            error_soup = BeautifulSoup(resp.text, 'html.parser')
            error_elem = (
                error_soup.find('span', class_='field-validation-error') or
                error_soup.find('div', class_='validation-summary-errors') or
                error_soup.find('li', string=lambda t: t and 'incorrect' in t.lower())
            )
            if error_elem:
                error_text = error_elem.get_text(strip=True)
                if 'locked' in error_text.lower():
                    return "Your account has been locked out for 15 minutes due to multiple failed login attempts."
                if 'attempt' in error_text:
                    return error_text
                return error_text or "Invalid credentials."

            return "An unknown error occurred during login."

        except requests.exceptions.Timeout:
            return "Failed to connect to the portal: request timed out."
        except requests.exceptions.ConnectionError:
            return "Failed to connect to the portal: connection error."
        except Exception as e:
            return f"Login failed: {str(e)}"

    def get_profile(self) -> Union[str, Tuple[str, str]]:
        """
        Retrieve the student's profile information.
        
        Returns:
            Union[str, Tuple[str, str]]: 
                - Tuple of (image_url, profile_details) if successful.
                - "GRADUATED" if student is graduated.
                - Error message if failed.
        """
        if not self.logged_in:
            login_result = self.login()
            if login_result is not None:
                return login_result

        if self.on_grade_page:
            return "GRADUATED"

        try:
            profile_url = self.base_url + 'Home'
            resp = self.session.get(profile_url, verify=False, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            img_tag = soup.find('img', class_='img-rounded')
            if img_tag and img_tag.get('src'):
                src = img_tag['src']
                if src.startswith(('http://', 'https://')):
                    image_url = src
                else:
                    image_url = self.base_url.rstrip('/') + '/' + src.lstrip('/')
            else:
                image_url = "https://i.imgur.com/6zZ9b8Z.png"

            data = {}
            table = soup.find('table')
            if table:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).rstrip(': ')
                        value = cells[1].get_text(strip=True)
                        data[key] = value

            full_name = data.get('Full Name', 'N/A')
            student_id = data.get('ID No.', 'N/A')
            department = data.get('Department', 'N/A')
            year = data.get('Year', 'N/A')

            profile_details = (
                f"Full Name: {full_name}\n"
                f"ID No.: {student_id}\n"
                f"Department: {department}\n"
                f"Year: {year}"
            )
            return (image_url, profile_details)

        except Exception as e:
            return f"Profile fetch failed: {str(e)}"

    def get_grades(self) -> Union[str, List[str]]:
        """
        Retrieve the student's grades, organized by semesters.
        
        Returns:
            Union[str, List[str]]: List of semester grade strings if successful, error message if failed.
        """
        if not self.logged_in:
            login_result = self.login()
            if login_result is not None:
                return login_result

        try:
            grade_url = self.base_url + 'Grade/GradeReport'
            resp = self.session.get(grade_url, verify=False, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            semesters: List[str] = []
            current_semester: List[str] = []
            skip_phrases = {'Assessment'}
            skip_values = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '2.00', '3.00', '4.00', '5.00'}

            for td in soup.find_all('td'):
                text = td.get_text(strip=True)
                if not text:
                    continue
                if text in skip_values or any(phrase in text for phrase in skip_phrases):
                    continue
                current_semester.append(text)
                if 'Academic Status' in text or 'CGPA' in text:
                    if current_semester:
                        semesters.append("\n".join(current_semester))
                        current_semester = []

            if current_semester:
                semesters.append("\n".join(current_semester))

            return semesters if semesters else ["No grades available yet."]

        except Exception as e:
            return f"Grades fetch failed: {str(e)}"
