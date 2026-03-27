"""
Scheduler Module
"""

import threading
import time
import logging
import schedule


def run_threaded(job):
    """
    Helper method to run a method in a thread
    """
    job_thread = threading.Thread(target=job)
    job_thread.start()


class Scheduler(threading.Thread):
    """
    Scheduler Class
    """

    def __init__(self):
        super(Scheduler, self).__init__()
        self.daemon = True
        self._is_interrupted = False
        self._is_running = False
        self.jobs = {}

    def add_schedule(self, period, job, name):
        """
        Adds a job to the schedule to be executed at the defined period
        """
        self.jobs[name] = schedule.every(period).seconds.do(run_threaded, job)
        logging.debug("Added new job: %s", name)

    def cancel_schedule(self, name):
        """
        Cancels a scheduled job by name
        """
        schedule.cancel_job(self.jobs[name])
        logging.debug("Cancelled job: %s", name)

    def run_job(self, name):
        """
        Run a job by name
        """
        self.jobs[name].run()

    def run_all_jobs(self):
        """
        Run all jobs in the schedule
        """
        schedule.run_all()

    def get_jobs(self):
        """
        Retrieve a schedule job object by name
        """
        return schedule.get_jobs()

    def run(self):
        """
        Start the schedule
        """
        self._is_running = True
        while not self._is_interrupted:
            schedule.run_pending()
            time.sleep(.05)
        self._is_running = False

    def stop(self):
        """
        Stop the schedule
        """
        self._is_interrupted = True
        while self._is_running:
            time.sleep(.01)
        for _, job in self.jobs.items():
            schedule.cancel_job(job)
