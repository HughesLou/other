Using step definitions from: 'feature_branch/background', 'feature_branch/create_branch', 'feature_branch/push_branch', 'feature_branch/push_master'

Feature: Creation of feature branch pipelines

    In order to achieve continuous integration ability for new feature branch,
    As a developer
    I want to clone entire pipeline from mainline
    So that each line of code will be integrated correctly on feature branch.

    Background:
        Given connect to jenkins and git repository
        And create a new branch called develop, then push to this branch

    Scenario: Create a new branch and push it, then the entire pipeline will apply for this branch
        Given retrieve initialize build number
        Then onpush job will be triggered on Jenkins
        And create-jobs job will be triggered on Jenkins
        And feature_branch_test_build_develop job will be created on Jenkins
        And job feature_branch_test_build_develop will be triggered on Jenkins

    Scenario: Push to develop branch, then branch build will be triggered
        Given retrieve initialize branch build number
        When create a empty file called trigger_branch.txt, push to develop branch
        Then onpush job will be triggered on Jenkins
        And job feature_branch_test_build_develop will be triggered on Jenkins

    Scenario: Push to master branch, then rebase job will be triggered
        Given retrieve initialize rebase build number
        When create a file called trigger_master.txt in master, push to master branch
        Then onpush job will be triggered on Jenkins
        And rebase job will be triggered on Jenkins
        And delete trigger_master.txt file on master after test