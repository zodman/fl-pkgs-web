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

    def get_pkgs(self):
        pkgs = self._bin_pkgs.find(fields={"filelist": False},
                sort=[("name", pymongo.ASCENDING)])
        return [Package(pkg) for pkg in pkgs]

    def count_binpkgs(self):
        return self._bin_pkgs.count()

    def get_src_pkgs(self):
        pkgs = self._src_pkgs.find(sort=[("name", pymongo.ASCENDING)])
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

    def search_pkg(self, keyword):
        ret = self._bin_pkgs.find({"name": re.compile(keyword, re.IGNORECASE)},
                fields={"filelist": False}, sort=[("name", pymongo.ASCENDING)])
        ret = [Package(pkg) for pkg in ret]
        return ret

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

def parse_search_term(keyword, query):
    keyword = keyword.decode("utf8")
    b = query.branch
    if not b or b not in branches:
        b = "qa"
    branch = branches[b]
    return keyword, branch

@route("/")
@view("index")
def index():
    return dict(branches=branches.values())

@route("/<b:re:(stable|qa)>")
@view("branch")
def show_branch(b):
    return dict(branch=branches[b])

@route("/<b:re:(stable|qa)>/source")
@view("branch-sources")
def show_branch_sources(b):
    '''List :source packages
    '''
    return dict(branch=branches[b])

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

@route("/search/<keyword>")
@view("searchpkg")
def search_pkg(keyword):
    keyword, branch = parse_search_term(keyword, request.query)
    pkgs = branch.search_pkg(keyword)
    return dict(pkgs=pkgs, keyword=keyword, branch=branch)

@route("/search/file/<keyword:path>")
@view("searchfile")
def search_file(keyword):
    keyword, branch = parse_search_term(keyword, request.query)
    if request.query.mode == "fullpath":
        files = branch.search_file(keyword)
    else:
        files = branch.search_file(keyword, only_basename=True)
    return dict(files=files, keyword=keyword, branch=branch)

@route("/search", method="POST")
def receive_search():
    query = ""
    b = request.forms.branch
    if b in branches and b != "qa":
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
