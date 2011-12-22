<h1>Packages in Foresight Linux</h1>

<h2>View package lists</h2>

<dl>
%for install in installs:
  <dt><a href="/{{install.name}}">View the packages in the {{install.name}} branch</a></dt>
  <dd>{{install.description}}</dd>
%end
</dl>
