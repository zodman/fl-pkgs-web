import os, json

from lxml import etree
import pymongo

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_trove_filelist(fname):
    '''Read a list of file names from the <trove> info of a component, which
    should contain a list of <fileref>
    '''
    ret = []
    xml = etree.parse(fname)
    for fileref in xml.findall("fileref"):
        ret.append(fileref.find("path").text)
    return ret

class Package:
    def __init__(self, data, cache):
        '''Information about a package
        '''
        self.cache = cache

        # basic info
        self.name = data["name"]
        self.revision = data["revision"]
        # list of flavor names; would be [None] if this is a no-flavor pkg
        self.flavors = data["flavors"]
        self.size = data["size"]
        self.source = data["source"]
        self.buildtime = data["buildtime"]
        self.buildlog = data["buildlog"]
        self.included = data["included"]

        # info available after read_filelist()
        self.filelist = [] # list of files

    def read_filelist(self):
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
        return {
            "name": self.name,
            "revision": self.revision,
            "flavors": self.flavors,
            "size": self.size,
            "source": self.source,
            "buildtime": self.buildtime,
            "buildlog": self.buildlog,
            "included": self.included,
            "filelist": self.filelist,
            }

class SourceTrove:
    def __init__(self, xml):
        self.name = xml.find("name").text
        self.revision = xml.find("version").find("revision").text
        self.ordering = float(xml.find("version").find("ordering").text)
        self.binpkgs = []

    def to_dict(self):
        return {
            "name": self.name,
            "revision": self.revision,
            "binpkgs": self.binpkgs,
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
        f = "%s/source-%s" % (self.cache, label)

        for e in etree.parse(f).getroot():
            pkg = SourceTrove(e)
            if pkg.revision.startswith("0-"):
                continue
            if pkg.name in self.src_pkgs and \
                    self.src_pkgs[pkg.name].ordering > pkg.ordering:
                continue
            self.src_pkgs[pkg.name] = pkg

    def _read_bin_pkgs(self, label):
        # must be after _read_src_pkgs
        f = open("%s/%s" % (self.cache, label))
        pkgs = json.load(f)
        f.close()

        for name, data in pkgs.items():
            pkg = Package(data, "%s/%s" % (self.cache, label.split("@")[1]))

            src = self.src_pkgs.get(pkg.source, None)
            if not src:
                continue
            mainpkg = pkgs.get(pkg.source.split(":")[0], None)
            if not mainpkg or pkg.revision != mainpkg["revision"]:
                continue

            self.bin_pkgs[name] = pkg
            src.binpkgs.append(name)

def cleanup_pkg_collection(coll, tokeep):
    '''Clean up the mongo collection @coll according to the pkg set @tokeep

    @tokeep should be either label.bin_pkgs or label.src_pkgs.
    '''
    print " cleaning up db"
    for pkg in coll.find():
        name = pkg["name"]
        if not name in tokeep:
            print " removing %s" % name
            coll.remove({"_id": name})
    print " db now has %d." % coll.count()

# not sure about the schema. for now use two separate collections for
# binary and source pkgs
def write_bin_pkgs(db, label):
    coll = db[label.branch + ":binary"]
    coll.ensure_index("name")
    print "storing %s binary pkgs. %d in total (including potential nils). Current db has %d." % (
            label.branch, len(label.bin_pkgs), coll.count())

    n = 0
    for name, pkg in label.bin_pkgs.items():
        existing = coll.find_one({"name": name})
        # whether the pkg has been changed
        if existing and existing["revision"] == pkg.revision:
            continue

        pkg.read_filelist()
        pkg = pkg.to_dict()
        pkg["_id"] = name # use pkg name as id
        coll.save(pkg)
        n += 1
    print " %d pkgs written." % n

    cleanup_pkg_collection(coll, label.bin_pkgs)

def write_src_pkgs(db, label):
    coll = db[label.branch + ":source"]
    coll.ensure_index("name")
    print "storing %s source pkgs. %d in total. Current db has %d." % (
            label.branch, len(label.src_pkgs), coll.count())

    n = 0
    for name, pkg in label.src_pkgs.items():
        existing = coll.find_one({"name": name})
        # whether the pkg has been changed
        if existing and existing["revision"] == pkg.revision:
            continue
        pkg = pkg.to_dict()
        pkg["_id"] = name # use pkg name as id
        coll.save(pkg)
        n += 1
    print " %d source pkgs written." % n

    cleanup_pkg_collection(coll, label.src_pkgs)

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
