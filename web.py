import json

from bottle import route, run, view, abort

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
        self.flavors = data["flavors"]
        self.size = data["size"]
        self.source = data["source"]
        self.buildtime = data["buildtime"]
        self.buildlog = data["buildlog"]
        self.included = data["included"]

        self._info_complete = True

class Label:
    def __init__(self, label):
        self.pkgs = {}
        self.name = label
        self.branch = label.split("@")[1] # fl:2-devel etc

        # read json data
        f = open("info/%s" % self.name)
        data = json.load(f)
        f.close()
        for name, revision in data["pkgs"]:
            if revision.startswith("0-"):
                # nil pkg
                continue
            self.pkgs[name] = Package(name, revision, self)

    def get_pkgs(self):
        return self.pkgs.values()

    def get_pkg(self, name):
        try:
            pkg = self.pkgs[name]
        except KeyError:
            abort(404, "No such page")
            return
        pkg.read_info()
        return pkg

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

    def get_pkg(self, name):
        for b in self.labels:
            try:
                pkg = b.get_pkg(name)
                return pkg
            except KeyError:
                continue
        raise KeyError

installs = {
        "2": Install("2", [
                "foresight.rpath.org@fl:2",
                "foresight.rpath.org@fl:2-kernel"]),
        "2-qa": Install("2-qa", [
                "foresight.rpath.org@fl:2-qa",
                "foresight.rpath.org@fl:2-qa-kernel"]),
        }

@route("/")
@view("index")
def index():
    return {}

@route("/<inst:re:(2|2-qa)>")
@view("install")
def show_install(inst):
    return dict(install=installs[inst])

@route("/<inst:re:(2|2-qa)>/<pkg>")
@view("pkg")
def show_pkg(inst, pkg):
    install = installs[inst]
    return dict(install=install, pkg=install.get_pkg(pkg))

if __name__ == "__main__":
    run(host="localhost", port=8080, reloader=True)
