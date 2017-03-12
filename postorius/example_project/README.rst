===============================
Running the example application
===============================

Assuming you use virtualenv, follow these steps to download and run the
postorius example application in this directory:

::

    $ git clone https://gitlab.com/mailman/postorius.git
    $ cd postorius/example_project
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install -r requirements.txt

Now we need to create the database tables and an admin user.
Run the following and when prompted to create a
superuser choose yes and follow the instructions:

::

    $ python manage.py migrate
    $ python manage.py createsuperuser


Now you need to run the Django development server:

::

    $ python manage.py runserver

You should then be able to open your browser on http://127.0.0.1:8000 and see
postorius running.


If you are using the example_application for development, you have to install
postorius and mailmanclient another way. Be sure to have the virtualenv
activated and from the base directory of the respective repositories
you should run:

::

    $ python setup.py develop
