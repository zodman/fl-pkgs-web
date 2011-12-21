import os, urllib2
from xml.etree import ElementTree

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def log(msg):
    print msg

class Package:
    def __init__(self, xmlelement):
        self.name = xmlelement.find("name").text
        self.revision = xmlelement.find("version").find("revision").text
        self.trovelist = xmlelement.find("trovelist").get("id")

def fetch_api_data(api, dest):
    '''Reading from url @api, and write to file @dest
    '''
    log("reading %s" % urllib2.unquote(api))
    u = urllib2.urlopen(api)
    content = u.read()
    u.close()

    log("writing %s" % dest)
    f = open(dest + ".new", "w")
    f.write(content)
    f.close()
    os.rename(dest + ".new", dest)

    return content

def parse_pkg_list(xml):
    '''Read a <nodelist> and return a list of pkgs contained within
    '''
    ret = [Package(e) for e in ElementTree.XML(xml)]
    # drop nil pkgs
    ret = [p for p in ret if not p.revision.startswith("0-")]
    return ret

def clean_cache(cachedir, pkgs):
    tokeep = ["%s-%s" % (p.name, p.revision) for p in pkgs]
    allfiles = os.listdir(cachedir)
    for f in set(allfiles) - set(tokeep):
        t = "%s/%s" % (cachedir, f)
        log("removing %s" % t)
        os.remove(t)

def refresh_pkg_info(pkgs, cachedir):
    '''Fetch detailed info about a pkg, from the 'trovelist' of the node
    '''
    for pkg in pkgs:
        f = "%s/%s-%s" % (cachedir, pkg.name, pkg.revision)
        if not os.path.exists(f):
            fetch_api_data(pkg.trovelist, f)
    clean_cache(cachedir, pkgs)

def refresh_pkg_list(api_site, label, cachedir):
    '''Fetch the list of pkgs, called 'nodes' in conary REST API.
    '''
    api = "%s/node?label=%s&type=package&type=group" % (api_site, label)
    dest = "%s/%s" % (cachedir, label)
    content = fetch_api_data(api, dest)

    pkgs = parse_pkg_list(content)
    destdir = "%s/%s" % (cachedir, label.split("@")[-1])
    mkdir(destdir)
    refresh_pkg_info(pkgs, destdir)

def refresh_source_list(api_site, label, cachedir):
    api = "%s/node?label=%s&type=source" % (api_site, label)
    dest = "%s/source-%s" % (cachedir, label)
    fetch_api_data(api, dest)

def main():
    api_site = "http://conary.foresightlinux.org/conary/api"

    labels = [
        "foresight.rpath.org@fl:2",
        "foresight.rpath.org@fl:2-kernel",
        "foresight.rpath.org@fl:2-qa",
        "foresight.rpath.org@fl:2-qa-kernel",
        ]

    cache = "rawdata"
    mkdir(cache)
    for b in labels:
        refresh_source_list(api_site, b, cache)
        refresh_pkg_list(api_site, b, cache)

if __name__ == "__main__":
    main()
