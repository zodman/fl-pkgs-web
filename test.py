#!/usr/bin/env python

import unittest

import convert

test_b = "foresight.rpath.org@fl:2-qa"
test_label = convert.Label(test_b, cache="datatest", read_pkg_details=False)

class TestXMLConvert(unittest.TestCase):
    def test_read_pkg_list(self):
        self.assertEqual(test_b, test_label.name)
        self.assertEqual(3503, len(test_label.get_pkgs()))

    def test_src_pkg_list(self):
        self.assertEqual(2269, len(test_label.get_src_pkgs()))

    def test_no_nil_pkg(self):
        self.assertEqual(0, len([p for p in test_label.get_pkgs() if p.revision.startswith("0-")]))
        self.assertEqual(0, len([p for p in test_label.get_src_pkgs() if p.revision.startswith("0-")]))

    def test_label_get_pkg(self):
        self.assertRaises(KeyError, test_label.get_pkg, "gitx")

    def test_src_pkg_info(self):
        pkg = [p for p in test_label.get_src_pkgs() if p.name == "git:source"][0]
        self.assertEqual(pkg.revision, "1.7.7-1")

    def test_read_pkg_info(self):
        pkg = test_label.get_pkg("git")
        pkg.read_info()
        self.assertEqual("git", pkg.name)
        self.assertEqual("1.7.7-1-1", pkg.revision)
        self.assertEqual(["is: x86", "is: x86_64"], pkg.flavors)
        self.assertEqual("git:source", pkg.source)
        self.assertEqual(146239829, pkg.size)
        self.assertEqual(1318314231, pkg.buildtime)
        self.assertEqual("http://conary.foresightlinux.org/conary/api/logfile/1546e65f9d9b8dafdd200fdd4c03fe920e50acc8", pkg.buildlog)
        self.assertEqual(pkg.included, [
            "git:config",
            "git:data",
            "git:debuginfo",
            "git:devel",
            "git:doc",
            "git:perl",
            "git:python",
            "git:runtime",
            "git:supdoc"])

    def test_subpkg_has_correct_source(self):
        pkg = test_label.get_pkg("git-svn")
        pkg.read_info()
        self.assertEqual("git:source", pkg.source)

    def test_no_flavor_pkg(self):
        pkg = test_label.get_pkg("wqy-zenhei")
        pkg.read_info()
        self.assertEqual([None], pkg.flavors)

    def test_no_flavor_pkg(self):
        pkg = test_label.get_pkg("wqy-zenhei")
        pkg.read_info()
        self.assertEqual([None], pkg.flavors)

    def test_more_than_2_flavors(self):
        pkg = test_label.get_pkg("gnucash")
        pkg.read_info()
        self.assertEqual(["~builddocs is: x86", "~!builddocs is: x86",
            "~builddocs is: x86_64", "~!builddocs is: x86_64"], pkg.flavors)

if __name__ == "__main__":
    unittest.main()
