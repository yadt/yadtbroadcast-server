from pybuilder.core import use_plugin, init, Author

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("python.unittest")
use_plugin("python.flake8")
use_plugin("python.frosted")

use_plugin("copy_resources")

default_task = ["analyze", "verify", "publish"]

name    = "yadtbroadcast-server"
version = "1.1"
summary = "Yet Another Deployment Tool - The BroadcastServer Part"
description = '''Yet Another Deployment Tool - The BroadcastServer Part
- provides channels for publish/subscribe
- handles messages form yadtbroadcast-client
- caches state information for newly connecting clients

for more documentation, visit http://www.yadt-project.org/
'''
authors = [Author("Arne Hilmann", "arne.hilmann@gmail.com")]

url = "https://github.com/yadt/yadtbroadcast-service"
license = "GNU GPL v3"

@init
def set_properties (project):
    project.build_depends_on("mock")

    project.depends_on("Twisted")
    project.depends_on("autobahn")
    project.depends_on("simplejson")

    project.set_property("verbose", True)

    project.get_property("distutils_commands").append("bdist_rpm")
    project.set_property("copy_resources_target", "$dir_dist")
    project.get_property("copy_resources_glob").append("setup.cfg")
    project.set_property('dir_dist_scripts', 'scripts')

    project.set_property("distutils_classifiers", [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration'
    ])

@init(environments='teamcity')
def set_properties_for_teamcity_builds (project):
    import os
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['install_build_dependencies', 'publish']


