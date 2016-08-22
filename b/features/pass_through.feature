Using step definitions from: 'pass_through/background', 'pass_through/push'

Feature: Creation of particular branch pipelines

    In order to achieve continuous integration ability for particular branch,
    As a developer
    I want to clone entire pipeline from mainline
    So that each line of code will be integrated correctly on particular branch.

    Background:
        Given connect to jenkins and git repository

    Scenario: Push to particular branch, then branch build will be triggered
        Given retrieve initialize build number
        When create a empty file called trigger_branch.txt, push to master branch
        Then onpush job will be triggered on Jenkins
        And job passthrough_test_build_master will be triggered on Jenkins
        And pushed hash value will be same as built in passthrough_test_build_master job