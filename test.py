#!/usr/bin/env python

import unittest

import convert

test_b = "foresight.rpath.org@fl:2-qa"
test_label = convert.Label([test_b], cache="datatest")

class TestXMLConvert(unittest.TestCase):
    def test_read_pkg_list(self):
        self.assertEqual(3578, len(test_label.bin_pkgs))

    def test_src_pkg_list(self):
        self.assertEqual(2269, len(test_label.src_pkgs))

    def test_no_nil_pkg(self):
        self.assertEqual(0, len([p for p in test_label.bin_pkgs.values() if p.revision.startswith("0-")]))
        self.assertEqual(0, len([p for p in test_label.src_pkgs.values() if p.revision.startswith("0-")]))

    def test_label_get_pkg(self):
        self.assertEqual(None, test_label.bin_pkgs.get("gitx", None))

    def test_src_pkg_info(self):
        pkg = test_label.src_pkgs["git:source"]
        self.assertEqual(pkg.revision, "1.7.7-1")

    def test_read_pkg_info(self):
        pkg = test_label.bin_pkgs["git"]
        pkg.read_info(with_filelist=False)
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
        pkg = test_label.bin_pkgs["git-svn"]
        pkg.read_info(with_filelist=False)
        self.assertEqual("git:source", pkg.source)

    def test_no_flavor_pkg(self):
        pkg = test_label.bin_pkgs["wqy-zenhei"]
        pkg.read_info(with_filelist=False)
        self.assertEqual([None], pkg.flavors)

    def test_no_flavor_pkg(self):
        pkg = test_label.bin_pkgs["wqy-zenhei"]
        pkg.read_info(with_filelist=False)
        self.assertEqual([None], pkg.flavors)

    def test_more_than_2_flavors(self):
        pkg = test_label.bin_pkgs["gnucash"]
        pkg.read_info(with_filelist=False)
        self.assertEqual(
                sorted(["~builddocs is: x86", "~!builddocs is: x86",
                    "~builddocs is: x86_64", "~!builddocs is: x86_64"]),
                sorted(pkg.flavors))

class TestFilelistParser(unittest.TestCase):
    def test_read_filelist(self):
        self.assertEqual(76,
            len(convert.read_trove_filelist("datatest/git:data-1.7.7-1-1")))

if __name__ == "__main__":
    unittest.main()
