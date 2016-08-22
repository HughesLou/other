from freshen import Given, scc, After
from hamcrest import assert_that, is_
from features.utils.git_helper import Git
from jenkinsapi.jenkins import Jenkins


@Given('connect to jenkins and git repository')
def setup():
    scc.jenkins = Jenkins('http://sabrebuild1.uk.standardchartered.com:8080/',
                          '1466811', 'cc17bc107d6e1ca2638058a0d7be38a4')
    scc.onpush_job = scc.jenkins.get_job('%s_onpush' % 'feature_branch_test')
    scc.create_jobs = scc.jenkins.get_job('%s_create-jobs' % 'feature_branch_test')
    scc.rebase_job = scc.jenkins.get_job('%s_rebase' % 'feature_branch_test')
    scc.project_path = '/shared/opt/jenkins-home/master-repos/feature_branch_test'
    scc.git = Git(scc.project_path)


@Given('create a new branch called (\w+), then push to this branch')
def create_branch(branch):
    scc.git.create_branch(branch)


@After()
def after(sc):
    _should_delete_branch_after_test('develop')


def _should_delete_branch_after_test(branch):
    scc.git.delete_branch(branch)
    assert_that(scc.git.has_branch(branch), is_(False),
                'should delete branch after test')