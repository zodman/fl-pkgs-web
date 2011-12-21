* cache.py: pull data from the conary repository (REST interface), and store in
  ./rawdata.
* convert.py: extract the information we are interested from the raw data
  (XML), and store in ./info (JSON).
  - test.py is a unittest for convert.py
* web.py: server the JSON data to the web.
  - serves both HTML and JSON
