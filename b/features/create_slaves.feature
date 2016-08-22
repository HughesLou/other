Using step definitions from: 'create_slaves/background', 'create_slaves/create_slave'

Feature: Creation of jenkins slaves from definition in project.yaml

    In order to achieve continuous integration ability for new feature branch,
    As a developer
    I want to be able to define slaves in project.yaml
    So slaves will be automatically created in jenkins

    Background:
        Given connect to jenkins
        Given slave BDD_create_new_slave__test_slave does not exist in Jenkins
        Given credentials with description BDD_create_new_slave__sabredev does not exist in Jenkins
        Given create-jobs job is triggered on Jenkins

    Scenario: Create new slave
        Then slave BDD_create_new_slave__test_slave will be created in Jenkins
        And credentials with description BDD_create_new_slave__sabredev will be created in Jenkins

    # Scenario: Push to develop branch, then branch build will be triggered
    #     Given retrieve initialize branch build number
    #     When create a empty file called trigger_branch.txt, push to develop branch
    #     Then onpush job will be triggered on Jenkins
    #     And job feature_branch_test_build_develop will be triggered on Jenkins

    # Scenario: Push to master branch, then rebase job will be triggered
    #     Given retrieve initialize rebase build number
    #     When create a file called trigger_master.txt in master, push to master branch
    #     Then onpush job will be triggered on Jenkins
    #     And rebase job will be triggered on Jenkins
    #     And delete trigger_master.txt file on master after test
