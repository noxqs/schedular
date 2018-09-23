from myscheduler import MyScheduler, Job

schedular = MyScheduler()

def test_job():
    print "run test job"

job1=Job(start_time="17:50:00", end_time="19:10:00", days=[6,0], interval="5m", job=test_job, jobArgs="aap" )
job1.info()
