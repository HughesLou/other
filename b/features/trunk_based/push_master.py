from os.path import join

from freshen import Given, When, scc, Then
from hamcrest import assert_that, greater_than

import time


@Given('retrieve initialize rebase build number')
def prepare():
    _initialize()


@When('create a file called (.*) in master, push to (.*) branch')
def push(filename, branch):
    scc.git.checkout(branch)
    open(join(scc.project_path, filename), 'w').close()
    scc.git.push(branch, 'create trigger master file.')


@Then('job trunkbased_test_build_master will be triggered on Jenkins')
def trigger_build():
    _should_trigger_branch_build()


@Then('delete (.*) file on (.*) after test')
def delete_file(filename, branch):
    scc.git.delete(filename)
    scc.git.push(branch, 'delete trigger file after test.')


def _initialize():
    try:
        scc.onpush_job_pre_trigger_number = scc.onpush_job.get_last_buildnumber()
        scc.build_job = scc.jenkins.get_job('trunkbased_test_build_master')
        scc.build_job_pre_trigger_number = scc.build_job.get_last_buildnumber()
    except:
        scc.onpush_job_pre_trigger_number = 0
        scc.build_job_pre_trigger_number = 0


def _should_trigger_branch_build():
    if scc.build_job.is_queued_or_running():
        time.sleep(10)
    build_job_post_trigger_number = scc.build_job.get_last_buildnumber()
    assert_that(build_job_post_trigger_number,
                greater_than(scc.build_job_pre_trigger_number),
                'should trigger branch build')
