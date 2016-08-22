from git import Repo


class Git(object):
    def __init__(self, path):
        repo = Repo(path)
        self._git = repo.git

    def create_branch(self, branch):
        self._git.checkout('master')
        if self.has_branch(branch):
            return
        self._git.branch(branch)
        self._git.checkout(branch)
        self._git.push('origin', branch)

    def delete_branch(self, branch):
        self._git.checkout('master')
        self._git.branch('-D', branch)
        self._git.push('origin', ':%s' % branch)

    def push(self, branch, message):
        self._git.checkout(branch)
        self._git.add('*')
        if message is None:
            message = 'autocommit'
        self._git.commit('-a', '-m %s' % message)
        self._git.push('origin', branch)

    def delete(self, filename):
        self._git.rm(filename)

    def checkout(self, name):
        self._git.checkout(name)

    def has_branch(self, branch):
        return 'origin/%s' % branch in self._git.branch('-r')

    def latest_reversion(self):
        return self._git.rev_parse('HEAD')
