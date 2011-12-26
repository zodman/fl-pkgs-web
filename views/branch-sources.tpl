%rebase layout title="Source packages in %s branch" % branch.name

<h1>Source Packages in the <b>{{branch.name}}</b> branch</h1>

<p>
Showing {{start}}-{{start + limit - 1}} of {{branch.count_srcpkgs()}}:
</p>

<ul>
%for pkg in pkgs:
  <li><a href="/{{branch.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
