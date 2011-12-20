from xml.etree import ElementTree

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
            elif e.tag == "builddeps":
                builddeps = collect_builddep_list(e)
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
        subdir = self.label.split("@")[-1]
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
        return "%s=%s/%s" % (self.name, self.label, self.revision)

class Label:
    '''Container of information about a conary label
    '''
    def __init__(self, label, cache, read_pkg_details=True):
        '''Read information about a @label from cached data at @cache.

        If @read_pkg_details is True, will read detailed info of each pkg.
        Could take a long time.
        '''
        self.name = label
        self._pkgs = {}

        f = open("%s/%s" % (cache, label))
        content = f.read()
        f.close()

        for e in ElementTree.XML(content):
            pkg = Package(e, label, cache)
            self._pkgs[pkg.name] = pkg

        if read_pkg_details:
            for pkg in self._pkgs.values():
                pkg.read_info()

    def get_pkgs(self):
        return self._pkgs.values()

    def get_pkg(self, name):
        return self._pkgs[name]
