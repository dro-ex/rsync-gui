import os, sqlite3, subprocess, shlex
from flask import Flask, render_template, request, redirect, url_for, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
DB = 'jobs.db'
sched = BackgroundScheduler()
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
            # remove existing
            sched.remove_job(str(job_id), jobstore=None, job_defaults=None) if sched.get_job(str(job_id)) else None
            # schedule new
            sched.add_job(
                rsync_job,
                'cron',
                id=str(job_id),
                args=[job_id, src, dest, opts],
                **{k:int(v) for k,v in [p.split('=') for p in cron.split()] }
            )
schedule_all()

@app.route('/')
def dashboard():
    with sqlite3.connect(DB) as db:
        stats = db.execute("SELECT COUNT(*), SUM(CASE WHEN last_status='OK' THEN 1 ELSE 0 END) FROM jobs").fetchone()
        jobs = db.execute("SELECT * FROM jobs").fetchall()
    return render_template('dashboard.html', stats=stats, jobs=jobs)

@app.route('/jobs')
def list_jobs():
    with sqlite3.connect(DB) as db:
        jobs = [dict(zip([c[0] for c in db.execute("PRAGMA table_info(jobs)")], row))
                for row in db.execute("SELECT * FROM jobs")]
    return jsonify(jobs)

@app.route('/jobs/add', methods=['POST'])
def add_job():
    data = request.form
    with sqlite3.connect(DB) as db:
        cur = db.execute(
            "INSERT INTO jobs (name,src,dest,options,cron) VALUES (?,?,?,?,?)",
            (data['name'], data['src'], data['dest'], data['options'], data['cron'])
        )
        job_id = cur.lastrowid
    schedule_all()
    return redirect(url_for('dashboard'))

@app.route('/jobs/edit/<int:job_id>', methods=['POST'])
def edit_job(job_id):
    data = request.form
    with sqlite3.connect(DB) as db:
        db.execute(
            "UPDATE jobs SET name=?,src=?,dest=?,options=?,cron=? WHERE id=?",
            (data['name'], data['src'], data['dest'], data['options'], data['cron'], job_id)
        )
    schedule_all()
    return redirect(url_for('dashboard'))

@app.route('/jobs/delete/<int:job_id>')
def delete_job(job_id):
    with sqlite3.connect(DB) as db:
        db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    try: sched.remove_job(str(job_id))
    except: pass
    return redirect(url_for('dashboard'))

@app.route('/builder')
def builder():
    return render_template('builder.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
