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

def parse_pkg_list(xml):
    ret = [Package(e) for e in ElementTree.XML(xml)]
    ret = [p for p in ret if not p.revision.startswith("0-")]
    return ret

def fetch_api_data(api):
    log("reading %s" % urllib2.unquote(api))
    u = urllib2.urlopen(api)
    content = u.read()
    u.close()
    return content

def write_api_data(content, dest):
    log("writing %s" % dest)
    f = open(dest + ".new", "w")
    f.write(content)
    f.close()
    os.rename(dest + ".new", dest)

# pkgs
def refresh_pkg_list(api_site, label, cachedir):
    content = fetch_api_data("%s/node?label=%s&type=package" % (api_site, label))
    write_api_data(content, "%s/%s" % (cachedir, label))

    pkgs = parse_pkg_list(content)
    destdir = "%s/%s" % (cachedir, label.split("@")[-1])
    mkdir(destdir)
    refresh_pkg_info(pkgs, destdir)

# source
def refresh_source_list(api_site, label, cachedir):
    content = fetch_api_data("%s/node?label=%s&type=source" % (api_site, label))
    write_api_data(content, "%s/source-%s" % (cachedir, label))

# pkg info
def refresh_pkg_info(pkgs, cachedir):
    for pkg in pkgs:
        f = "%s/%s-%s" % (cachedir, pkg.name, pkg.revision)
        if not os.path.exists(f):
            content = fetch_api_data(pkg.trovelist)
            write_api_data(content, f)
    clean_cache(cachedir, pkgs)

def clean_cache(cachedir, pkgs):
    tokeep = ["%s-%s" % (p.name, p.revision) for p in pkgs]
    allfiles = os.listdir(cachedir)
    for f in set(allfiles) - set(tokeep):
        t = "%s/%s" % (cachedir, f)
        log("removing %s" % t)
        os.remove(t)

def main():
    api_site = "http://conary.foresightlinux.org/conary/api"

    labels = [
        "foresight.rpath.org@fl:2",
        "foresight.rpath.org@fl:2-kernel",
        "foresight.rpath.org@fl:2-qa",
        "foresight.rpath.org@fl:2-qa-kernel",
        #"foresight.rpath.org@fl:2-devel",
        #"foresight.rpath.org@fl:2-devel-kernel",
        ]

    cache = "rawdata"
    mkdir(cache)
    for b in labels:
        refresh_source_list(api_site, b, cache)
        refresh_pkg_list(api_site, b, cache)

if __name__ == "__main__":
    main()
