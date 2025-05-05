mport os, sqlite3, subprocess, shlex
from flask import Flask, render_template, request, redirect, url_for, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
DB = 'jobs.db'

# Configure scheduler to run jobs one at a time, no overlap
executors = {'default': ThreadPoolExecutor(1)}
job_defaults = {'coalesce': True, 'max_instances': 1}
sched = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
sched.start()

def init_db():
    with sqlite3.connect(DB) as db:
        db.execute('''
          CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            name TEXT,
            src TEXT,
            dest TEXT,
            options TEXT,
            cron TEXT,
            last_run TEXT,
            last_status TEXT
          )''')
init_db()


def rsync_job(job_id, src, dest, options):
    cmd = f"rsync {options} {shlex.quote(src)} {shlex.quote(dest)}"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    status = 'OK' if proc.returncode == 0 else 'FAIL'
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    with sqlite3.connect(DB) as db:
        db.execute(
            "UPDATE jobs SET last_run=?, last_status=? WHERE id=?",
            (now, status, job_id)
        )


def schedule_all():
    with sqlite3.connect(DB) as db:
        for row in db.execute("SELECT id, src, dest, options, cron FROM jobs"):
            job_id, src, dest, opts, cron = row
            # remove any existing job
            if sched.get_job(str(job_id)):
                sched.remove_job(str(job_id))
            # build cron args
            params = {k: int(v) for k,v in [p.split('=') for p in cron.split()]}
            sched.add_job(
                rsync_job,
                'cron',
                id=str(job_id),
                args=[job_id, src, dest, opts],
                **params
            )
schedule_all()

@app.route('/')
def dashboard():
    with sqlite3.connect(DB) as db:
        stats = db.execute("SELECT COUNT(*), SUM(CASE WHEN last_status='OK' THEN 1 ELSE 0 END) FROM jobs").fetchone()
        jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@app.route('/jobs/new')
def new_job():
    return render_template('job_form.html', job=None)

@app.route('/jobs/edit/<int:job_id>', methods=['GET'])
def edit_form(job_id):
    with sqlite3.connect(DB) as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        cols = [c[0] for c in db.execute("PRAGMA table_info(jobs)")]
        job = dict(zip(cols, row))
    return render_template('job_form.html', job=job)

@app.route('/jobs/add', methods=['POST'])
def add_job():
    data = request.form
    cron = f"minute={data['minute']} hour={data['hour']} day={data['day']} month={data['month']} day_of_week={data['dow']}"
    with sqlite3.connect(DB) as db:
        cur = db.execute(
            "INSERT INTO jobs (name,src,dest,options,cron) VALUES (?,?,?,?,?)",
            (data['name'], data['src'], data['dest'], data['options'], cron)
        )
        job_id = cur.lastrowid
    schedule_all()
    return redirect(url_for('dashboard'))

@app.route('/jobs/edit/<int:job_id>', methods=['POST'])
def edit_job(job_id):
    data = request.form
    cron = f"minute={data['minute']} hour={data['hour']} day={data['day']} month={data['month']} day_of_week={data['dow']}"
    with sqlite3.connect(DB) as db:
        db.execute(
            "UPDATE jobs SET name=?,src=?,dest=?,options=?,cron=? WHERE id=?",
            (data['name'], data['src'], data['dest'], data['options'], cron, job_id)
        )
    schedule_all()
    return redirect(url_for('dashboard'))

@app.route('/jobs/delete/<int:job_id>')
def delete_job(job_id):
    with sqlite3.connect(DB) as db:
        db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    try:
        sched.remove_job(str(job_id))
    except:
        pass
    return redirect(url_for('dashboard'))

@app.route('/builder')
def builder():
    return render_template('builder.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
