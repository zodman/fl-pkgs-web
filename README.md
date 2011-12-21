* cache.py: pull data from the conary repository (REST interface), and store in
  ./rawdata.
* convert.py: extract the information we are interested from the raw data
  (XML), and store in ./info (JSON).
  - test.py is a unittest for convert.py
* web.py: server the JSON data to the web.
  - serves both HTML and JSON

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
