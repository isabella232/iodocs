import getpass
import os
import sys

from fabric.api import run, local, cd, env, roles, execute
import requests

CODE_DIR = '/home/deploy/www/iodocs'

env.roledefs = {
    'web': ['web1'],
}


def deploy():
    # pre-roll checks
    check_user()

    # do a local git pull, so the revision # when we record the deploy is correct
    local("git pull")

    # do the roll.
    # execute() will call the passed-in function, honoring host/role decorators.
    execute(update_and_restart)

    # post-roll tasks
    #ratchet_record_deploy()


@roles('web')
def update_and_restart():
    with cd(CODE_DIR):
        run("git pull")
        run("npm install")
        run("supervisorctl restart iodocs")


def check_user():
    if getpass.getuser() != 'deploy':
        print "This command should be run as deploy. Run like: sudo -u deploy fab deploy"
        sys.exit(1)


def ratchet_record_deploy():
    # read access_token from production.ini
    access_token = local("grep 'ratchet.access_token' production.ini | sed 's/^.* = //g'", capture=True)

    environment = 'production'
    local_username = local('whoami', capture=True)
    revision = local('git log -n 1 --pretty=format:"%H"', capture=True)

    resp = requests.post('https://submit.ratchet.io/api/1/deploy/', {
        'access_token': access_token,
        'environment': environment,
        'local_username': local_username,
        'revision': revision
    }, timeout=3)

    if resp.status_code == 200:
        print "Deploy recorded successfully. Deploy id:", resp.json['result']['id']
    else:
        print "Error recording deploy:", resp.text


