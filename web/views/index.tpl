%rebase layout title="Packages"

<h1>Packages in Foresight Linux</h1>

<p>
Bonjour! Here you can find information about packages from the Foresight Linux
repository.
</p>
<p>
Any issues you spot, let us know through the forum or the issue tracking system
FITS.
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
<p>Search packages by name.</p>

<form action="/search" method="post">
<fieldset>
  <label for="pkw">Keyword:</label>
	<div class="input">
	  	<input id="pkw" type="text" name="keyword" />
  		<input type="submit" value="Search" />
	</div>
	<div class="input">
		<ul class="inputs-list">
			<li> 
				<label>
				<input id="searchbin" type="radio" checked="checked" value="package" name="searchon"/>
				<span>Packages names</span>
				</label>
			</li>
			<li>	
				<label>
				<input id="searchsrc" type="radio" value="source" name="searchon"/>
				<span>Source packages names</span>
				</label>

			</li>
		</ul>

	</div>
  <br/>
  <label for="pbranch">Branch:</label>
  <div class="input">
	  <select id="pbranch" name="branch">
	    <option value="stable">stable</option>
	    <option selected="selected" value="qa">qa</option>
	    <option value="devel">devel</option>
	  </select>
  </div>
</fieldset>
</form>

<h2>Search the contents of packages</h2>
<p>
Search the contents of Foresight Linux distributions for any files that are
part of packages. You can also get a full list of files in a given package.
</p>

<form action="/search" method="post">
<fieldset>
  <label for="fkw">Keyword:</label>
  <input id="kfw" type="text" name="keyword" />
  <input type="submit" value="Search" />
  <br />
  Display:
  <br />
  <input id="searchpathending" type="radio" value="path" name="searchon" checked="checked" />
  <label for="searchpathending">paths ending with the keyword</label>
  <br />
  <input id="searchfile" type="radio" value="filename" name="searchon" />
  <label for="searchfile">filenames containing the keyword</label>
  <br />
  <input id="searchpath" type="radio" value="fullpath" name="searchon" />
  <label for="searchpath">paths containing the keyword</label>
  <br />
  <label for="fbranch">Branch:</label>
  <select id="fbranch" name="branch">
    <option value="stable">stable</option>
    <option selected="selected" value="qa">qa</option>
    <option value="devel">devel</option>
  </select>
</fieldset>
</form>

<div class="footer">
  Any issue with this website, please report to
  <a href="https://github.com/zhangsen/fl-pkgs-web">the github page</a>.
</div>
