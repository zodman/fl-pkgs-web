<h1>Packages in Foresight Linux</h1>

<h2>View package lists</h2>

<dl>
%for install in installs:
  <dt><a href="/{{install.name}}">View the packages in the {{install.name}} branch</a>
    (<a href="/{{install.name}}/source">view source packages</a>)</dt>
  <dd>{{install.description}}</dd>
%end
</dl>

<h2>Search package directories</h2>
Search packages by name.
<form action="/search" method="post">
  <label for="kw">Keyword:</label>
  <input id="kw" type="text" name="keyword" //>
  <input type="submit" value="Search" />
  <br />
  <label for="branch">Branch:</label>
  <select id="branch" name="branch">
    <option value="stable">stable</option>
    <option selected="selected" value="qa">qa</option>
  </select>
</form>

<h2>Search the contents of packages</h2>
Search the contents of Foresight Linux distributions for any files that are
part of packages. You can also get a full list of files in a given package.

<form action="/search" method="post">
  <label for="kw">Keyword:</label>
  <input id="kw" type="text" name="keyword" />
  <input type="submit" value="Search" />
  <br />
  <label for="branch">Branch:</label>
  <select id="branch" name="branch">
    <option value="stable">stable</option>
    <option selected="selected" value="qa">qa</option>
  </select>
  <input type="hidden" name="searchtype" value="file"/>
</form>
