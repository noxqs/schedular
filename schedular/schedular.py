import json
import threading
import time
from datetime import datetime, timedelta
from math import floor
from multiprocessing.dummy import Pool as Pool

DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DAYSS = dict((v, k) for k, v in DAYS.iteritems())


class Job():
    def __init__(self, days, job, start_time=None,  end_time=None, cut_off_time=None, interval=None, jobArgs=[], now=None, id=None, group=None):
        self.now            = now
        self.job_thread     = None
        self.id             = id
        self.next_run       = None
        self.next_day       = None
        self.group          = group
        self.start_time     = None
        self.end_time       = None
        self.cut_off_time   = None
        self.dayss          = []
        self.days           = []

        if isinstance(days,basestring):
            days            = days.split(",")

        if not isinstance(days,list):
            print "No days"
            return

        try:
            if isinstance(end_time, basestring):
                self.end_time = datetime.strptime(end_time, "%H:%M:%S")
            elif isinstance(end_time, datetime):
                self.end_time = end_time
        except ValueError as e:
            print "end_time not in HH:MM:SS format:", end_time

        try:
            if isinstance(start_time, basestring):
                self.start_time = datetime.strptime(start_time, "%H:%M:%S")
            elif isinstance(start_time, datetime):
                self.start_time = start_time
        except ValueError as e:
            print "start time not in HH:MM:SS format:", start_time

        try:
            if isinstance(cut_off_time, basestring):
                self.cut_off_time = datetime.strptime(cut_off_time, "%H:%M:%S")
            elif isinstance(cut_off_time, datetime):
                self.cut_off_time = cut_off_time
        except ValueError as e:
            print "cut_off_time not in HH:MM:SS format:", cut_off_time

        for day in days:
            if isinstance(day, int) or (isinstance(day, basestring) and day.isdigit()):
                if isinstance(day, basestring) and day.isdigit():
                    day = int(day)
                self.dayss.append(DAYSS[day])
                self.days.append(day)
            elif isinstance(day, basestring):
                self.dayss.append(day)
                self.days.append(DAYS[day])

        if interval is not None:
            if interval.endswith("m"):
                interval = interval.replace("m", "")
                interval = 60 * int(interval)
            elif interval.endswith("s"):
                interval = interval.replace("s", "")
                interval = int(interval)
            elif interval.endswith("h"):
                interval = interval.replace("h", "")
                interval = 60 * 60 * int(interval)
            elif interval.isdigit():
                interval = int(interval)
            else:
                print "Unknown interval"
                return

        self.interval       = interval
        self.job            = job
        self.jobArgs        = jobArgs
        self.calc_next_run()


    def get_days_as_string(self):
        days = []
        for day in self.days:
            days.append(DAYS[day])
        return ",".join(days)


    def calc_day(self, day, next_week=False):
        self.next_day = day
        today = datetime.today()
        if next_week:
            _day = today + timedelta((day - today.weekday()) % 7)
            self.next_run = self.next_run.replace(year=_day.year, day=_day.day, month=_day.month)
        else:
            _day = today + timedelta((day - today.weekday()) % 7)
            self.next_run = self.next_run.replace(year=_day.year, day=_day.day, month=_day.month)

    def info(self,as_json=False):
        st = self.start_time.strftime("%H:%M:%S") if self.start_time is not None else "NONE"
        et = self.end_time.strftime("%H:%M:%S") if self.end_time is not None else "NONE"
        interval = "%ss." % self.interval if self.interval is not None else "NONE"
        today_num = datetime.now().weekday()

        dummy = " ID:%s DAYS:%s ST:%s ET:%s INT:%s JOB:%s(%s)" % (
        self.id, ", ".join(self.dayss), st, et, interval, self.job.__name__, str(self.jobArgs))
        dummy += ", NEXT: %s (%s)" % (
            self.next_run.strftime("%a %d-%m-%Y %H:%M:%S") if self.next_run is not None else "NONE", "this week" if self.next_day is not None and today_num <= self.next_day else "next week")

        runStat = ""

        if self.start_time is not None and self.next_day is not None:
            if datetime.now().replace(year=1900, day=1, month=1) > self.start_time and self.next_day == datetime.now().weekday():
                runStat=" [ACTIVE]" if self.end_time is not None else " [ONCE]"
            else:
                runStat=" [PENDING]" if self.end_time is not None else " [ONCE]"
        else:
            if self.cut_off_time is not None:
                runStat = "[ACTIVE]"
            else:
                runStat = "UNKNOWN"

        dummy += runStat

        if self.now is not None:
            dummy += " TEST with now as %s" % (self.now)

        if as_json:

            if self.next_run is not None:
                nextRun = self.next_run.strftime("%a %d-%m-%Y %H:%M:%S")
            else:
                nextRun = "unknown date"

            if today_num <= self.next_day:
                nextRun += " (this week)"
            else:
                nextRun += " (next week)"
            return {
                "id":self.id,
                "group":self.group,
                "start_time":self.start_time.strftime("%H:%M:%S") if self.start_time is not None else "NA",
                "end_time": self.end_time.strftime("%H:%M:%S") if self.end_time is not None else "NA",
                "cut_off_time": self.cut_off_time.strftime("%H:%M:%S") if self.cut_off_time is not None else "NA",
                "interval": "%s sec" % self.interval if self.interval is not None else "NA",
                "days":", ".join(self.dayss),
                "exec":self.job.__name__,
                "execArgs":str(self.jobArgs),
                "nextRun":nextRun,
                "status":runStat
            }

        return dummy

    def calc_next_run(self):
        if self.interval is None and self.end_time is None:
            self._calc_next_run_one_time_job()
        else:
            self._calc_next_run()

    def _calc_next_run_one_time_job(self):
        print "-> one time job"

        self.next_run   = start_time = self.cut_off_time
        nowtime         = datetime.now().replace(year=1900, day=1, month=1)
        today_num       = datetime.now().weekday()
        d2c_thisWeek    = [d for d in self.days if d >= today_num]
        d2c_nextWeek    = [d for d in self.days if d < today_num]
        self.next_day   = None

        if len(d2c_thisWeek) > 0:
            if nowtime > start_time:
                if len(d2c_thisWeek) > 1:
                    self.calc_day(next_week=False, day=d2c_thisWeek[1])
                else:
                    if len(d2c_nextWeek) > 0:
                        self.calc_day(next_week=True, day=d2c_nextWeek[0])
                    else:
                        print "No valid days"
            else:
                self.calc_day(next_week=False, day=d2c_thisWeek[0])
        else:
            print "next week"

            if len(d2c_nextWeek) > 0:
                self.calc_day(next_week=True, day=d2c_nextWeek[0])
            else:
                print "No valid days"

    def _calc_next_run(self):
        self.next_run   = self.start_time
        nowtime         = datetime.now().replace(year=1900, day=1, month=1)
        today_num       = datetime.now().weekday()

        if nowtime > self.start_time:
            dt  = nowtime - self.start_time
            dtr = self.interval * (1 + floor(dt.total_seconds() / self.interval))
            nr  = self.start_time + timedelta(seconds=dtr)
            if nr > self.end_time:
                print "WARN: next run overshoots end time"
            self.next_run = nr
        else:
            self.next_run = self.start_time

        d2c_thisWeek = sorted([d for d in self.days if d >= today_num])
        d2c_nextWeek = sorted([d for d in self.days if d < today_num])
        self.next_day = None

        if len(d2c_thisWeek) > 0:
            if nowtime > self.end_time:
                if len(d2c_thisWeek) > 1:
                    self.calc_day(next_week=False, day=d2c_thisWeek[1])
                else:
                    if len(d2c_nextWeek) > 0:
                        self.calc_day(next_week=True, day=d2c_nextWeek[0])
                    else:
                        print "No valid days"
            else:
                self.calc_day(next_week=False, day=d2c_thisWeek[0])
        else:
            if len(d2c_nextWeek) > 0:
                self.calc_day(next_week=True, day=d2c_nextWeek[0])
            else:
                print "No valid days"

    def run(self):
        self.job(self.jobArgs)


class Schedular:
    def __init__(self, threaded=False, skip_unfinished_jobs=True):
        self.jobIndex       = 0
        self.threaded       = threaded
        self.jobs           = {}
        self.jobsByGroups   = {}
        self.groupPool      = {}         # allowing only one job at a time to be executed in a group
        self.groupCount     = {}         # count nr jobs running per group (testing, should be 1)
        self.skip_unfinished_jobs = skip_unfinished_jobs

    def schedule(self, job):
        if job.id is None:
            jobIndex = self.jobIndex
            self.jobIndex += 1
            job.id = jobIndex
        else:
            jobIndex = job.id

        if job.id in self.jobs.keys():
            print "WARNING: This job already exist, skipping"
            return

        group = job.group
        if group is None:
            group = "default"

        self.jobs[jobIndex] = job
        if group is not None:
            if group in self.jobsByGroups:
                self.jobsByGroups[group].append(job)
            else:
                self.jobsByGroups[group] = [job]
                self.groupCount[group] = 0
                self.groupPool[group] = Pool(processes=1)

        return jobIndex

    def onJobFinished(self, id):
        self.groupCount[self.jobs[id].group] -= 1
        print "stop ", id," [%s:%d]"%(self.jobs[id].group, self.groupCount[self.jobs[id].group] )

    def run_job(self, id):
        if self.jobs[id].group is None:
            if not self.jobs[id].job_thread.isAlive():
                print "running normal job", id
                self.jobs[id].job_thread = threading.Thread(target=self.jobs[id].job, args=[self.jobs[id].jobArgs])
                self.jobs[id].job_thread.start()
            else:
                print "skipping jobless job.id", id
        else:
            self.jobs[id].job_thread = self.groupPool[self.jobs[id].group].apply_async(self.jobs[id].job, (self.jobs[id].jobArgs,)) #, callback=self.onJobFinished)


    def clear(self, group=None, id=None):
        if id is not None and id in self.jobs.keys():
            del self.jobs[id]
            print "Job (%s) cleared by id" % (id)
        elif group is not None and group in self.jobsByGroups:
            for job in self.jobsByGroups[group]:
                if job.id in self.jobs:
                    del self.jobs[job.id]
                    print "Job (%s) cleared by group" % (job.id)

            self.jobsByGroups[group] = []
            self.groupCount[group] = []
            self.groupPool[group]=[]
        else:
            print "No such job with id:", id
            self.info()

    def start(self):
        if self.threaded:
            self._mainThread = threading.Thread(target=self._threaded)
            self._mainThread.start()
        else:
            self._threaded()

    def stop(self):
        self.running = False
        if self.threaded:
            self._mainThread.join()

    def check_jobs(self, by_group=False):
        if by_group:
            for group in sorted(self.jobsByGroups.keys()):
                print "\n- GROUP %s" % group
                for job in self.jobsByGroups[group]:
                    print "  %s" % (job.info())
        else:
            for id, job in self.jobs.iteritems():
                # print id,job.next_run, datetime.now(), job.next_run < datetime.now()
                if job.next_run is not None and job.next_run < datetime.now():
                    self.run_job(id)
                    job.calc_next_run()

    def _threaded(self):
        self.running = 1
        while self.running:
            time.sleep(1)
            self.check_jobs()

    def run_pending(self):
        for i, job in self.jobs.iteritems():
            print i, job.start

    def info(self, by_group=False):
        if len(self.jobs):
            print "[ JOBS at %s]" % datetime.now().strftime("%a %d-%m-%Y %H:%M:%S")

            if by_group:
                for group in sorted(self.jobsByGroups.keys()):
                    print "\n- GROUP %s"%group
                    for job in self.jobsByGroups[group]:
                        print "  %s" % (job.info())
            else:
                for id, job in self.jobs.iteritems():
                    if id != job.id:
                        print "! %s" % (job.info())
                    else:
                        print "  %s" % (job.info())
        else:
            print "No jobs."

    def as_json(self):
        print " * creating jobs as json"
        if len(self.jobs):
            return json.dumps([job.info(as_json=True) for id, job in self.jobs.iteritems()])
        else:
            print ""

def test_job(param):
    print param,"start",
    time.sleep(2)
    print "finished"

if __name__ == '__main__':
    schedular = Schedular(threaded=True, skip_unfinished_jobs=True)
    job1 = Job(start_time="10:00:00", end_time="18:33:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="1", group="cam2")
    job2 = Job(start_time="10:00:00", end_time="18:34:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="2", group="cam2")
    job3 = Job(start_time="10:00:00", end_time="18:35:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="3", group="cam2")
    job4 = Job(cut_off_time="16:00:00", days=["thu", "wed", "tue"], job=test_job, jobArgs="job4:once", group="cam1")
    schedular.schedule(job1)
    schedular.schedule(job2)
    schedular.schedule(job3)
    schedular.schedule(job4)
    schedular.info(by_group=True)
    schedular.start()
    time.sleep(3000000)
    schedular.stop()
    print "Done."
