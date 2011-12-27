%rebase layout title="Packages"

<h1>Packages in Foresight Linux</h1>

<p>
Bonjour! Here you can find information about packages from the Foresight Linux
repository.
</p>
<p>
Any issues you spot, please kindly let us know through the forum or
our issue tracking system FITS.
</p>

<h2>View package lists</h2>

<dl>
%for branch in branches:
  <dt><a href="/{{branch.name}}">View the packages in the {{branch.name}} branch</a>
    (<a href="/{{branch.name}}/source">view source packages</a>)</dt>
  <dd><p>{{branch.description}}</p></dd>
%end
</dl>

<h2>Search package directories</h2>
Search packages by name.

<p>
<form action="/search" method="post">
  <label for="kw">Keyword:</label>
  <input id="kw" type="text" name="keyword" //>
  <input type="submit" value="Search" />
  <br />
  <label for="branch">Branch:</label>
  <select id="branch" name="branch">
    <option value="stable">stable</option>
    <option selected="selected" value="qa">qa</option>
    <option value="devel">devel</option>
  </select>
</form>
</p>

<h2>Search the contents of packages</h2>
Search the contents of Foresight Linux distributions for any files that are
part of packages. You can also get a full list of files in a given package.

<p>
<form action="/search" method="post">
  <input type="hidden" name="searchtype" value="file"/>
  <label for="kw">Keyword:</label>
  <input id="kw" type="text" name="keyword" />
  <input type="submit" value="Search" />
  <br />
  Display:
  <br />
  <input id="searchpathending" type="radio" value="pathending" name="mode" checked="checked" />
  <label for="searchpathending">paths ending with the keyword</label>
  <br />
  <input id="searchfile" type="radio" value="filename" name="mode" />
  <label for="searchfile">filenames containing the keyword</label>
  <br />
  <input id="searchpath" type="radio" value="fullpath" name="mode" />
  <label for="searchpath">paths containing the keyword</label>
  <br />
  <label for="branch">Branch:</label>
  <select id="branch" name="branch">
    <option value="stable">stable</option>
    <option selected="selected" value="qa">qa</option>
    <option value="devel">devel</option>
  </select>
</form>
</p>

<div class="footer">
  Any issue with this website, please report to
  <a href="https://github.com/zhangsen/fl-pkgs-web">the github page</a>.
</div>
