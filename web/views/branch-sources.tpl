%rebase layout title="Source packages in %s branch" % branch.name

%include quick-search branch=branch.name

<h1>Source Packages in the <b>{{branch.name}}</b> branch</h1>

<p>
Showing {{start}}-{{min(start + limit - 1, branch.count_srcpkgs())}} of {{branch.count_srcpkgs()}}:
</p>

<ul>
%for pkg in pkgs:
  <li><a href="/{{branch.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>

%include pager url="/%s/source" % branch.name, start=start, limit=limit, total=branch.count_srcpkgs()
