from flask import Flask, render_template, render_template_string, redirect, url_for, make_response, send_file, request
from auth import SessionManager, AccountManager
from challenges import assembleChallengePage, initDatabaseFromFiles, checkAnswer, updateChallengeSolves, getFileLocation
from werkzeug.exceptions import NotFound
from custom_methods import resetAll, checkLoggedIn, fullAssembleChallengePage

app = Flask(__name__)


@app.route('/')
def index():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return render_template('index.html', navBarPage="home", authenticated=False)
    else: # if logged in
        return render_template('index.html', navBarPage="home", authenticated=True)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        loggedIn = checkLoggedIn(request)

        if loggedIn == False: #if not logged in or if sessionID is wrong
            resp = make_response(render_template('login.html', navBarPage="login", authenticated=False))
            resp = SessionManager('./db/database.db').remove_session(request.cookies, resp) 
            # clear out the session id cookie for clean login (this func also removes the token from the db but since token does not exist nothing happens)
            return resp
            
        else: # if logged in
            return redirect(url_for('index'))

    if request.method == "POST":
        account = AccountManager('./db/database.db')
        resp = account.login(request)
        return resp

    
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "GET":
        loggedIn = checkLoggedIn(request)

        if loggedIn == False: #if not logged in or if sessionID is wrong
            resp = make_response(render_template('register.html', navBarPage="register", authenticated=False))
            resp = SessionManager('./db/database.db').remove_session(request.cookies, resp) 
            # clear out the session id cookie for clean register (this func also removes the token from the db but since token does not exist nothing happens)
            return resp
        else: # if logged in
            return redirect(url_for('index'))

    elif request.method == "POST":
        account = AccountManager('./db/database.db')
        resp = account.register(request)
        return resp

@app.route('/challenges')
def challenge():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else: # if logged in
        resp = fullAssembleChallengePage(loggedIn)
        return resp

@app.route('/challenges/<challengeID>', methods=['POST'])
def submitAnswer(challengeID):
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))

    else: # if logged in
        username = loggedIn
        answer = request.form['answer']

        account = AccountManager('./db/database.db') # interacts with user db
        allowed = account.checkAllowSubmit(username, challengeID) # interacts with user db
        pointsToAdd = checkAnswer(challengeID, answer) # interacts with challenge db

        if pointsToAdd != 0: # if answer is correct
            if allowed: # if user has not already solved this challenge
                account.addPoints(username, pointsToAdd) # interacts with user db
                account.addSolvedChallenge(username, challengeID) # interacts with user db

                updateChallengeSolves(challengeID) # interacts with challenge db

                resp = fullAssembleChallengePage(username, alertType="success", alertMessage="The answer you submitted is correct!")
                return resp

            else: # not required, for readability
                resp = fullAssembleChallengePage(username, alertType="warning", alertMessage="Correct, but no resubmitting!")
                return resp

        else: # if answer is wrong
            resp = fullAssembleChallengePage(username, alertType="danger", alertMessage="The answer you submitted is wrong!")
            return resp

@app.route('/files/<challengeID>')
def downloadFile(challengeID):
    loggedIn = checkLoggedIn(request)
    if loggedIn == False:
        return redirect(url_for('login'))
    else:
        location = getFileLocation(challengeID)
        if location != None:
            return send_file(location, as_attachment=True)
        else:
            return "file does not exist: spurious request?"

@app.route('/account')
def account():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else:
        username = loggedIn
        account = AccountManager('./db/database.db')
        points = account.getPoints(username)
        placing = account.getPlacing(username)

    return render_template('account.html', navBarPage="account", authenticated=True, username=username, points=points, placing=placing)
    
@app.route('/logout')
def logout():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else:
        resp = make_response(redirect(url_for('index')))
        resp = SessionManager('./db/database.db').remove_session(request.cookies, resp)
        return resp

@app.route('/leaderboard')
def leaderboard():
    loggedIn = checkLoggedIn(request)
    if loggedIn == False: #if not logged in or if sessionID is wrong
        return redirect(url_for('login'))
    else:
        account = AccountManager('./db/database.db')
        leaderboard = account.getLeaderboard()

        return render_template('leaderboard.html', navBarPage="leaderboard", authenticated=True, username=loggedIn, leaderboard=leaderboard)

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)