# tiny polling app
# copyright 2020 Pascal Molin
from flask import Flask, request, render_template, session, redirect, url_for, send_file, send_from_directory
from markupsafe import Markup
from functools import wraps

app = Flask(__name__)
app.secret_key = "idontcaresecuresession"

class Vote(dict):
    """ id -> choice """
    template = None
    def __init__(self,form):
        self.text = form.get('text','',type=str)
        self.autopublish = form.get('autopublish',0,type=int)
        self.published = False
    def form(self):
        return Markup(render_template("form-%s.html"%self.template,this=self))
    def results(self):
        print(self)
        return Markup(render_template("results-%s.html"%self.template,this=self))
    @classmethod
    def create(cls):
        return Markup(render_template("create-%s.html"%cls.template,this=cls))

class YesNo(Vote):
    name = "Oui/Non"
    template = "yesno"
    _options = ['Non','Oui']
    def __init__(self, form):
        super().__init__(form)
        self.options = [ form.get(x,d,type=str) for x,d in enumerate(self._options) ]
        self.choices = [ 0 for x in self._options ]
    def submit(self,sha,form):
        choice = form.get('choice',type=int)
        self[sha] = choice
        self.choices[choice] += 1
        if len(self) == self.autopublish:
            self.published = True
class ABC(YesNo):
    name = "ABC"
    template = "yesno"
    _options = ['A','B','C']
class ABCD(YesNo):
    name = "ABCD"
    template = "yesno"
    _options = ['A','B','C','D']
class SELECT(Vote):
    name = "Choix"
    template = "select"
    def __init__(self, form):
        super().__init__(form)
        lines = form.get('options',type=str).split('\n')
        lines = [ l.strip() for l in lines ]
        self.options = [ l for l in lines if l ]
        self.choices = [ 0 for x in self.options ]
    def submit(self,sha,form):
        choices = form.getlist('choice',type=int)
        self[sha] = choices
        for i in choices:
            self.choices[i] += 1
        if len(self) == self.autopublish:
            self.published = True
    def counts(self):
        counts = list(zip(self.choices,self.options)) 
        counts.sort()
        return counts

class PollStation(list):
    """ as expected """
    types = [YesNo, ABC, ABCD, SELECT]
    limit = 1000
    options_defaults = [ ('anonymous','anonymiser les votes'),
                ('details',  'afficher le resultat des votes'),
                ('votants',  'liste des votants') ]
    def __init__(self, key, admin_key, form):
        super().__init__()
        self.key = key
        self.admin_key = admin_key
        self.number = form.get('number',0,type=int)
    def new(self, form):
        if len(self) > self.limit:
            return
        if form.get('admin_key') != self.admin_key:
            return
        i = form.get('type',type=int)
        self.append(self.types[i](form))
    def publish(self, form):
        if form.get('admin_key') == self.admin_key:
            i = form.get('index',type=int)
            self[i].published = True 
    def submit(self, form):
        i = form.get('index',type=int)
        sha = form.get('sha',type=str)
        self[i].submit(sha,form)
        return i
    def api(self, form):
        action = form.get('action',type=str)
        if action == 'new':
            self.new(form)
        elif action == 'publish':
            self.publish(form)
 
class VoteApp(dict):
    limit = 1000

    def create(self, form):
        if len(self) > self.limit:
            return None
        admin_key = form.get('admin_key',type=str)
        key = form.get('key',type=str)
        if key in self:
            return None
        self[key] = PollStation(key,admin_key,form)
        return self[key]
    def request(self, request):
        if 'key' in request.form:
            key = request.form.get('key',None,type=str)
        else:
            key = request.args.get('key',None,type=str)
        return self.get(key,None)
    def user_access(self, f):
        @wraps(f)
        def decorated(*args,**kwargs):
            votes = self.request(request)
            if votes is None:
                return render_template('illegal.html')
            return f(votes,*args,**kwargs)
        return decorated
    def admin_access(self, f):
        @wraps(f)
        def decorated(*args,**kwargs):
            if 'admin_key' in request.form:
                admin_key = request.form.get('admin_key',None,type=str)
            else:
                admin_key = request.args.get('admin_key',None,type=str) 
            votes = db.request(request)
            if votes is None or admin_key != votes.admin_key:
                return render_template('illegal.html');
            return f(votes,*args,**kwargs)
        return decorated

db = VoteApp()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/create', methods = ['GET','POST'])
def api_create():
    votes = db.create(request.form)
    if votes is None:
        render_template("illegal.html")
    return redirect(url_for('admin',key=votes.key,admin_key=votes.admin_key))

@app.route('/vote', methods = ['GET'])
@db.user_access
def vote(votes):
    print(session)
    if votes.key not in session:
        session[votes.key] = []
    return render_template("vote.html",this=votes,history=session[votes.key])

@app.route('/admin', methods = ['GET'])
@db.admin_access
def admin(votes):
    return render_template("admin.html",this=votes)

@app.route('/submit', methods = ['GET','POST'])
@db.user_access
def api_submit(votes):
    i = votes.submit(request.form)
    session[votes.key] = session.get(votes.key,[])+[i]
    print(session)
    return redirect(url_for('vote',key=votes.key))

@app.route('/new', methods = ['GET','POST'])
@db.admin_access
def api_new(votes):
    votes.new(request.form)
    return redirect(url_for('admin',key=votes.key,admin_key=votes.admin_key))

@app.route('/publish', methods = ['GET','POST'])
@db.admin_access
def api_publish(votes):
    votes.publish(request.form)
    return redirect(url_for('admin',key=votes.key,admin_key=votes.admin_key))

@app.route('/static/<path:filename>')
def api_static(filename):
    return send_from_directory('static',filename)

if __name__=='__main__':
    app.run(debug=True,
            #ssl_context='adhoc',
            port=7912)
