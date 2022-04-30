# Eye - exam project

My team and I made a service for teachers, which allows to quickly create test works, and will also check them from photos


The created service consists of 3 parts:
1. Web application in which you can create tests, as well as view the results of them.

2. Telegram bot that receives and processes photos of test papers

3. Validation algorithm that checks each work by the photo that telegram bot has received

https://www.loom.com/share/f3b0feb37f1d4bfe8113e82e038b1b3a
https://www.loom.com/share/32e1fce2b96146d5ae209d3c1b8b9e02

By clicking on these links you will see a demonstration of the web application and telegram bot work.

# To launch project, you need to: 

1. Install venv and requirements
2. Add a database
3. Create a Superuser for django app
4. Launch Bot
5. Launch Django web server

# Install venv and requirements

1. Activate virtual environment
2. From root folder run `pip install -r requirements.txt`

# Add a database 

1. `.cd` to `eye-exam-project/eye_exam`
2. run `python manage.py makemigrations` command
3. run `python manage.py migrate` command

# Create a Superuser for django app 

1. In `eye-exam-project/eye_exam` directory run `python manage.py createsuperuser` command
2. After that write your username, email address and password

# Launch bot:

1. Obtain telegram bot api token
2. Paste your api token to `eye-exam-project/eye_exam/tasks/bot/bot_settings.py`
3. Simply launch `eye-exam-project/eye_exam/tasks/bot/handlers.py` from root directory of the project
4. Open your bot in telegram and write something or send a photo of test paper to it

# Launch django app:

1. run `python eye-exam-project/eye_exam/manage.py runserver`
2. navigate to `http://127.0.0.1:8000/`
