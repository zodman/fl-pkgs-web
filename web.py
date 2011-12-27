import os, time, re, urllib

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
            return None

    def get_src_pkg(self, name):
        '''Could return None
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
            return None

    def search_pkg(self, keyword, skip=0, limit=50):
        pkgs = self._bin_pkgs.find({"name": re.compile(keyword, re.IGNORECASE)},
                skip=skip, limit=limit, fields={"filelist": False},
                sort=[("name", pymongo.ASCENDING)])
        total = pkgs.count()
        pkgs = [Package(pkg) for pkg in pkgs]
        return pkgs, total

    def search_src_pkg(self, keyword, skip=0, limit=50):
        if keyword.endswith(":source"):
            keyword = keyword.split(":")[0]
        keyword += ".*:source"
        pkgs = self._src_pkgs.find(
                {"name": re.compile(keyword, re.IGNORECASE)},
                skip=skip, limit=limit,
                sort=[("name", pymongo.ASCENDING)])
        total = pkgs.count()
        pkgs = [SourceTrove(pkg) for pkg in pkgs]
        return pkgs, total

    def search_file(self, keyword, searchon="path"):
        '''@searchon can be path, filename or fullpath. Default is path,
        searching for path ending with @keyword.

        These searchon terms are referenced in several places. Don't forget to
        change them together.
        '''
        # needs rethinking
        keyword = keyword.lower()
        ret = []
        if searchon == "fullpath":
            func = lambda path: keyword in path.lower()
        elif searchon == "filename":
            func = lambda path: keyword in path.rsplit("/")[-1].lower()
        else:
            func = lambda path: path.lower().endswith(keyword)
        for pkg in self._bin_pkgs.find():
            ret.extend([(path, Package(pkg)) for path in pkg["filelist"]
                if func(path)])
        ret.sort(key=lambda tup: tup[0])
        return ret

branches = {}

url_branches = "<b:re:(stable|qa|devel)>"

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

    start is counted from 1 here (and in the views). But in the db and in
    Branch it's from 0.
    '''
    start = get_value_gt(request.query.start, minim=1, default=1)
    limit = get_value_gt(request.query.limit, minim=1, default=50)
    return start, limit

@route("/")
@view("index")
def index():
    order = {"stable": 0, "qa": 1, "devel": 2}
    bs = branches.values()
    bs = sorted(bs, key=lambda b: order[b.name])
    return dict(branches=bs)

@route("/%s" % url_branches)
@view("branch")
def show_branch(b):
    start, limit = get_pagination(request.query)
    branch = branches[b]
    pkgs = branch.get_pkgs(start - 1, limit)
    return dict(branch=branch, pkgs=pkgs, start=start, limit=limit)

@route("/%s/source" % url_branches)
@view("branch-sources")
def show_branch_sources(b):
    '''List :source packages
    '''
    start, limit = get_pagination(request.query)
    branch = branches[b]
    pkgs = branch.get_src_pkgs(start - 1, limit)
    return dict(branch=branch, pkgs=pkgs, start=start, limit=limit)

@route("/%s/<pkg>" % url_branches)
@view("pkg")
def show_pkg(b, pkg):
    branch = branches[b]
    pkg = branch.get_pkg(pkg)
    if not pkg:
        abort(404, "No found")
    return dict(branch=branch, pkg=pkg)

@route("/%s/<pkg>/filelist" % url_branches)
@view("filelist")
def show_pkg_filelist(b, pkg):
    branch = branches[b]
    pkg = branch.get_pkg(pkg, with_filelist=True)
    if not pkg:
        abort(404, "No found")
    return dict(branch=branch, pkg=pkg)

@route("/%s/source/<pkg>" % url_branches)
@view("srcpkg")
def show_src_pkg(b, pkg):
    branch = branches[b]
    src = branch.get_src_pkg(pkg)
    if not src:
        abort(404, "No found")
    return dict(branch=branch, src=src)

@route("/search/%s/<searchon:re:(package|source)>/<keyword>" % url_branches)
@view("searchpkg")
def search_pkg(b, searchon, keyword):
    start, limit = get_pagination(request.query)
    keyword = keyword.decode("utf8")
    branch = branches[b]
    if searchon == "source":
        pkgs, total = branch.search_src_pkg(keyword, start - 1, limit)
    else:
        pkgs, total = branch.search_pkg(keyword, start - 1, limit)
    return dict(pkgs=pkgs, total=total, keyword=keyword, searchon=searchon,
            branch=branch, start=start, limit=limit)

@route("/search/%s/<searchon:re:filename>/<keyword>" % url_branches)
@route("/search/%s/<searchon:re:(fullpath|path)>/<keyword:path>" % url_branches)
@view("searchfile")
def search_file(b, searchon, keyword):
    keyword = keyword.decode("utf8")
    branch = branches[b]
    files = branch.search_file(keyword, searchon=searchon)
    return dict(files=files, keyword=keyword, searchon=searchon, branch=branch)

@route("/search", method="POST")
def receive_search():
    b = request.forms.branch
    if not b in branches:
        b = "qa"

    keyword = urllib.quote(request.forms.keyword.encode("utf8"))

    searchtype = request.forms.searchtype
    mode = request.forms.mode
    if searchtype == "file":
        if mode not in ("path", "filename", "fullpath"):
            mode = "path"
    else: # search for pkg
        if mode not in ("source", "package"):
            mode = "package"
    redirect("/search/%s/%s/%s" % (b, mode, keyword))

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
    branches["devel"] = Branch("devel", "This is the devel branch, where \
            Foresight Linux development happens. All binary packages are \
            built against this branch.", "fl:2-devel", db)

    run(server='gevent', host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
