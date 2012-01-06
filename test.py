#!/usr/bin/env python

import unittest

import convert

test_b = "foresight.rpath.org@fl:2-qa"
test_label = convert.Label([test_b], cache="datatest")

test_label2 = convert.Label(["foresight.rpath.org@fl:2-devel"], cache="datatest")

class TestXMLConvert(unittest.TestCase):
    def test_read_pkg_list(self):
        self.assertEqual(3274, len(test_label.bin_pkgs))

    def test_src_pkg_list(self):
        self.assertEqual(2265, len(test_label.src_pkgs))

    def test_no_nil_pkg(self):
        self.assertEqual(0, len([p for p in test_label.bin_pkgs.values() if p.revision.startswith("0-")]))
        self.assertEqual(0, len([p for p in test_label.src_pkgs.values() if p.revision.startswith("0-")]))

    def test_subpkg_is_nil(self):
        # sub-pkg, where the main pkg has been nil
        self.assertTrue("gcc-java" not in test_label.bin_pkgs)
        src = test_label.src_pkgs["gcc:source"]
        # currently there are 8 pkgs built from gcc:source
        self.assertEqual(8, len(src.binpkgs))

    def test_pkg_older_than_src(self):
        # pkg whose latest recipe is not built yet
        src = test_label2.src_pkgs["valgrind:source"]
        pkg = test_label2.bin_pkgs["valgrind"]
        self.assertEqual(src.revision, "3.7.0-0.3")
        self.assertEqual(pkg.revision, "3.7.0-0.2-1")
        self.assertTrue(pkg.name in src.binpkgs)

    def test_mainpkg_non_existent(self):
        # :source that doesn't have a same-named main pkg.
        # from xorg-libs:source, there is not a real xorg-libs (only
        # :debuginfo). it's available in 2-devel, but not in 2-qa.
        src = test_label.src_pkgs["xorg-libs:source"]
        self.assertEqual(src.revision, "7.6-3")
        self.assertEqual(None, test_label.bin_pkgs.get("xorg-libs", None))

        pkg = test_label.bin_pkgs["xcb-util"]
        self.assertEqual(pkg.revision, "7.6-3-1")
        self.assertTrue(pkg.name in src.binpkgs)

    def test_label_get_pkg(self):
        self.assertEqual(None, test_label.bin_pkgs.get("gitx", None))

    def test_src_pkg_info(self):
        pkg = test_label.src_pkgs["git:source"]
        self.assertEqual(pkg.revision, "1.7.7-1")

    def test_read_pkg_info(self):
        pkg = test_label.bin_pkgs["git"]
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
        self.assertEqual("git:source", pkg.source)

    def test_no_flavor_pkg(self):
        pkg = test_label.bin_pkgs["wqy-zenhei"]
        self.assertEqual([None], pkg.flavors)

    def test_more_than_2_flavors(self):
        pkg = test_label.bin_pkgs["gnucash"]
        self.assertEqual(
                sorted(["~builddocs is: x86", "~!builddocs is: x86",
                    "~builddocs is: x86_64", "~!builddocs is: x86_64"]),
                sorted(pkg.flavors))

    def test_source_correct_revision(self):
        pkg = test_label.src_pkgs["Mesa:source"]
        self.assertEqual(pkg.revision, "7.10.3-3")

class TestFilelistParser(unittest.TestCase):
    def test_read_filelist(self):
        self.assertEqual(76,
            len(convert.read_trove_filelist("datatest/git:data-1.7.7-1-1")))

if __name__ == "__main__":
    unittest.main()
