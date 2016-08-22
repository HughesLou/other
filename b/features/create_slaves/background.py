from fresher import Given, scc, After
from hamcrest import assert_that, is_
from features.utils.git_helper import Git
from jenkinsapi.jenkins import Jenkins


@Given('connect to jenkins')
def setup():
    scc.jenkins = Jenkins('http://sabrebuild1.uk.standardchartered.com:8180/',
                          'maleksey', '3d261f625cd6b0e5ed443aa36bf49ea7')
    scc.create_jobs = scc.jenkins.get_job('%s_create-jobs' % 'BDD_create_new_slave')


@After()
def cleanup(sc):
    if scc.slave_name in scc.jenkins.nodes:
        del scc.jenkins.nodes[scc.slave_name]

    if scc.cred_descr in scc.jenkins.credentials:
        del scc.jenkins.credentials[scc.cred_descr]
