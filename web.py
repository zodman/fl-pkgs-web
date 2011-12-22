import time, json

from bottle import route, run, view, abort

def format_size(size):
    if size < 1000:
        size = "%dB" % size
    elif size >= 1000 and size < 1000 * 1000:
        size = "%.1fKB" % (size / 1000.0)
    else:
        size = "%.1fMB" % (size / 1000.0 / 1000.0)
    return size

def format_flavors(flavors):
    return ", ".join(["[%s]" % str(f) for f in flavors])

def format_buildtime(buildtime):
    return time.strftime("%a, %d %b %Y %H:%M", time.localtime(buildtime))

class SourceTrove:
    def __init__(self, name, revision):
        self.name = name
        self.revision = revision
        self.binpkgs = []

class Package:
    def __init__(self, name, revision, label):
        self.name = name
        self.revision = revision
        self.label = label

        self._info_complete = False

    def read_info(self):
        if self._info_complete:
            return

        branch = self.label.branch
        f = open("info/%s/%s-%s" % (branch, self.name, self.revision))
        data = json.load(f)

        self.flavors = format_flavors(data["flavors"])
        self.size = format_size(data["size"])
        self.source = data["source"]
        self.buildtime = format_buildtime(data["buildtime"])
        self.buildlog = data["buildlog"]
        self.included = data["included"]
        self.filelist = data["filelist"]

        self._info_complete = True

class Label:
    def __init__(self, label):
        self.name = label
        self.branch = label.split("@")[1] # fl:2-devel etc
        self._bin_pkgs = {}
        self._src_pkgs = {}

        self._read_info()

    def _read_info(self):
        f = open("info/%s" % self.name)
        data = json.load(f)
        f.close()

        # read binary packages
        for name, revision in data["pkgs"]:
            pkg = Package(name, revision, self)
            # read all info into memory
            pkg.read_info()
            self._bin_pkgs[name] = pkg

        # read src packages
        for name, revision in data["srcpkgs"]:
            pkg = SourceTrove(name, revision)
            self._src_pkgs[name] = pkg

        # associate :source with relevant pkgs
        for k, p in self._bin_pkgs.items():
            try:
                self._src_pkgs[p.source].binpkgs.append(p)
            except KeyError:
                # when a pkg's :source can't be found, it means the :source has
                # been redirected to nil, but the pkg is not (since it's a
                # subpkg)
                del self._bin_pkgs[k]

    def get_pkgs(self):
        return self._bin_pkgs.values()

    def get_src_pkgs(self):
        return self._src_pkgs.values()

    def get_pkg(self, name):
        '''Could raise KeyError
        '''
        return self._bin_pkgs[name]

    def get_src_pkg(self, name):
        '''Could raise KeyError
        '''
        if not ":" in name:
            name += ":source"
        return self._src_pkgs[name]

class Install:
    '''An install can have several labels, e.g. 2-qa should include fl:2-qa and
    fl:2-qa-kernel.

    Not sure `install` is a good name.
    '''
    def __init__(self, name, labels):
        self.name = name
        self.labels = [Label(b) for b in labels]

    def get_pkgs(self):
        ret = []
        for b in self.labels:
            ret.extend(b.get_pkgs())
        ret.sort(key=lambda p: p.name)
        return ret

    def get_src_pkgs(self):
        ret = []
        for b in self.labels:
            ret.extend(b.get_src_pkgs())
        ret.sort(key=lambda p: p.name)
        return ret

    def get_pkg(self, name):
        for b in self.labels:
            try:
                pkg = b.get_pkg(name)
                return pkg
            except KeyError:
                continue
        abort(404, "No such page")

    def get_src_pkg(self, name):
        for b in self.labels:
            try:
                pkg = b.get_src_pkg(name)
                return pkg
            except KeyError:
                continue
        abort(404, "No such page")

installs = {}

@route("/")
@view("index")
def index():
    return {}

@route("/<inst:re:(2|2-qa)>")
@view("install")
def show_install(inst):
    return dict(install=installs[inst])

@route("/<inst:re:(2|2-qa)>/source")
@view("install-sources")
def show_install_sources(inst):
    '''List :source packages
    '''
    return dict(install=installs[inst])

@route("/<inst:re:(2|2-qa)>/<pkg>")
@view("pkg")
def show_pkg(inst, pkg):
    install = installs[inst]
    return dict(install=install, pkg=install.get_pkg(pkg))

@route("/<inst:re:(2|2-qa)>/<pkg>/filelist")
@view("filelist")
def show_pkg_filelist(inst, pkg):
    install = installs[inst]
    return dict(install=install, pkg=install.get_pkg(pkg))

@route("/<inst:re:(2|2-qa)>/source/<pkg>")
@view("srcpkg")
def show_src_pkg(inst, pkg):
    install = installs[inst]
    return dict(install=install, src=install.get_src_pkg(pkg))

if __name__ == "__main__":
    installs = {
            "2": Install("2", [
                    "foresight.rpath.org@fl:2",
                    "foresight.rpath.org@fl:2-kernel"]),
            "2-qa": Install("2-qa", [
                    "foresight.rpath.org@fl:2-qa",
                    "foresight.rpath.org@fl:2-qa-kernel"]),
            }

    run(host="localhost", port=8080)
