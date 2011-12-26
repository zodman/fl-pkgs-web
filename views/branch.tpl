%rebase layout title="Packages in %s branch" % branch.name

<h1>Software Packages in the <b>{{branch.name}}</b> branch</h2>

<p>
Showing {{start}}-{{start + limit - 1}} of {{branch.count_binpkgs()}}:
</p>

<ul>
%for pkg in pkgs:
  <li><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
