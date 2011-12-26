import os, time, re

import pymongo
from bottle import route, run, view, abort, request, redirect, static_file

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

class Branch:
    def __init__(self, name, description, branch, db):
        '''A Branch can contain one or more conary labels
        '''
        self.name = name
        self.description = description

        self._bin_pkgs = db[branch + ":binary"]
        self._src_pkgs = db[branch + ":source"]

    def get_pkgs(self, skip=0, limit=50):
        pkgs = self._bin_pkgs.find(fields={"filelist": False},
                skip=skip, limit=limit, sort=[("name", pymongo.ASCENDING)])
        return [Package(pkg) for pkg in pkgs]

    def count_binpkgs(self):
        return self._bin_pkgs.count()

    def get_src_pkgs(self, skip=0, limit=50):
        pkgs = self._src_pkgs.find(skip=skip, limit=limit,
                sort=[("name", pymongo.ASCENDING)])
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
            abort(404, "No such page")

    def get_src_pkg(self, name):
        '''Could raise KeyError
        '''
        if not ":" in name:
            name += ":source"
        pkg = self._src_pkgs.find_one({"name": name})
        if pkg:
            binpkgs = self._bin_pkgs.find({"source": name},
                    fields={"filelist": False},
                    sort=[("name", pymongo.ASCENDING)])
            pkg["binpkgs"] = [Package(p) for p in binpkgs]
            return SourceTrove(pkg)
        else:
            abort(404, "No such page")

    def search_pkg(self, keyword, skip=0, limit=50):
        pkgs = self._bin_pkgs.find({"name": re.compile(keyword, re.IGNORECASE)},
                skip=skip, limit=limit, fields={"filelist": False},
                sort=[("name", pymongo.ASCENDING)])
        total = pkgs.count()
        pkgs = [Package(pkg) for pkg in pkgs]
        return pkgs, total

    def search_file(self, keyword, only_basename=False):
        # needs rethinking
        ret = []
        if only_basename:
            func = lambda path: keyword.lower() in path.rsplit("/")[-1].lower()
        else:
            func = lambda path: keyword.lower() in path.lower()
        for pkg in self._bin_pkgs.find():
            ret.extend([(path, Package(pkg)) for path in pkg["filelist"]
                if func(path)])
        ret.sort(key=lambda tup: tup[0])
        return ret

branches = {}

def get_value_gt(value, minim, default):
    '''Cast @value to int, making sure it's greater than @minim. If not, return
    @default.
    '''
    try:
        ret = int(value)
    except:
        ret = default
    if ret < minim:
        ret = default
    return ret

def get_pagination(query):
    '''Get pagination info. Return requested start and limit
    '''
    start = get_value_gt(request.query.start, minim=1, default=1)
    limit = get_value_gt(request.query.limit, minim=1, default=50)
    return start, limit

@route("/")
@view("index")
def index():
    return dict(branches=branches.values())

@route("/<b:re:(stable|qa)>")
@view("branch")
def show_branch(b):
    start, limit = get_pagination(request.query)
    branch = branches[b]
    pkgs = branch.get_pkgs(start - 1, limit)
    return dict(branch=branch, pkgs=pkgs, start=start, limit=limit)

@route("/<b:re:(stable|qa)>/source")
@view("branch-sources")
def show_branch_sources(b):
    '''List :source packages
    '''
    start, limit = get_pagination(request.query)
    branch = branches[b]
    pkgs = branch.get_src_pkgs(start - 1, limit)
    return dict(branch=branch, pkgs=pkgs, start=start, limit=limit)

@route("/<b:re:(stable|qa)>/<pkg>")
@view("pkg")
def show_pkg(b, pkg):
    branch = branches[b]
    return dict(branch=branch, pkg=branch.get_pkg(pkg))

@route("/<b:re:(stable|qa)>/<pkg>/filelist")
@view("filelist")
def show_pkg_filelist(b, pkg):
    branch = branches[b]
    return dict(branch=branch, pkg=branch.get_pkg(pkg, with_filelist=True))

@route("/<b:re:(stable|qa)>/source/<pkg>")
@view("srcpkg")
def show_src_pkg(b, pkg):
    branch = branches[b]
    return dict(branch=branch, src=branch.get_src_pkg(pkg))

@route("/search/<b:re:(stable|qa)>/package/<keyword>")
@view("searchpkg")
def search_pkg(b, keyword):
    start, limit = get_pagination(request.query)
    keyword = keyword.decode("utf8")
    branch = branches[b]
    pkgs, total = branch.search_pkg(keyword, start, limit)
    return dict(pkgs=pkgs, total=total, keyword=keyword, branch=branch,
            start=start, limit=limit)

@route("/search/<b:re:(stable|qa)>/<searchon:re:file/<keyword>")
@route("/search/<b:re:(stable|qa)>/<searchon:re:path/<keyword:path>")
@view("searchfile")
def search_file(b, keyword):
    keyword = keyword.decode("utf8")
    branch = branches[b]
    if searchon == "path":
        files = branch.search_file(keyword)
    else:
        files = branch.search_file(keyword, only_basename=True)
    return dict(files=files, keyword=keyword, branch=branch)

@route("/search", method="POST")
def receive_search():
    b = request.forms.branch
    if not b in branches:
        b = "qa"

    keyword = request.forms.keyword.encode("utf8")
    if request.forms.searchtype == "file":
        # search only filename or fullpath
        if request.forms.mode == "fullpath":
            redirect("/search/%s/file/%s" % (b, keyword))
        else:
            redirect("/search/%s/path/%s" % (b, keyword))
    else:
        redirect("/search/%s/package/%s" % (b, keyword))

@route("/static/<filename:path>")
def serve_static(filename):
    return static_file(filename, root="static")

if __name__ == "__main__":
    conn = pymongo.Connection()
    db = conn.fl_pkgs
    branches = {}
    branches["stable"] = Branch("stable", "This is the stable branch of \
            the Foresight Linux distribution. New release are usually made \
            from this branch. However, due to various reasons, this branch \
            hasn't been updated for a long time. Current releases are made \
            from the QA branch.", "fl:2", db)
    branches["qa"] = Branch("qa", "This is the QA branch, which \
            is synced frequently with the devel branch, and is meant for \
            brave users who want to help with Foresight Linux development. \
            For various reasons, this branch is also used for official \
            releases.", "fl:2-qa", db)

    run(server='gevent', host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
