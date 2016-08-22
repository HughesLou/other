import time

from os.path import join
from freshen import Given, Then, scc, When
from hamcrest import assert_that, greater_than, greater_than_or_equal_to, is_


@Given('retrieve initialize build number')
def prepare():
    _initialize()


@When('create a empty file called (.*), push to (\w+) branch')
def push(filename, branch):
    open(join(scc.project_path, filename), 'w').close()
    scc.git.push(branch, 'create trigger branch file.')


@Then('onpush job will be triggered on Jenkins')
def trigger_onpush():
    _should_trigger_onpush()


@Then('job passthrough_test_build_master will be triggered on Jenkins')
def trigger_build():
    _should_trigger_branch_build()


@Then('pushed hash value will be same as built in passthrough_test_build_master job')
def compare_reversion():
    pushed_hash = scc.git.latest_reversion()
    built_hash = scc.build_job.get_last_build().get_revision()
    assert_that(built_hash, is_(pushed_hash))


def _initialize():
    try:
        scc.onpush_job_pre_trigger_number = scc.onpush_job.get_last_buildnumber()
        scc.build_job = scc.jenkins.get_job('passthrough_test_build_master')
        scc.build_job_pre_trigger_number = scc.build_job.get_last_buildnumber()

    except:
        scc.onpush_job_pre_trigger_number = 0
        scc.build_job_pre_trigger_number = 0


def _should_trigger_onpush():
    time.sleep(30)
    while scc.onpush_job.is_queued_or_running():
        time.sleep(10)
    onpush_job_post_trigger_number = scc.onpush_job.get_last_buildnumber()
    assert_that(onpush_job_post_trigger_number,
                greater_than(scc.onpush_job_pre_trigger_number),
                'should trigger onpush')


def _should_trigger_branch_build():
    if scc.build_job.is_queued_or_running():
        time.sleep(10)
    build_job_post_trigger_number = scc.build_job.get_last_buildnumber()
    assert_that(build_job_post_trigger_number,
                greater_than(scc.build_job_pre_trigger_number),
                'should trigger branch build')