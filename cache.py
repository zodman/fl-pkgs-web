import sys, os, urllib2
from xml.etree import ElementTree

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def log(msg):
    print msg

def log_error(msg):
    sys.stderr.write(msg + "\n")

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

def clean_pkgs_cache(destdir, pkgs):
    tokeep = ["%s-%s" % (p.name, p.revision) for p in pkgs]
    allfiles = os.listdir(destdir)
    for f in set(allfiles) - set(tokeep):
        t = "%s/%s" % (destdir, f)
        if os.path.isfile(t):
            log("removing %s" % t)
            os.remove(t)

def fetch_pkg_info(pkgs, destdir):
    '''Fetch detailed info about a pkg, from the 'trovelist' of the node
    '''
    for pkg in pkgs:
        f = "%s/%s-%s" % (destdir, pkg.name, pkg.revision)
        if not os.path.exists(f):
            fetch_api_data(pkg.trovelist, f)

def refresh_pkg_list(api_site, label, cachedir):
    '''Fetch the list of pkgs, called 'nodes' in conary REST API.
    '''
    api = "%s/node?label=%s&type=package&type=group" % (api_site, label)
    dest = "%s/%s" % (cachedir, label)
    content = fetch_api_data(api, dest)

    pkgs = parse_pkg_list(content)
    destdir = "%s/%s" % (cachedir, label.split("@")[-1])
    mkdir(destdir)
    fetch_pkg_info(pkgs, destdir)
    clean_pkgs_cache(destdir, pkgs)

def refresh_source_list(api_site, label, cachedir):
    api = "%s/node?label=%s&type=source" % (api_site, label)
    dest = "%s/source-%s" % (cachedir, label)
    fetch_api_data(api, dest)

def refresh_components(labeldir):
    '''Fetch info of components, which will have the list of files
    '''
    destdir = "%s/components" % labeldir
    mkdir(destdir)
    for fname in os.listdir(labeldir):
        if fname.startswith("group-"):
            continue
        path = "%s/%s" % (labeldir, fname)
        if not ("-" in fname and os.path.isfile(path)):
            continue

        # each file contains the trove info of a pkg
        f = open(path)
        content = f.read()
        f.close()

        # only take the first of the trovelist (usu. the is:x86 one)
        xml = ElementTree.XML(content)[0]

        # all components
        included = [(t.find("name").text,
                     t.find("version").find("revision").text,
                     t.get("id"))
                         for t in xml.find("included").find("trovelist")]
        for name, revision, infolink in included:
            f = "%s/%s-%s" % (destdir, name, revision)
            if os.path.exists(f):
                continue
            try:
                fetch_api_data(infolink, f)
            # sometimes there is UnicodeDecodeError: 'ascii' codec can't decode
            # byte 0xd0 in position 69: ordinal not in range(128).
            # reported to rpath/crest: https://issues.rpath.com/browse/BUGS-469
            except urllib2.HTTPError as e:
                if e.code == 500 and e.readline().startswith("UnicodeDecodeError"):
                    log_error("got UnicodeDecodeError when fetching %s-%s" % (name, revision))
                    continue

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
        refresh_components("%s/%s" % (cache, b.split("@")[1]))

if __name__ == "__main__":
    main()
