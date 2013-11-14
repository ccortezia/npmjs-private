import os
from fabric.utils import abort
from fabric.api import run, sudo, local, task, env
from fabric.context_managers import cd, prefix, lcd, settings
from fabric.contrib.files import exists
from fabric.operations import put

HERE = os.path.dirname(os.path.abspath(__file__))
COUCHDB_PROJNAME = 'apache-couchdb'
COUCHDB_VERSION = '1.5.0'
COUCHDB_DIRNAME = '%s-%s' % (COUCHDB_PROJNAME, COUCHDB_VERSION)
COUCHDB_FILENAME = '%s-%s.tar.gz' % (COUCHDB_PROJNAME, COUCHDB_VERSION)
COUCHDB_URL = 'http://ftp.unicamp.br/pub/apache/couchdb/source/%s/%s' % (COUCHDB_VERSION, COUCHDB_FILENAME)
COUCHDB_LOCAL_INI = os.path.join(HERE, 'local.ini')
COUCHDB_REMOTE_INI = '/usr/local/etc/couchdb/local.ini'

NODE_VERSION = '0.10'

def user_exists(username):
  with settings(warn_only=True):
    result = run("grep %s /etc/passwd" % username)
    return result.return_code == 0


@task
def build():
  with cd('/tmp'):
    if not exists(COUCHDB_FILENAME):
      run('wget %s' % COUCHDB_URL)
    if not exists(COUCHDB_DIRNAME):
      run('tar xfv %s' % COUCHDB_FILENAME)
    with cd(COUCHDB_DIRNAME):
      run('./configure')
      run('make')
      sudo('make install')
    #sudo('rm -rf %s' % COUCHDB_DIRNAME)

@task
def configure():
  if not user_exists('couchdb'):
    sudo('adduser --disabled-login --disabled-password --no-create-home --gecos "CouchDB Admin" couchdb')
  sudo('chown -R couchdb:couchdb /usr/local/var/{log,lib,run}/couchdb')
  sudo('chown -R couchdb:couchdb /usr/local/etc/couchdb/local.ini')
  sudo('ln -sf /usr/local/etc/init.d/couchdb /etc/init.d')
  sudo('update-rc.d couchdb defaults')
  put(COUCHDB_LOCAL_INI, COUCHDB_REMOTE_INI, use_sudo=True)


@task
def restart():
  sudo('service couchdb restart')


def on_active_nvm(cmd):
  return 'source /home/%s/.profile; %s' % (env.user, cmd)

def on_active_npm(cmd):
  return on_active_nvm('nvm use %s; %s' % (NODE_VERSION, cmd))

@task
def nvm():
  if not exists('/home/%s/.nvm/' % env.user):
    with cd('/tmp'):
      run('wget -qO- https://raw.github.com/creationix/nvm/master/install.sh | sh')
  run(on_active_nvm('nvm install %s' % NODE_VERSION))


@task
def npmjs():
  with cd('/tmp'):
    if not exists('npmjs.org'):
      run('git clone git://github.com/isaacs/npmjs.org.git')
    with cd('npmjs.org'):
      run(on_active_npm('npm install -g couchapp'))
      run(on_active_npm('npm install couchapp'))
      run(on_active_npm('npm install semver'))
      run(on_active_npm('couchapp push registry/app.js http://localhost:5984/registry'))
      run(on_active_npm('couchapp push www/app.js http://localhost:5984/registry'))


@task
def deps():
  sudo('apt-get update')
  sudo('apt-get install -y build-essential')
  sudo('apt-get install -y autoconf')
  sudo('apt-get install -y automake')
  sudo('apt-get install -y libtool')
  sudo('apt-get install -y erlang')
  sudo('apt-get install -y libicu-dev')
  sudo('apt-get install -y libmozjs-dev')
  sudo('apt-get install -y libcurl4-openssl-dev')
  sudo('apt-get install -y git-core')


@task(default=True)
def full():
  deps()
  build()
  configure()
  restart()
