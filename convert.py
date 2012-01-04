import os, json

from lxml import etree
import pymongo

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
    f.close()

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
    def __init__(self, data, cache):
        self.cache = cache
        self.name = data["name"]
        self.revision = data["revision"]
        # list of flavor names; would be [None] if this is a no-flavor pkg
        self.flavors = data["flavors"]

        self.size = None # int
        self.source = None # str
        self.buildtime = None # int; unix time
        self.buildlog = None # url
        self.builddeps = [] # list of (name, label, revision) tuples
        self.included = [] # list of names
        self.filelist = [] # list of files

        self._info_complete = False

    def read_info(self, with_filelist=True):
        '''Read detailed information from cached data
        '''
        if self._info_complete:
            return
        f = open("%s/%s-%s" % (self.cache, self.name, self.revision))
        content = f.read()
        f.close()
        self._parse(etree.XML(content))
        if with_filelist:
            self._read_filelist()
        self._info_complete = True

    def _parse(self, xml):
        info = TroveInfoParser(xml)
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
            f = "%s/components/%s-%s" % (self.cache, trove, self.revision)
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
        self.read_info()
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

    def to_dict(self):
        return {
            "name": self.name,
            "revision": self.revision,
            }

class Label:
    def __init__(self, labels, cache):
        '''A Label is a container of one or more conary labels, which are
        always installed together (e.g. fl:2 and fl:2-kernel)

        The first label is taken as the primary one, and the rest are
        auxiliary.

        Read information about @labels from cached data at @cache.

        If @read_pkg_details is True, will read detailed info of each pkg.
        Could take a long time.
        '''
        self.branch = labels[0].split("@")[1]
        self.cache = cache
        self.src_pkgs = {}
        self.bin_pkgs = {}

        for b in labels:
            self._read_src_pkgs(b)
        for b in labels:
            self._read_bin_pkgs(b)

    def _read_src_pkgs(self, label):
        f = open("%s/source-%s" % (self.cache, label))
        content = f.read()
        f.close()

        for e in etree.XML(content):
            pkg = SourceTrove(e)
            if pkg.revision.startswith("0-"):
                continue
            self.src_pkgs[pkg.name] = pkg

    def _read_bin_pkgs(self, label):
        f = open("%s/%s" % (self.cache, label))
        pkgs = json.load(f)
        f.close()

        for pkg in pkgs:
            pkg = Package(pkg, "%s/%s" % (self.cache, label.split("@")[1]))
            self.bin_pkgs[pkg.name] = pkg

# not sure about the schema. for now use two separate collections for
# binary and source pkgs
def write_bin_pkgs(db, label):
    coll = db[label.branch + ":binary"]
    coll.ensure_index("name")
    print "storing %s binary pkgs. %d in total. Current db has %d." % (
            label.branch, len(label.bin_pkgs), coll.count())

    # remove pkgs not present in @label
    for pkg in coll.find():
        if not pkg["name"] in label.bin_pkgs:
            print " removing %s" % pkg["name"]
            coll.remove({"_id": pkg["name"]})

    n = 0
    for pkg in label.bin_pkgs.values():
        existing = coll.find_one({"name": pkg.name})
        # whether the pkg has been changed
        if existing and existing["revision"] == pkg.revision:
            continue
        pkg = pkg.to_dict()
        # skip if there is no corresponding :source
        if not label.src_pkgs.get(pkg["source"], None):
            continue
        pkg["_id"] = pkg["name"] # use pkg name as id
        coll.save(pkg)
        n += 1
    print " %d pkgs written." % n

def write_src_pkgs(db, label):
    coll = db[label.branch + ":source"]
    coll.ensure_index("name")
    print "storing %s source pkgs. %d in total. Current db has %d." % (
            label.branch, len(label.src_pkgs), coll.count())

    # remove pkgs not present in @label
    for pkg in coll.find():
        if not pkg["name"] in label.src_pkgs:
            print " removing %s" % pkg["name"]
            coll.remove({"_id": pkg["name"]})

    for pkg in label.src_pkgs.values():
        pkg = pkg.to_dict()
        pkg["_id"] = pkg["name"] # use pkg name as id
        coll.save(pkg)

def convert():
    cache = "rawdata"
    conn = pymongo.Connection()
    db = conn.fl_pkgs
    for b in [
            ("foresight.rpath.org@fl:2",
             "foresight.rpath.org@fl:2-kernel"),
            ("foresight.rpath.org@fl:2-qa",
             "foresight.rpath.org@fl:2-qa-kernel"),
            ("foresight.rpath.org@fl:2-devel",
             "foresight.rpath.org@fl:2-devel-kernel"),
            ]:
        label = Label(b, cache)
        write_bin_pkgs(db, label)
        write_src_pkgs(db, label)

if __name__ == "__main__":
    convert()
