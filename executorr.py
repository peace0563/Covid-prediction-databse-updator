from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from master import execut

sched = BlockingScheduler()

# Schedule job_function to be called every two hours
sched.add_job(execut, 'interval', days=5)

sched.start()