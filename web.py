import os, time

import pymongo
from bottle import route, run, view, abort, request, redirect

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
    def __init__(self, data):
        self.name = data["name"]
        self.revision = data["revision"]
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
    def __init__(self, label, db):
        self.name = label
        self.branch = label.split("@")[1] # fl:2-devel etc
        self._bin_pkgs = {}
        self._src_pkgs = {}

        self._read_info(db)
        self._all_info_complete = False

    def _read_info(self, db):
        # read binary packages
        coll = db[self.branch + ":binary"]
        for pkgdata in coll.find():
            pkg = Package(pkgdata)
            self._bin_pkgs[pkg.name] = pkg

        # read src packages
        coll = db[self.branch + ":source"]
        for pkgdata in coll.find():
            pkg = SourceTrove(pkgdata)
            self._src_pkgs[pkg.name] = pkg

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
    def __init__(self, name, description, labels, db):
        self.name = name
        self.description = description
        self.labels = [Label(b, db) for b in labels]

    def get_pkgs(self, sort=True):
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

    def search_file(self, keyword, only_basename=False):
        ret = []
        if only_basename:
            func = lambda path: keyword in path.rsplit("/")[-1]
        else:
            func = lambda path: keyword in path
        for pkg in self.get_pkgs(sort=False):
            ret.extend([(path, pkg) for path in pkg.filelist if func(path)])
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
def search_pkg(keyword):
    keyword = keyword.decode("utf8")
    branch = request.query.branch
    if not branch or branch not in installs:
        branch = "qa"
    install = installs[branch]
    pkgs = install.search_pkg(keyword)
    return dict(install=install, pkgs=pkgs)

@route("/search/file/<keyword:path>")
@view("searchfile")
def search_file(keyword):
    keyword = keyword.decode("utf8")
    branch = request.query.branch
    if not branch or branch not in installs:
        branch = "qa"
    install = installs[branch]
    if request.query.mode == "fullpath":
        files = install.search_file(keyword)
    else:
        files = install.search_file(keyword, only_basename=True)
    return dict(install=install, files=files)

@route("/search", method="POST")
def receive_search():
    query = ""
    b = request.forms.branch
    if b in installs and b != "qa":
        query = "?branch=%s" % b

    if request.forms.searchtype == "file":
        # search only filename or fullpath
        if request.forms.mode == "fullpath":
            if "?" not in query:
                query += "?"
            else:
                query += "&"
            query += "mode=fullpath"
        redirect("/search/file/%s%s" % (request.forms.keyword.encode("utf8"), query))
    else:
        redirect("/search/%s%s" % (request.forms.keyword.encode("utf8"), query))

if __name__ == "__main__":
    conn = pymongo.Connection()
    db = conn.fl_pkgs
    installs = {}
    installs["stable"] = Install("stable", "This is the stable branch of \
            the Foresight Linux distribution. New release are usually made \
            from this branch. However, due to various reasons, this branch \
            hasn't been updated for a long time. Current releases are made \
            from the QA branch.", [
        "foresight.rpath.org@fl:2",
        "foresight.rpath.org@fl:2-kernel"], db)
    installs["qa"] = Install("qa", "This is the QA branch, which \
            is synced frequently with the devel branch, and is meant for \
            brave users who want to help with Foresight Linux development. \
            For various reasons, this branch is also used for official \
            releases.", [
        "foresight.rpath.org@fl:2-qa",
        "foresight.rpath.org@fl:2-qa-kernel"], db)

    run(server='gevent', host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
