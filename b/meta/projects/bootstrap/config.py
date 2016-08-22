from os.path import join as jp
from multiconf.envs import EnvFactory

from data_object.project import Project
from data_object.git_object import Git, BootstrapGit
from data_object.git_object import FeatureBranchingModel
from data_object.virtualenv import VirtualEnv
from data_object.jenkins import DefaultJenkins
from data_object.jenkinsjobs import BaseJenkinsJobs, ProjectJenkinsJobs
from data_object.jenkinsviews import JenkinsNestedView, JenkinsListView

ef = EnvFactory()

devlocal = ef.Env('devlocal')
dev = ef.Env('dev')
valid_envs = [devlocal, dev]


def all_envs():
    return ef.EnvGroup('all', *valid_envs).envs()


def conf(env_name):
    env = ef.env(env_name)

    with Project(env, valid_envs=[devlocal, dev], name='ADMIN') as project:
        base_jobs = BaseJenkinsJobs(
                                    branch_regex='.*',
                                    )
        project_jobs = ProjectJenkinsJobs(jobs_path=jp('bootstrap', 'meta'),
                                          branch_regex='.*',
                                          use_shallow_clone=False)

        with DefaultJenkins(node='master') as jenkins:
            jenkins.setattr('workspace',
                            dev='/sabrebuild/jobs/ADMIN/workspace',
                            devlocal='/sabrebuild/jobs/ADMIN/workspace')
            jenkins.setattr('master_workspace',
                            dev='/sabrebuild/jobs/ADMIN/rebase-workspace',
                            devlocal='/sabrebuild/jobs/ADMIN/rebase-workspace')
            jenkins.setattr('url',
                            dev='http://sabrebuild1.'
                                'uk.standardchartered.com:8180/',
                            devlocal='http://sabrebuild1'
                                '.uk.standardchartered.com:8180/')
            jenkins.setattr('user_name', dev='1459847', devlocal='maleksey')
            jenkins.setattr('user_password',
                            dev='a3dc948b406a547fbb9f115ab02fd826',
                            devlocal='3d261f625cd6b0e5ed443aa36bf49ea7')
            # Remove this once main Jenkins is upgraded
            jenkins.setattr('version', dev='new', devlocal='old')

            with JenkinsNestedView('%s' % project.name) as top_view:
                # top_view.setattr('parent_path', devlocal='view/Parent')
                JenkinsListView('%s-repository' % project.name, jobs=base_jobs)
                JenkinsNestedView('%s-branches' % project.name,
                                  jobs=project_jobs)

        with BootstrapGit(branch_for_jobs='master') as bg:
            bg.setattr('branch_for_jobs', devlocal='develop')

        with Git(url=project.bootstrapgit.url,
            master_repo=jp(jenkins.master_workspace, project.name),
            branch_repo=jp(jenkins.workspace, project.name)) as git:
            FeatureBranchingModel()

        VirtualEnv(home='/home/sabredev/virtualenv/jenkins_bootstrap',
                   python_path='bootstrap/meta/py/lib/jenkins-job-builder')

        return project
