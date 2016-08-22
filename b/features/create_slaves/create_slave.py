import time

from fresher import Given, Then, scc
# from hamcrest import has_item, is_not, assert_that


@Given('slave (\w+) does not exist in Jenkins')
def verify_slave(slave_name):
    scc.slave_name = slave_name
    assert(slave_name not in scc.jenkins.nodes)


@Given('credentials with description (\w+) does not exist in Jenkins')
def verify_creds(cred_descr):
    scc.cred_descr = cred_descr
    assert(cred_descr not in scc.jenkins.credentials)


@Given('create-jobs job is triggered on Jenkins')
def trigger_onpush():
    scc.create_jobs.invoke()
    while scc.create_jobs.is_queued_or_running():
        time.sleep(5)


@Then('slave (\w+) will be created in Jenkins')
def check_created_slave(slave_name):
    assert(slave_name in scc.jenkins.nodes)


@Then('credentials with description (\w+) will be created in Jenkins')
def check_created_credentials(cr_description):
    assert(cr_description in scc.jenkins.credentials)
