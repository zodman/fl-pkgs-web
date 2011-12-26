%rebase layout title="Packages in %s branch" % branch.name

<h1>Software Packages in the <b>{{branch.name}}</b> branch</h2>

<p>
Showing {{start}}-{{min(start + limit - 1, branch.count_binpkgs())}} of {{branch.count_binpkgs()}}:
</p>

<ul>
%for pkg in pkgs:
  <li><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>

%include pager url="/" + branch.name, start=start, limit=limit, total=branch.count_binpkgs()
