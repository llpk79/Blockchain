import json
import requests
from basic_wallet_p import app
from flask import request, render_template, redirect, url_for
# noinspection PyUnresolvedReferences
from forms import LoginForm


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    message = ''
    if form.validate_on_submit():
        # noinspection PyProtectedMember
        user = form.username._value()
        node = "http://localhost:5000"
        chain = requests.get(url=node + '/chain')
        chain = chain.json()['chain']

        for block in chain.values():
            for transaction in block['transactions']:
                if user == str(transaction['recipient']) or user == str(transaction['sender']):

                    payload = json.dumps({'user': user})
                    return redirect(url_for('.balance',
                                            payload=payload))

        message = 'Sorry, I cannot find that user in the chain.'
        return render_template('login.html',
                               title='Login',
                               form=form,
                               message=message)

    return render_template('login.html',
                           title='Login',
                           form=form,
                           message=message)


@app.route('/balance')
def balance():
    data = request.args['payload']
    data = json.loads(data)
    user = data['user']

    node = "http://localhost:5000"
    r = requests.get(url=node + '/chain')
    chain = r.json()['chain']
    bal = 0
    transactions = []

    for block in chain.values():
        for transaction in block['transactions']:

            if str(transaction['sender']) == str(transaction['recipient']) == user:
                bal += transaction['amount']
                transaction['sender'] = 0
                transactions.append(transaction)

            elif user == str(transaction['recipient']):
                bal += transaction['amount']
                transactions.append(transaction)

            elif user == str(transaction['sender']):
                bal -= transaction['amount']
                transaction['amount'] *= -1
                transactions.append(transaction)
    transactions = list(sorted(transactions, key=lambda x: x['timestamp'], reverse=True))
    return render_template('wallet.html',
                           user=user,
                           transactions=transactions,
                           balance=bal,
                           title='Balance and Transactions')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, load_dotenv=True)
