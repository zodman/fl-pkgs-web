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
        self.binpkgs = data.get("binpkgs", [])

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
        self.filelist = data.get("filelist", [])

class Label:
    def __init__(self, label, db):
        self.name = label
        self.branch = label.split("@")[1] # fl:2-devel etc
        self._src_pkgs = {}

        self._bin_pkgs = db[self.branch + ":binary"]
        self._src_pkgs = db[self.branch + ":source"]

    def get_pkgs(self):
        pkgs = self._bin_pkgs.find(fields={"filelist": False})
        return [Package(pkg) for pkg in pkgs]

    def count_binpkgs(self):
        return self._bin_pkgs.count()

    def get_src_pkgs(self):
        pkgs = self._src_pkgs.find()
        return [SourceTrove(pkg) for pkg in pkgs]

    def count_srcpkgs(self):
        return self._src_pkgs.count()

    def get_pkg(self, name, with_filelist=False):
        '''Could return None
        '''
        if with_filelist:
            pkg = self._bin_pkgs.find_one({"name": name})
        else:
            pkg = self._bin_pkgs.find_one({"name": name},
                    fields={"filelist": False})
        if pkg:
            return Package(pkg)
        else:
            return None

    def get_src_pkg(self, name):
        '''Could raise KeyError
        '''
        if not ":" in name:
            name += ":source"
        pkg = self._src_pkgs.find_one({"name": name})
        if pkg:
            binpkgs = self._bin_pkgs.find({"source": name},
                    fields={"filelist": False})
            pkg["binpkgs"] = [Package(p) for p in binpkgs]
            return SourceTrove(pkg)
        else:
            return None

    def search_pkg(self, keyword):
        ret = self._bin_pkgs.find({"name": {"$regex": ".*%s.*" % keyword}},
                fields={"filelist": False})
        ret = [Package(pkg) for pkg in ret]
        return ret

    def search_file(self, keyword, only_basename=False):
        # needs rethinking
        ret = []
        if only_basename:
            func = lambda path: keyword in path.rsplit("/")[-1]
        else:
            func = lambda path: keyword in path
        for pkg in self._bin_pkgs.find():
            ret.extend([(path, Package(pkg)) for path in pkg["filelist"]
                if func(path)])
        return ret

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

    def count_binpkgs(self):
        return sum([b.count_binpkgs() for b in self.labels])

    def get_src_pkgs(self, sort=True):
        ret = []
        for b in self.labels:
            ret.extend(b.get_src_pkgs())
        if sort:
            ret.sort(key=lambda p: p.name)
        return ret

    def count_srcpkgs(self):
        return sum([b.count_srcpkgs() for b in self.labels])

    def get_pkg(self, name, with_filelist=False):
        for b in self.labels:
            pkg = b.get_pkg(name, with_filelist)
            if pkg:
                return pkg
            else:
                continue
        abort(404, "No such page")

    def get_src_pkg(self, name):
        for b in self.labels:
            pkg = b.get_src_pkg(name)
            if pkg:
                return pkg
            else:
                continue
        abort(404, "No such page")

    def search_pkg(self, keyword):
        ret = []
        for b in self.labels:
            ret.extend(b.search_pkg(keyword))
        ret.sort(key=lambda pkg: pkg.name)
        return ret

    def search_file(self, keyword, only_basename=False):
        ret = []
        for b in self.labels:
            ret.extend(b.search_file(keyword, only_basename))
        ret.sort(key=lambda tup: tup[0])
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
    return dict(install=install, pkg=install.get_pkg(pkg, with_filelist=True))

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
    return dict(pkgs=pkgs, keyword=keyword, install=install)

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
    return dict(files=files, keyword=keyword, install=install)

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
