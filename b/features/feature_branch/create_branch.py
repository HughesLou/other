import time

from freshen import Given, Then, scc
from hamcrest import assert_that, is_, greater_than, greater_than_or_equal_to


@Given('retrieve initialize build number')
def prepare():
    _initialize()


@Then('onpush job will be triggered on Jenkins')
def trigger_onpush():
    _should_trigger_onpush()


@Then('create-jobs job will be triggered on Jenkins')
def trigger_create_jobs():
    _should_trigger_create_jobs()


@Then('(\w+) job will be created on Jenkins')
def jobs_views_exist(job_name):
    _should_create_branch_jobs_and_views(job_name)


@Then('job feature_branch_test_build_develop will be triggered on Jenkins')
def trigger_build():
    _should_trigger_branch_build()


def _initialize():
    try:
        scc.onpush_job_pre_trigger_number = scc.onpush_job.get_last_buildnumber()
        scc.create_jobs_job_pre_trigger_number = scc.create_jobs.get_last_buildnumber()

    except:
        scc.onpush_job_pre_trigger_number = 0
        scc.create_jobs_job_pre_trigger_number = 0

    try:
        scc.branch_build = scc.jenkins.get_job('feature_branch_test_build_develop')
        scc.branch_build_pre_trigger_number = scc.branch_build.get_last_buildnumber()
    except:
        scc.branch_build_pre_trigger_number = 0


def _should_trigger_onpush():
    time.sleep(30)
    while scc.onpush_job.is_queued_or_running():
        time.sleep(10)
    onpush_job_post_trigger_number = scc.onpush_job.get_last_buildnumber()
    assert_that(onpush_job_post_trigger_number,
                greater_than(scc.onpush_job_pre_trigger_number),
                'should trigger onpush')


def _should_trigger_create_jobs():
    while scc.create_jobs.is_queued_or_running():
        time.sleep(10)
    create_jobs_job_post_trigger_number = scc.create_jobs.get_last_buildnumber()
    assert_that(create_jobs_job_post_trigger_number,
                greater_than(scc.create_jobs_job_pre_trigger_number),
                'should trigger create jobs')


def _should_create_branch_jobs_and_views(job_name):
    assert_that(scc.jenkins.has_job(job_name), is_(True),
                'should create branch jobs and views')


def _should_trigger_branch_build():
    if scc.branch_build.is_queued_or_running():
        time.sleep(10)
    branch_build_post_trigger_number = scc.branch_build.get_last_buildnumber()
    assert_that(branch_build_post_trigger_number,
                greater_than(scc.branch_build_pre_trigger_number),
                'should trigger branch build')
