import sys, os, urllib2, json
# running a do-nothing refresh of components:
# lxml takes 0m56.850s.
# cElementTree takes 1m2.269s.
# ElepentTree takes forever (>10m)
from lxml import etree

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def log(msg):
    print msg

def log_error(msg):
    sys.stderr.write(msg + "\n")

def cleanup_dir(dire, tokeep):
    '''Clean up the dir @dire, only keep files in @tokeep

    Does not touch non-files.
    '''
    allfiles = os.listdir(dire)
    for f in set(allfiles) - set(tokeep):
        t = "%s/%s" % (dire, f)
        if os.path.isfile(t):
            log("removing %s" % t)
            os.remove(t)

def collect_component_list(xml):
    '''Collect name " from a <trovelist></trovelist>
    '''
    ret = [(t.find("name").text, t.get("id")) for t in xml.find("trovelist")]
    return ret

class TroveInfoParser:
    def __init__(self, xml):
        size = None
        source = None
        buildtime = None
        # note: can be none
        buildlog = None
        included = []

        for e in xml:
            if e.tag == "size":
                size = int(e.text)
            elif e.tag == "source":
                # only take trovelist[0]. There should always be only one :source.
                source = e.find("trovelist")[0].find("name").text
            elif e.tag == "buildtime":
                buildtime = int(e.text)
            elif e.tag == "buildlog":
                buildlog = e.get("id")
            elif e.tag == "included":
                included = collect_component_list(e)

        self.size = size
        self.source = source
        self.buildtime = buildtime
        self.buildlog = buildlog
        self.included = included

class Package:
    def __init__(self, xmlelement):
        self.name = xmlelement.find("name").text
        self.revision = xmlelement.find("version").find("revision").text
        self.ordering = float(xmlelement.find("version").find("ordering").text)
        # link to pkg details
        self.troveinfo = xmlelement.get("id")
        self.flavors = [xmlelement.find("flavor").text]

    def fetch_details(self, destdir):
        f = "%s/%s-%s" % (destdir, self.name, self.revision)
        if not os.path.exists(f):
            content = fetch_api_data(self.troveinfo, f)
            xml = etree.XML(content)
        else:
            xml = etree.parse(f).getroot()

        info = TroveInfoParser(xml)
        self.size = info.size
        self.source = info.source
        self.buildtime = info.buildtime
        self.buildlog = info.buildlog
        self.included = info.included

    def to_dict(self):
        return {
            "name": self.name,
            "revision": self.revision,
            "flavors": self.flavors,
            "size": self.size,
            "source": self.source,
            "buildtime": self.buildtime,
            "buildlog": self.buildlog,
            # note self.included contains tuple, while the exported dict
            # contains just strings
            "included": [name for (name, link) in self.included],
            }

def fetch_api_data(api, dest):
    '''Reading from url @api, and write to file @dest
    '''
    log("reading %s" % urllib2.unquote(api))
    u = urllib2.urlopen(api)
    content = u.read()
    u.close()

    if dest:
        log("writing %s" % dest)
        f = open(dest + ".new", "w")
        f.write(content)
        f.close()
        os.rename(dest + ".new", dest)

    return content

def parse_pkg_list(xml):
    '''Read a <trovelist> and return a list of pkgs contained within

    The <trovelist> from /api/trove contains all flavors of a pkg (and in some
    cases, older versions of the pkg as well), but we only record the info link
    (Package.troveinfo) of one flavor (and also collect all flavors into
    Package.flavors).
    '''
    pkgs = {}
    for e in etree.XML(xml):
        pkg = Package(e)
        # drop nil pkgs
        if pkg.revision.startswith("0-"):
            continue
        if pkg.name in pkgs and pkgs[pkg.name].ordering > pkg.ordering:
            continue
        if pkg.name in pkgs and pkgs[pkg.name].ordering == pkg.ordering:
            pkgs[pkg.name].flavors.extend(pkg.flavors)
            continue
        pkgs[pkg.name] = pkg
    return pkgs

def write_pkg_list(pkgs, dest):
    '''Write the parsed pkg list instead of the raw XML. So we don't have to
    repeat ourselves in convert.py
    '''
    log("dumping json to %s" % dest)
    f = open(dest, "w")
    json.dump(pkgs, f)
    f.close()

def read_pkg_list(dest):
    f = open(dest)
    pkgs = json.load(f)
    f.close()
    return pkgs

def fetch_component(trove, revision, link, destdir):
    fname = "%s-%s" % (trove, revision)
    dest = "%s/%s" % (destdir, fname)

    if os.path.exists(dest):
        return

    #### blacklist ####
    blacklist = {
            "fl:2": ("community-themes:data-0.13-3-2",
                     "klavaro:data-1.2.1-1-1"),
            "fl:2-qa": ("community-themes:data-0.13-3-3",
                        "pitivi:locale-0.15.0-1-1",
                        "pitivi:runtime-0.15.0-1-1"),
            "fl:2-devel": ("community-themes:data-0.13-3-3",
                        "pitivi:locale-0.15.0-1-1",
                        "pitivi:runtime-0.15.0-1-1"),
            }
    if fname in blacklist.get(destdir.split("/")[-2], []):
        log_error("skipping %s" % dest)
        return
    #### end ####

    try:
        fetch_api_data(link, dest)
    # sometimes there is UnicodeDecodeError: 'ascii' codec can't decode
    # byte 0xd0 in position 69: ordinal not in range(128).
    # reported to rpath/crest: https://issues.rpath.com/browse/BUGS-469
    except urllib2.HTTPError as e:
        if e.code == 500 and e.readline().startswith("UnicodeDecodeError"):
            log_error("got UnicodeDecodeError. NOT writing %s" % dest)

def refresh_pkg_list(api_site, label, cachedir):
    '''Fetch the list of pkgs
    '''
    dest = "%s/%s" % (cachedir, label)
    pkgdata = {}
    if os.path.exists(dest):
        pkgdata = read_pkg_list(dest)

    api = "%s/trove?label=%s&type=package&type=group" % (api_site, label)
    content = fetch_api_data(api, None)
    pkgs = parse_pkg_list(content)
    changed_pkgs = {}

    destdir = "%s/%s" % (cachedir, label.split("@")[-1])
    mkdir(destdir)

    for name, pkg in pkgs.items():
        if name not in pkgdata or pkg.revision != pkgdata[name]["revision"]:
            pkg.fetch_details(destdir)
            pkgdata[name] = pkg.to_dict()
            changed_pkgs[name] = pkg

    write_pkg_list(pkgdata, dest)

    return changed_pkgs, pkgdata

def refresh_source_list(api_site, label, cachedir):
    api = "%s/trove?label=%s&type=source" % (api_site, label)
    dest = "%s/source-%s" % (cachedir, label)
    fetch_api_data(api, dest)

def refresh_components(pkgs, labeldir):
    '''Fetch info of components for all pkgs on a label

    The components will be cached in the 'components' subdir.
    '''
    destdir = "%s/components" % labeldir
    mkdir(destdir)

    for name, pkg in pkgs.items():
        if name.startswith("group-"):
            continue
        for trove, link in pkg.included:
            if trove.endswith(":debuginfo") or trove.endswith(":test"):
                continue
            fetch_component(trove, pkg.revision, link, destdir)

def cleanup_cache(pkgdata, labeldir):
    # cleanup pkgs, i.e. rawdata/fl:*/
    pkgs = ["%s-%s" % (name, p["revision"]) for name, p in pkgdata.items()]
    cleanup_dir(labeldir, pkgs)

    # cleanup components, i.e. rawdata/fl:*/components
    compos = []
    for name, pkg in pkgdata.items():
        if name.startswith("group-"):
            continue
        for trove in pkg["included"]:
            if trove.endswith(":debuginfo") or trove.endswith(":test"):
                continue
            compos.append("%s-%s" % (trove, pkg["revision"]))
    cleanup_dir("%s/components" % labeldir, compos)

def main():
    api_site = "http://conary.foresightlinux.org/conary/api"

    labels = [
        "foresight.rpath.org@fl:2",
        "foresight.rpath.org@fl:2-kernel",
        "foresight.rpath.org@fl:2-qa",
        "foresight.rpath.org@fl:2-qa-kernel",
        "foresight.rpath.org@fl:2-devel",
        "foresight.rpath.org@fl:2-devel-kernel",
        ]

    cache = "rawdata"
    mkdir(cache)
    for b in labels:
        labeldir = "%s/%s" % (cache, b.split("@")[1])
        #refresh_source_list(api_site, b, cache)
        changed_pkgs, pkgs = refresh_pkg_list(api_site, b, cache)
        refresh_components(changed_pkgs, labeldir)
        cleanup_cache(pkgs, labeldir)

if __name__ == "__main__":
    main()
