import os, time, json

from bottle import route, run, view, abort, request

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
    def __init__(self, data):
        self.name = data["name"]
        self.revision = data["revision"]

        self.flavors = format_flavors(data["flavors"])
        self.size = format_size(data["size"])
        self.source = data["source"]
        self.buildtime = format_buildtime(data["buildtime"])
        self.buildlog = data["buildlog"]
        self.included = data["included"]
        self.filelist = data["filelist"]

class Label:
    def __init__(self, label):
        self.name = label
        self.branch = label.split("@")[1] # fl:2-devel etc
        self._bin_pkgs = {}
        self._src_pkgs = {}

        self._read_info()
        self._all_info_complete = False

    def _read_info(self):
        f = open("info/%s" % self.name)
        data = json.load(f)
        f.close()

        # read binary packages
        for pkgdata in data["pkgs"]:
            pkg = Package(pkgdata)
            self._bin_pkgs[pkg.name] = pkg

        # read src packages
        for name, revision in data["srcpkgs"]:
            pkg = SourceTrove(name, revision)
            self._src_pkgs[name] = pkg

        for k, p in self._bin_pkgs.items():
            # associate :source with relevant pkgs
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
        pkg = self._bin_pkgs[name]
        return pkg

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
    def __init__(self, name, description, labels):
        self.name = name
        self.description = description
        self.labels = [Label(b) for b in labels]

    def get_pkgs(self, sort=True):
        '''Note!: returned pkgs may not have detailed info yet. Only name and
        revision are ensured.
        '''
        ret = []
        for b in self.labels:
            ret.extend(b.get_pkgs())
        if sort:
            ret.sort(key=lambda p: p.name)
        return ret

    def get_src_pkgs(self, sort=True):
        ret = []
        for b in self.labels:
            ret.extend(b.get_src_pkgs())
        if sort:
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

    def search_pkg(self, keyword):
        ret = [pkg for pkg in self.get_pkgs(sort=False) +
                              self.get_src_pkgs(sort=False)
                if keyword in pkg.name]
        ret.sort(key=lambda pkg: pkg.name)
        return ret

    def search_file(self, keyword):
        ret = []
        for pkg in self.get_pkgs(sort=False):
            ret.extend([(path, pkg) for path in pkg.filelist
                if keyword in path])
        ret.sort(key=lambda e: e[0])
        return ret

installs = {}

@route("/")
@view("index")
def index():
    return dict(installs=installs.values())

@route("/<inst:re:(stable|qa)>")
@view("install")
def show_install(inst):
    return dict(install=installs[inst])

@route("/<inst:re:(stable|qa)>/source")
@view("install-sources")
def show_install_sources(inst):
    '''List :source packages
    '''
    return dict(install=installs[inst])

@route("/<inst:re:(stable|qa)>/<pkg>")
@view("pkg")
def show_pkg(inst, pkg):
    install = installs[inst]
    return dict(install=install, pkg=install.get_pkg(pkg))

@route("/<inst:re:(stable|qa)>/<pkg>/filelist")
@view("filelist")
def show_pkg_filelist(inst, pkg):
    install = installs[inst]
    return dict(install=install, pkg=install.get_pkg(pkg))

@route("/<inst:re:(stable|qa)>/source/<pkg>")
@view("srcpkg")
def show_src_pkg(inst, pkg):
    install = installs[inst]
    return dict(install=install, src=install.get_src_pkg(pkg))

@route("/search/<keyword>")
@view("searchpkg")
def search(keyword):
    branch = request.query.branch
    if not branch or branch not in installs:
        branch = "qa"
    pkgs = installs[branch].search_pkg(keyword)
    return dict(pkgs=pkgs)

@route("/search/file/<keyword>")
@view("searchfile")
def search(keyword):
    branch = request.query.branch
    if not branch or branch not in installs:
        branch = "qa"
    files = installs[branch].search_file(keyword)
    return dict(files=files)

if __name__ == "__main__":
    installs = {}
    installs["stable"] = Install("stable", "This is the stable branch of \
            the Foresight Linux distribution. New release are usually made \
            from this branch. However, due to various reasons, this branch \
            hasn't been updated for a long time. Current releases are made \
            from the QA branch.", [
        "foresight.rpath.org@fl:2",
        "foresight.rpath.org@fl:2-kernel"])
    installs["qa"] = Install("qa", "This is the QA branch, which \
            is synced frequently with the devel branch, and is meant for \
            brave users who want to help with Foresight Linux development. \
            For various reasons, this branch is also used for official \
            releases.", [
        "foresight.rpath.org@fl:2-qa",
        "foresight.rpath.org@fl:2-qa-kernel"])

    run(host="localhost", port=8080)
