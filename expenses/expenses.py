from datetime import datetime
import argparse
import json
import os
import webbrowser

import requests
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

from . import api
from .api.exceptions import MonzoUnauthorizedError, MonzoBadRequestError

URL_DEVELOPER_PORTAL = 'https://developers.monzo.com'

client_id = os.environ.get('MONZO_EXPENSES_CLIENT_ID')
client_secret = os.environ.get('MONZO_EXPENSES_CLIENT_SECRET')
redirect_uri = os.environ.get('MONZO_EXPENSES_REDIRECT_URI',
                                  'http://localhost:3456')

def first_time_setup():

    OAUTH_PORT = '3456'
    try:
        webbrowser.get()
        redirect_uri = 'http://localhost:' + OAUTH_PORT
        headless = False
    except:
        headless = True
        redirect_uri = 'http://' + requests.get('http://canhazip.com').text.strip() \
                        + ':' + OAUTH_PORT
    print("""
    Welcome to Monzo Expenses!
    
    FIRST TIME SETUP
    ----------------
    
    Register a 'New Client' at
    {}

    You'll need the following details:
    
    Name:               Monzo Expenses
    Logo URL:           
    Redirect URLs:      {}
    Description:        Expense Reporting
    Confidentiality:    Confidential

    Then set the following environment variables:
        MONZO_EXPENSES_CLIENT_ID
        MONZO_EXPENSES_CLIENT_SECRET""".format(URL_DEVELOPER_PORTAL, redirect_uri))

    if not headless:
        input('Hit return to open your browser\n')
        webbrowser.open(URL_DEVELOPER_PORTAL)
    else:
        print('        MONZO_EXPENSES_REDIRECT_URI\n')

def generate_report(client, start_date, end_date,
                    filename, acc='personal'):

    print("Generating expense report...")

    accounts = client.accounts()

    account = None
    for a in accounts:
        if a.account_type == acc:
            account = a
    
    account_id = account.identifier
    account_holder = account.owners[0].preferred_name
    account_number = account.account_number
    sort_code = add_dashes(account.sort_code) 
    expenses = [txn for txn in client.transactions(account_id=account_id)
                 if start_date < txn.created < end_date
                 and txn.category == 'expenses']

    total = str(abs(sum([expense.amount for expense in expenses])))
    total_expenses = '£' + total[:-2] + '.' + total[-2:]

    for expense in expenses:
        new_amount = '£' + str(abs(expense.amount))[:-2] + '.' + str(abs(expense.amount))[-2:]
        expense.amount = new_amount

    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__) + '/templates/'))
    font_config = FontConfiguration()
    template = env.get_template("report.html")

    template_vars = {
        "start_date" : start_date,
        "end_date" : end_date,
        "account_holder" : account_holder,
        "sort_code" : sort_code,
        "account_number" : account_number,
        "generated" : datetime.now().strftime('%d/%m/%Y'),
        "expenses": expenses,
        "total": total_expenses
    }

    html_out = template.render(template_vars)
    HTML(string=html_out).write_pdf(os.path.join(os.getcwd(), filename),
        stylesheets=[CSS(
            filename=os.path.dirname(__file__) + '/templates/report.css',
            font_config=font_config)], font_config=font_config)

    print('Saved to the current directory as: ' + filename)

def add_dashes(sort_code):
    return '{}-{}-{}'.format(sort_code[:2], sort_code[2:4], sort_code[4:])

def main():
    """Main script entry point."""
    
    if not (client_id and client_secret):
        first_time_setup()

    client = api.MonzoClient(client_id, client_secret, redirect_uri)

    path = os.path.dirname(__file__) + '/api'
    if not os.path.isfile(path + '/monzo.json'):
        client.authenticate()
    else:
        with open(path + '/monzo.json') as fp:
            client.access_token = json.loads(fp.read())['access_token']

    try:
        accounts = client.accounts()
    except (MonzoUnauthorizedError, MonzoBadRequestError):
        client.authenticate()
        accounts = client.accounts()

    # Read user input.
    args = get_command_line_arguments()

    try:
        start_date = datetime.strptime(args['from'], '%d/%m/%y')
    except ValueError:
        print('Start Date must be in format: dd/mm/yy')
        return
    try:
        end_date = datetime.strptime(args['to'], '%d/%m/%y')
    except ValueError:
        print('End Date must be in format: dd/mm/yy')
        return

    generate_report(client,
                    start_date, end_date,
                    args.get('output') or 'expenses.pdf')

def get_command_line_arguments():
    parser = argparse.ArgumentParser(description='Monzo Expenses')
    parser.add_argument('-a','--account',
        help='Account (either "personal" or "joint"). Default is personal.',
        required=False)
    parser.add_argument('-f','--from',
        help='Period Start Date in format dd/mm/yy',
        required=True)
    parser.add_argument('-t','--to',
        help='Period End Date in format dd/mm/yy',
        required=True)
    parser.add_argument('-o','--output',
                        help='Filename for the saved PDF Expense Report',
                        required=False)
    return vars(parser.parse_args())

if __name__ == '__main__':
    main()

