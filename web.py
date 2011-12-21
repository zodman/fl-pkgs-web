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
        self.shortbranch = label.split(":")[1] # 2-devel etc

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
            abort(404, "%s doesn't have %s" % (self.name, name))
            return
        pkg.read_info()
        return pkg

labels = {
        "foresight.rpath.org@fl:2": Label("foresight.rpath.org@fl:2"),
        "foresight.rpath.org@fl:2-qa": Label("foresight.rpath.org@fl:2-qa"),
        }

@route("/")
@view("index")
def index():
    return {}

@route("/<b:re:(2|2-qa)>")
@view("label")
def show_label(b):
    if b == "2":
        label = "foresight.rpath.org@fl:2"
    elif b == "2-qa":
        label = "foresight.rpath.org@fl:2-qa"
    else:
        return
    return dict(label=labels[label])

@route("/<b:re:(2|2-qa)>/<pkg>")
@view("pkg")
def show_pkg(b, pkg):
    if b == "2":
        label = "foresight.rpath.org@fl:2"
    elif b == "2-qa":
        label = "foresight.rpath.org@fl:2-qa"
    else:
        return
    return dict(label=label, pkg=labels[label].get_pkg(pkg))

if __name__ == "__main__":
    run(host="localhost", port=8080, reloader=True)
