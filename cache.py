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

class Package:
    def __init__(self, xmlelement):
        self.name = xmlelement.find("name").text
        self.revision = xmlelement.find("version").find("revision").text
        self.ordering = float(xmlelement.find("version").find("ordering").text)
        # link to pkg details
        self.troveinfo = xmlelement.get("id")
        self.flavors = [xmlelement.find("flavor").text]

    def to_dict(self):
        return dict(name=self.name, revision=self.revision, flavors=self.flavors)

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
    ret = pkgs.values()
    return ret

def write_pkg_list(pkgs, dest):
    '''Write the parsed pkg list instead of the raw XML. So we don't have to
    repeat ourselves in convert.py
    '''
    f = open(dest, "w")
    json.dump([pkg.to_dict() for pkg in pkgs], f)
    f.close()

def fetch_component_info(link, f):
    if os.path.exists(f):
        return
    try:
        fetch_api_data(link, f)
    # sometimes there is UnicodeDecodeError: 'ascii' codec can't decode
    # byte 0xd0 in position 69: ordinal not in range(128).
    # reported to rpath/crest: https://issues.rpath.com/browse/BUGS-469
    except urllib2.HTTPError as e:
        if e.code == 500 and e.readline().startswith("UnicodeDecodeError"):
            log_error("got UnicodeDecodeError. NOT writing %s" % f)

def fetch_components_for_pkg(pkgfile, destdir):
    '''Take a pkg info file, and fetch its components to destdir

    Return all component files that have been cached, so we can do cleanup
    later.
    '''

    ret = []

    xml = etree.parse(pkgfile)
    revision = xml.find("version").find("revision").text

    included = [(t.find("name").text, t.get("id"))
            for t in xml.find("included").find("trovelist")]
    for trove, infolink in included:
        if trove.endswith(":debuginfo") or trove.endswith(":test"):
            continue
        f = "%s-%s" % (trove, revision)

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
        if f in blacklist.get(destdir.split("/")[-2], []):
            log_error("skipping %s/%s" % (destdir, f))
            continue
        #### end ####

        ret.append(f)
        fetch_component_info(infolink, "%s/%s" % (destdir, f))

    return ret

def refresh_pkg_list(api_site, label, cachedir):
    '''Fetch the list of pkgs
    '''
    api = "%s/trove?label=%s&type=package&type=group" % (api_site, label)
    content = fetch_api_data(api, None)

    pkgs = parse_pkg_list(content)
    dest = "%s/%s" % (cachedir, label)
    write_pkg_list(pkgs, dest)

    destdir = "%s/%s" % (cachedir, label.split("@")[-1])
    mkdir(destdir)

    for pkg in pkgs:
        f = "%s/%s-%s" % (destdir, pkg.name, pkg.revision)
        if not os.path.exists(f):
            fetch_api_data(pkg.troveinfo, f)

    tokeep = ["%s-%s" % (p.name, p.revision) for p in pkgs]
    cleanup_dir(destdir, tokeep)

def refresh_source_list(api_site, label, cachedir):
    api = "%s/trove?label=%s&type=source" % (api_site, label)
    dest = "%s/source-%s" % (cachedir, label)
    fetch_api_data(api, dest)

def refresh_components(labeldir):
    '''Fetch info of components for all pkgs on a label

    The components will be cached in the 'components' subdir.
    '''
    destdir = "%s/components" % labeldir
    mkdir(destdir)

    tokeep = []
    for fname in os.listdir(labeldir):
        if fname.startswith("group-"):
            continue
        path = "%s/%s" % (labeldir, fname)
        if not ("-" in fname and os.path.isfile(path)):
            continue

        comps = fetch_components_for_pkg(path, destdir)
        tokeep.extend(comps)
    cleanup_dir(destdir, tokeep)

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
        refresh_source_list(api_site, b, cache)
        refresh_pkg_list(api_site, b, cache)
        refresh_components("%s/%s" % (cache, b.split("@")[1]))

if __name__ == "__main__":
    main()
