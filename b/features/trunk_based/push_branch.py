from os.path import join
from freshen import Given, When, scc


@Given('retrieve initialize branch build number')
def prepare():
    _initialize()


@When('create a empty file called (.*), push to (\w+) branch')
def push(filename, branch):
    scc.git.checkout(branch)
    open(join(scc.project_path, filename), 'w').close()
    scc.git.push(branch, 'create trigger branch file.')


def _initialize():
    scc.branch_build = scc.jenkins.get_job('trunkbased_test_build_develop')
    try:
        scc.onpush_job_pre_trigger_number = scc.onpush_job.get_last_buildnumber()
        scc.branch_build_pre_trigger_number = scc.branch_build.get_last_buildnumber()
    except:
        scc.onpush_job_pre_trigger_number = 0
        scc.branch_build_pre_trigger_number = 0
