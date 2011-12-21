import os, json
from xml.etree import ElementTree

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def collect_builddep_list(xml):
    '''Collect (name, label, revision) tuples" from a <trovelist></trovelist>
    '''
    ret = []
    for t in xml.find("trovelist"):
        name = t.find("name").text
        if ":" in name:
            continue
        label = t.find("version").find("label").text
        revision = t.find("version").find("revision").text
        ret.append((name, label, revision))
    return ret

def collect_component_list(xml):
    '''Collect name " from a <trovelist></trovelist>
    '''
    ret = [t.find("name").text for t in xml.find("trovelist")]
    return ret

class TroveInfo:
    def __init__(self, xml):
        size = None
        source = None
        buildtime = None
        # note: can be none
        buildlog = None
        builddeps = []
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
            #elif e.tag == "builddeps":
            #    builddeps = collect_builddep_list(e)
            elif e.tag == "included":
                included = collect_component_list(e)

        self.size = size
        self.source = source
        self.buildtime = buildtime
        self.buildlog = buildlog
        self.builddeps = builddeps
        self.included = included

class Package:
    def __init__(self, xml, label, cache):
        self.label = label
        self.name = xml.find("name").text
        self.revision = xml.find("version").find("revision").text

        self.flavors = None # would be [None] if this is a no-flavor pkg
        self.size = None # int
        self.source = None # str
        self.buildtime = None # int; unix time
        self.buildlog = None # url
        self.builddeps = None # list of (name, label, revision, flavor) tuples
        self.included = None # list of (name, label, revision, flavor) tuples

        self._cache = cache

    def read_info(self):
        '''Read detailed information from cached data
        '''
        subdir = self.label.branch
        f = open("%s/%s/%s-%s" % (self._cache, subdir, self.name, self.revision))
        content = f.read()
        f.close()
        self._parse(ElementTree.XML(content))

    def _parse(self, xml):
        self.flavors = [t.find("displayflavor").text for t in xml]

        # all troves should contain mostly same info.
        # some info is different, e.g. size/buildtime/buildlog, but for now we
        # just consider the first trove.
        info = TroveInfo(xml[0])
        self.size = info.size
        self.source = info.source
        self.buildtime = info.buildtime
        self.buildlog = info.buildlog
        self.builddeps = info.builddeps
        self.included = info.included

    def __repr__(self):
        return "%s=%s" % (self.name, self.revision)

    def to_dict(self):
        return {
            "name": self.name,
            "revision": self.revision,
            "flavors": self.flavors,
            "size": self.size,
            "source": self.source,
            "buildtime": self.buildtime,
            "buildlog": self.buildlog,
            # not outputing builddeps. Not sure if it's useful.
            #"builddeps": self.builddeps,
            "included": self.included,
            }

class Label:
    '''Container of information about a conary label
    '''
    def __init__(self, label, cache, read_pkg_details=True):
        '''Read information about a @label from cached data at @cache.

        If @read_pkg_details is True, will read detailed info of each pkg.
        Could take a long time.
        '''
        self.name = label
        self.branch = label.split("@")[1]
        self._pkgs = {}

        f = open("%s/%s" % (cache, label))
        content = f.read()
        f.close()

        for e in ElementTree.XML(content):
            pkg = Package(e, self, cache)
            self._pkgs[pkg.name] = pkg

        if read_pkg_details:
            for pkg in self.get_pkgs():
                pkg.read_info()

    def get_pkgs(self):
        return self._pkgs.values()

    def get_pkg(self, name):
        return self._pkgs[name]

    def to_dict(self):
        return {"pkgs": [(p.name, p.revision) for p in self.get_pkgs()]}

def write_info(src, dest, obj):
    '''Put obj.to_json() to the @dest file.

    @src is merely for logging here.
    '''
    print src, "=>", dest

    f = open(dest, "w")
    json.dump(obj.to_dict(), f)
    f.close()

def convert():
    cache = "rawdata"
    output = "info"
    for b in [
            "foresight.rpath.org@fl:2",
            "foresight.rpath.org@fl:2-kernel",
            "foresight.rpath.org@fl:2-qa",
            "foresight.rpath.org@fl:2-qa-kernel"]:
        branch = b.split("@")[-1]
        mkdir("%s/%s" % (output, branch))

        src = "%s/%s" % (cache, b)
        dest = "%s/%s" % (output, b)
        label = Label(b, cache, read_pkg_details=False)
        write_info(src, dest, label)

        for pkg in label.get_pkgs():
            f = "%s-%s" % (pkg.name, pkg.revision)
            src = "%s/%s/%s" % (cache, branch, f)
            dest = "%s/%s/%s"  % (output, branch, f)
            if os.path.exists(dest):
                continue
            pkg.read_info()
            write_info(src, dest, pkg)

if __name__ == "__main__":
    convert()
