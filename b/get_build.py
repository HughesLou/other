from jenkinsapi import jenkins
from jenkinsapi import build
import logging

logger = None
logging.basicConfig(level='DEBUG')
logger = logging.getLogger()
api = jenkins.Jenkins('http://sabrebuild1.uk.standardchartered.com:8180', 'maleksey', 
        password='llimejib')

b = build.Build('http://sabrebuild1.uk.standardchartered.com:8180/job/ADMIN-flow-1/14', 14, api.get_job('ADMIN-flow-1'))
print b.get_actions()
