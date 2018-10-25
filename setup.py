import setuptools
from setuptools import setup


# pip install wheel twine
# python setup.py sdist bdist_wheel
# twine upload dist/*


setup(
    name="schedular",
    version="1.0.4",
    author="Morgan NoXQS Heijdemann",
    author_email="targhan@gmail.com",
    description="Schedular is here to schedule jobs by cut off time or jobs that require start+end+interval.",
    long_description="""
    # Schedular

Schedular is a Python 2 scheduling library to create two types of jobs:
 - Jobs running at certain interval at certain days from start time till end time
 - Jobs that are triggered at a specific time of a specific day
# Features
  - Jobs can be put into groups which ensures sequencial execution of these jobs withing each group.
  - Jobs not in any group will be run parallel.


# Examples

```py
from schedular import Schedular, Job

def test_job(param):
    print param,"start",
    time.sleep(2)
    print "finished"
    
schedular = MyScheduler(threaded=True, skip_unfinished_jobs=True)
job1 = Job(start_time="10:00:00", end_time="15:33:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="1", group="cam2")
job2 = Job(start_time="10:00:00", end_time="15:34:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="2", group="cam2")
job3 = Job(start_time="10:00:00", end_time="15:35:00", days=["thu", "wed", "tue"], interval="10s", job=test_job, jobArgs="3", group="cam2")
job4 = Job(cut_off_time="16:00:00", days=["thu", "wed", "tue"], job=test_job, jobArgs="job4:once", group="cam1")
schedular.schedule(job1)
schedular.schedule(job2)
schedular.schedule(job3)
schedular.schedule(job4)
schedular.info(by_group=True)
schedular.start()
time.sleep(3000000)
schedular.stop()
```
gives output:
```
[ JOBS at Wed 24-10-2018 15:59:51]

- GROUP cam1
   ID:3 DAYS:thu, wed, tue ST:NONE ET:NONE INT:NONE JOB:test_job(job4:once), NEXT: Thu 25-10-2018 16:00:00 (this week)[ACTIVE]

- GROUP cam2
   ID:0 DAYS:thu, wed, tue ST:10:00:00 ET:18:33:00 INT:10s. JOB:test_job(1), NEXT: Wed 24-10-2018 16:00:00 (this week) [ACTIVE]
   ID:1 DAYS:thu, wed, tue ST:10:00:00 ET:18:34:00 INT:10s. JOB:test_job(2), NEXT: Wed 24-10-2018 16:00:00 (this week) [ACTIVE]
   ID:2 DAYS:thu, wed, tue ST:10:00:00 ET:18:35:00 INT:10s. JOB:test_job(3), NEXT: Wed 24-10-2018 16:00:00 (this week) [ACTIVE]
1 start finished
2 start finished
3 start finished
```

Although released as 1.0, there might be bugs. Don't use this is production software. 
Github project at https://github.com/noxqs/schedular

Licensed under the MIT License, enjoy""",
    long_description_content_type="text/markdown",
    url="https://github.com/noxqs/schedular",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT License'
)

