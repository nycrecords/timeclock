# README #


## About ##

TimeClock is a Flask-based application used to track employee hours and relevant employee information. The application's development functionality currently includes the ability to clock in and out, request and review time punches, request and review vacation periods, generate timesheets and invoices, and export data to the CSV file format. 

The objective is to make TimeClock as encompassing as possible, to provide a consistent, reliable, modern, and scalable system to municipal workers and administrators. 

TimeClock is developed and maintained by the New York City Department of Records.

Official Production Version: 2.0 (stable)

Current Development Version: 2.0

## Get Started ##

Here, you can find information on how to set up and deploy your own version of TimeClock. TimeClock requires Python 3.5.1+, Flask, and Postgresql. A list of all required packages can be found in the `requirements.txt` file in the root directory of the repository. 

### Initialization ###

To get started, download the source code and enter the top directory. We highly recommend [setting up a virtual environment](https://virtualenv.pypa.io/en/stable/) within which you can download and run necessary files. You can update the `config.py` file to set important configuration variables like your database name, your secret key (which we highly recommend you store as an environment variable), CSRF protection, and mail server information. 

Once you are satisfied with your application configuration, you can initialize the database by entering `python manage.py reset_db` in bash. Note that this will override any old data in the database if it already exists. 

That's it, you're all set! From here, you can begin creating user accounts, logging employee hours and payrates, and generating invoices through the web app.

### Testing ###

Currently, no unit tests are publicly available.



## Contribution Guidelines ##

We're not currently looking for any contributions, but if there are any features you'd like to see in TimeClock, feel free to contact us.



## Contact ##

For any questions or comments regarding the TimeClock application, you can contact the New York City Department of Records.

test