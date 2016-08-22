from freshen import Given, scc, After
from features.utils.git_helper import Git
from jenkinsapi.jenkins import Jenkins


@Given('connect to jenkins and git repository')
def setup():
    scc.jenkins = Jenkins('http://sabrebuild1.uk.standardchartered.com:8080/',
                          '1466811', 'cc17bc107d6e1ca2638058a0d7be38a4')
    scc.onpush_job = scc.jenkins.get_job('%s_onpush' % 'passthrough_test')
    scc.project_path = '/shared/opt/jenkins-home/master-repos/passthrough_test'
    scc.git = Git(scc.project_path)


@After()
def after(sc):
    scc.git.delete('trigger_branch.txt')
    scc.git.push('master', 'delete trigger file after test.')