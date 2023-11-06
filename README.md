
# AAU Robot Telegram Bot

AAU Robot is a Telegram bot designed to provide students of Addis Ababa University with quick access to their academic information, including grade reports and profile details. The bot ensures the privacy and security of user data while offering a convenient way for students to retrieve important information.

## Features

- **Grade Report:** Students can request their grade reports by providing their student ID and a password. The bot securely logs in to the AAU student portal to fetch and display the grade report.

- **View Profile:** Students can view their profile information, including their Telegram ID, Portal ID, and campus details.

- **Delete Account:** Registered users can delete their accounts by answering a math question. This provides an extra layer of security.

- **Data Encryption:** All sensitive data, including student IDs and passwords, are encrypted using the Fernet symmetric encryption method to ensure the security and privacy of user information.

- **Permanent Accounts:** Users who have registered with the bot do not need to enter their data again. The bot remembers their information for quick and easy access.


## Usage/Examples

1. Start a conversation with the bot using the `/start` command.

2. Agree to the terms and conditions to begin registration.

3. Choose your campus (AAIT, AAU, or EIABC) during registration.

4. Enter your student ID in the format "UGR/XXXX/YY" to complete registration.

5. You can then access your grade report, view your profile, and delete your account without entering your data again.

## Security

AAU Robot takes user data privacy seriously. The bot does not store or remember any user data, ensuring that your information remains secure. All sensitive data is encrypted using the Fernet encryption method.

You can read more about the bot's privacy policy using the `/policy` command.
## Additonal information

- [About AAU Robot](https://telegra.ph/About-AAU-ROBOT-12-03): Learn more about the bot's development and purpose.

- [Help for AAU Robot](https://telegra.ph/HELP-for-AAU-Robot-12-03): Find help articles to guide you through using the bot.
## Run Locally

Clone the project

```bash
  git clone https://github.com/Esubaalew/AAUROBOT
```

Go to the project directory

```bash
  cd AAUROBOT
```

Install the required Python packages

```bash
  pip install -r requirements.txt
```

Run the bot

```bash
 python bot.py
```

