import os, json
from lxml import etree

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

def read_trove_filelist(fname):
    '''Read a list of file names from the <trove> info of a component, which
    should contain a list of <fileref>
    '''
    f = open(fname)
    content = f.read()
    f.close

    ret = []
    xml = etree.XML(content)
    for fileref in xml.findall("fileref"):
        ret.append(fileref.find("path").text)
    return ret

class TroveInfoParser:
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
    def __init__(self, xml, label):
        self.label = label
        self.name = xml.find("name").text
        self.revision = xml.find("version").find("revision").text

        # list of flavor names; would be [None] if this is a no-flavor pkg
        self.flavors = []
        self.size = None # int
        self.source = None # str
        self.buildtime = None # int; unix time
        self.buildlog = None # url
        self.builddeps = [] # list of (name, label, revision) tuples
        self.included = [] # list of names
        self.filelist = [] # list of files

    def read_info(self, with_filelist=True):
        '''Read detailed information from cached data
        '''
        f = open("%s/%s/%s-%s" % (self.label.cache, self.label.branch,
            self.name, self.revision))
        content = f.read()
        f.close()
        self._parse(etree.XML(content))
        if with_filelist:
            self._read_filelist()

    def _parse(self, xml):
        self.flavors = [t.find("displayflavor").text for t in xml]

        # all troves should contain mostly same info.
        # some info is different, e.g. size/buildtime/buildlog, but for now we
        # just consider the first trove.
        info = TroveInfoParser(xml[0])
        self.size = info.size
        self.source = info.source
        self.buildtime = info.buildtime
        self.buildlog = info.buildlog
        self.builddeps = info.builddeps
        self.included = info.included

    def _read_filelist(self):
        '''Read filelist from components
        '''
        self.filelist = []
        for trove in self.included:
            f = "%s/%s/components/%s-%s" % (self.label.cache,
                    self.label.branch, trove, self.revision)
            try:
                self.filelist.extend(read_trove_filelist(f))
            except IOError as e:
                # ENOENT. the component info is not available. skip it.
                # Either the component can be fetched, or it's deliberatedly
                # omitted (:debuginfo, :test etc)
                if e.errno == 2:
                    continue

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
            "filelist": self.filelist,
            }

class SourceTrove:
    def __init__(self, xml):
        self.name = xml.find("name").text
        self.revision = xml.find("version").find("revision").text

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
        self.cache = cache
        self._bin_pkgs = {}
        self._src_pkgs = {}

        self._read_bin_pkgs(read_pkg_details)
        self._read_src_pkgs()

    def _read_bin_pkgs(self, read_details):
        f = open("%s/%s" % (self.cache, self.name))
        content = f.read()
        f.close()

        for e in etree.XML(content):
            pkg = Package(e, self)
            if pkg.revision.startswith("0-"):
                continue
            self._bin_pkgs[pkg.name] = pkg

        if read_details:
            for pkg in self._bin_pkgs.values():
                pkg.read_info()

    def _read_src_pkgs(self):
        f = open("%s/source-%s" % (self.cache, self.name))
        content = f.read()
        f.close()

        for e in etree.XML(content):
            pkg = SourceTrove(e)
            if pkg.revision.startswith("0-"):
                continue
            self._src_pkgs[pkg.name] = pkg

    def get_pkgs(self):
        return self._bin_pkgs.values()

    def get_src_pkgs(self):
        return self._src_pkgs.values()

    def get_pkg(self, name):
        return self._bin_pkgs[name]

    def to_dict(self):
        return {
            "pkgs": [(p.name, p.revision) for p in self.get_pkgs()],
            "srcpkgs": [(p.name, p.revision) for p in self.get_src_pkgs()]}

def write_info(dest, obj):
    '''Put obj.to_json() to the @dest file.
    '''
    print "=>", dest

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
        label = Label(b, cache, read_pkg_details=False)
        labeldir = "%s/%s" % (output, label.branch)
        mkdir(labeldir)

        write_info("%s/%s" % (output, b), label)

        for pkg in label.get_pkgs():
            f = "%s-%s" % (pkg.name, pkg.revision)
            dest = "%s/%s"  % (labeldir, f)
            if os.path.exists(dest):
                continue
            pkg.read_info()
            write_info(dest, pkg)

if __name__ == "__main__":
    convert()
