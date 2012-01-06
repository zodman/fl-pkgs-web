* cache.py: pull data from the conary repository (REST interface), and store in
  `./rawdata`.
* convert.py: extract the information we are interested from the raw data
  (XML), and store in the mongodb.
  - test.py is a unittest for convert.py
* web.py: server the data to the web.

* dataflow:

        +----------------+             +-------------+               +-------+
        |   repository   |  cache.py   | local cache |  convert.py   | mongo |
        |(REST interface)| ----------> |    (XML)    | ------------> |       |
        +----------------+             +-------------+               +-------+

* usage:
  - python cache.py | tee log-cache
  - python convert.py | tee log-convert
  - python web.py

* taxonomy. In general the variables and classes are named using conary
  concepts, with a few exceptions such as "install".
  - repository: foresight.rpath.org
  - label: foresight.rpath.org@fl:2-devel
  - branch: fl:2-devel
  - install: a group of labels that are usually installed together to create a
    foresight release. For example foresight.rpath.org@fl:2 and
    foresight.rpath.org@fl:2-kernel.

* issues:
  - userspace-kernel-firmware is available on both 2-qa and 2-qa-kernel. Not
    sure how to handle it.

* requirement:
  - bottle
  - gevent (can be easily replaced)
  - mongodb and pymongo

* cached data size
  - included labels: fl:2, fl:2-kernel, fl:2-qa, fl:2-qa-kernel, fl:2-devel,
    fl:2-devel-kernel
  - 2.9G    rawdata

* database size:
  -  65M fl_pkgs.0
  - 129M fl_pkgs.1
  - 257M fl_pkgs.2
  - 513M fl_pkgs.3
  -  17M fl_pkgs.ns
