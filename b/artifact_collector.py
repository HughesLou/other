#!/bin/env python
"""
Usage:
    artifact_collector.py [--csv NAME] [--yaml NAME] [--fromfile NAME]

Options:
    --help                  This screen
    --csv NAME              generate csv file for all defined sabre projects
                            [default: projects.csv]
    --yaml NAME             dump all sabre projects build and release details
                            into yaml file [default: projects.yaml]
    --fromfile NAME         use given yaml file to generate the csv file.
"""
import csv
import sys
import yaml
import logging
import requests
from os import listdir
from docopt import docopt
from xml.etree import ElementTree
from xml.etree import ElementPath
from jenkinsapi.jenkins import Jenkins
from posixpath import isdir, join, isfile


logger = logging.getLogger(__name__)
JENKINS_URL = "http://sabrebuild1.uk.standardchartered.com:8080"
NEXUS_CLASS_QUERY_URL = 'http://sabrebuild1.uk.standardchartered.com:8081/' \
                        'nexus/service/local/data_index?q={class_name}'
BUILD_NAME = "{project}_1-BUILD_{branch}"
RELEASE_NAME = "{project}_2-RELEASE_{branch}"


def yaml_load(file_name):
    with open(file_name, 'r') as f:
        return yaml.load(f)


def yaml_dump(file_name, contents):
    with open(file_name, 'w') as f:
        yaml.safe_dump(contents, f, default_flow_style=False,
                       encoding='utf-8', indent=4, allow_unicode=True)


def artifact_exist(artifacts, name, key, path):
    for a in artifacts:
        if a[key] == name:
            return True, a[path]
    return False, None


def get_url_value(url, key=None):
    f = requests.get(url)
    if not key:
        return f.text
    for line in f.text.split('\n'):
        if key in line:
            return line.split('=')[1].strip()
    return ''


class JenkinsHelper(object):
    def __init__(self, jenkins_url=JENKINS_URL):
        self.jenkins = Jenkins(jenkins_url)

    def get_jenkins_job(self, job_name):
        try:
            job = self.jenkins[job_name]
            return True, job
        except Exception as e:
            logger.error("job %s not exist, Exception %s" % (job_name, str(e)))
            return False, None

    def get_job_last_good_build_details(self, job_name):
        build_details = {}
        res, job = self.get_jenkins_job(job_name)
        if not res:
            build_details['job_exist'] = False
            return build_details
        build_details['job_exist'] = True
        try:
            lgb = job.get_last_good_build()
            build_details['last_success_build'] = \
                {'build_num': lgb.buildno,
                 'artifacts': lgb._data['artifacts'],
                 'baseurl': lgb.baseurl}
            return build_details
        except Exception as e:
            logger.info("get last good build fails to Exception %s" % str(e))
            build_details['last_success_build'] = {}
            return build_details


class NexusChecker(object):
    def __init__(self, class_query=NEXUS_CLASS_QUERY_URL):
        self.class_query = class_query

    def class_exist(self, class_name):
        class_query = self.class_query.format(class_name=class_name)
        response = requests.get(class_query)
        if response.status_code != 200:
            logging.info("Can't get response from the url(%s)" % class_query)
            return False, None
        return True, response.text

    def check_class_gav(self, class_name):
        """
        return groupId, artifactId
        """
        class_query = self.class_query.format(class_name=class_name)
        res, content = self.class_exist(class_name)
        if not res:
            return "", ""
        doc = ElementTree.XML(content)
        try:
            a = ElementPath.find(doc, ".//artifact")
            return a.find("groupId").text, a.find("artifactId").text
        except Exception as e:
            logger.error("can't find groupId, artifactId through url:%s  "
                         "Exception %s" % (class_query, str(e)))
            return "", ""


class SabreProjects(object):
    def __init__(self, base_path='meta/projects', branch='master'):
        self.base_path = base_path
        self.branch = branch
        self.jenkins_helper = JenkinsHelper()
        self.nexus_checker = NexusChecker()

    def get_build_job_name(self, pro_name, branch=None):
        if not branch:
            branch = self.branch
        return BUILD_NAME.format(project=pro_name, branch=branch)

    def get_release_job_name(self, pro_name, branch=None):
        if not branch:
            branch = self.branch
        return RELEASE_NAME.format(project=pro_name, branch=branch)

    def get_all_projects(self):
        projects = [f for f in listdir(self.base_path)
                    if isdir(join(self.base_path, f)) and
                       isfile(join(self.base_path, f, 'project.yaml'))]
        return projects

    def add_gav(self, class_name, build_details):
        res, content = self.nexus_checker.class_exist(class_name)
        build_details['artifact_in_nexus'] = res
        if res:
            groupid, artifactid = \
                self.nexus_checker.check_class_gav(class_name)
            build_details['groupId'] = groupid
            build_details['artifactId'] = artifactid

    def get_project_build_release_details(self, pro_name):
        """
        get build and release last success build details
        """
        project_details = {}
        project_details['project_name'] = pro_name

        build_name = self.get_build_job_name(pro_name)
        build_ldb_details = \
            self.jenkins_helper.get_job_last_good_build_details(build_name)
        install_name = \
            self.get_project_install_name(pro_name, build_ldb_details)
        if install_name:
            self.add_gav(install_name, build_ldb_details)
        build_ldb_details['install_name'] = install_name
        project_details[build_name] = build_ldb_details

        release_name = self.get_release_job_name(pro_name)
        release_ldb_details = \
            self.jenkins_helper.get_job_last_good_build_details(release_name)
        release_url = \
            self.get_project_release_url(pro_name, release_ldb_details)
        if release_url:
            release_ldb_details['version'] = release_url.split('/')[-1]
        release_ldb_details['release_url'] = release_url
        project_details[release_name] = release_ldb_details

        return project_details

    def get_all_projects_build_release_details(self, projects=[]):
        projects_details = {}
        if not projects:
            projects = self.get_all_projects()
        for p in projects:
            projects_details[p] = self.get_project_build_release_details(p)
        return projects_details

    def get_project_install_name(self, pro_name, build_details=None,
                                 artifact='ReleaseManifest.txt',
                                 artifact_key='fileName',
                                 path_key='relativePath',
                                 key='APPLICATION_INSTALL_NAME'):
        build_name = self.get_build_job_name(pro_name)
        if not build_details:
            project_details = self.get_project_build_release_details(pro_name)
            build_details = project_details[build_name]
        if build_details['job_exist'] and build_details['last_success_build']:
            lgb = build_details['last_success_build']
            res, path = artifact_exist(lgb['artifacts'], artifact,
                                       artifact_key, path_key)
            if res:
                a_url = '%s/artifact/%s' % (lgb['baseurl'], path)
                return get_url_value(a_url, key).strip()
        return ''

    def get_project_release_url(self, pro_name, release_details=None,
                                artifact='ReleaseURL.txt',
                                artifact_key='fileName',
                                path_key='relativePath'):
        release_name = self.get_release_job_name(pro_name)
        if not release_details:
            project_details = self.get_project_build_release_details(pro_name)
            release_details = project_details[release_name]
        if release_details['job_exist'] and \
                release_details['last_success_build']:
            lgb = release_details['last_success_build']
            res, path = artifact_exist(lgb['artifacts'], artifact,
                                       artifact_key, path_key)
            if res:
                a_url = '%s/artifact/%s' % (lgb['baseurl'], path)
                return get_url_value(a_url)
        return ''

    def generate_build_csv_fields(self, pro_name, build):
        fields = []
        build_job = self.get_build_job_name(pro_name)
        if not build['job_exist'] or build['job_exist'] == 'false':
            return [build_job+": false", "", "", "", ""]
        fields.append(build_job+": true")
        if build['install_name']:
            arti = build['install_name']
            art = arti + ': true' if build['artifact_in_nexus'] else \
                arti + ': false'
        else:
            art = ""
        if build["last_success_build"]:
            lgb = build["last_success_build"]
            fields.append(lgb['build_num'])
            fields.append(art)
            if 'groupId' in build.keys():
                fields.append(build['groupId'])
                fields.append(build['artifactId'])
            else:
                fields.extend(["", ""])
        else:
            fields.extend(["", art, "", ""])
        return fields

    def generate_release_csv_fields(self, pro_name, release):
        fields = []
        release_job = self.get_release_job_name(pro_name)
        if not release['job_exist'] or release['job_exist'] == 'false':
            return [release_job+": false", "", "", ""]
        fields.append(release_job+": true")
        if release["last_success_build"]:
            lgb = release["last_success_build"]
            fields.append(lgb['build_num'])
            if 'version' in release.keys():
                fields.append(release['version'])
                fields.append(release['release_url'])
            else:
                fields.extend(["", ""])
        else:
            fields.extend(["", "", ""])
        return fields

    def generate_csv(self, projects_details=None, file_name='projects.csv'):
        fieldnames = ["Project", "Master_build: exists",
                      "Last_successful_build", "Artefact: in_nexus", "GroupId",
                      "ArtefactId", "Master_release: exists",
                      "Last_successful_release", "Release_version",
                      "Release_url"]
        if not projects_details:
            projects_details = self.get_all_projects_build_release_details()
        with open(file_name, 'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(fieldnames)
            for p in self.get_all_projects():
                fields = []
                build_job = self.get_build_job_name(p)
                release_job = self.get_release_job_name(p)
                fields.append(p)  # Project
                build = projects_details[p][build_job]
                fields.extend(self.generate_build_csv_fields(p, build))
                release = projects_details[p][release_job]
                fields.extend(self.generate_release_csv_fields(p, release))
                csv_writer.writerow(fields)


if __name__ == '__main__':
    args = docopt(__doc__, version='1.0')
    loglevel = 'INFO'
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=loglevel)
    try:
        sabre = SabreProjects()
        csv_file = args['--csv'] if args['--csv'].endswith('.csv')\
            else args['--csv'] + '.csv'
        yaml_file = args['--yaml'] if args['--yaml'].endswith('.yaml')\
            else args['--yaml'] + '.yaml'
        if args['--fromfile']:
            proj_details = yaml_load(args['--fromfile'])
        else:
            proj_details = sabre.get_all_projects_build_release_details()
        yaml_dump(yaml_file, proj_details)
        sabre.generate_csv(file_name=csv_file, projects_details=proj_details)
    except Exception as ex:
        logger.error(str(ex))
        sys.exit(1)