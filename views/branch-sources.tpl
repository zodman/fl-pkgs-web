%rebase layout title="Source packages in %s branch" % branch.name

<h1>Source Packages in the <b>{{branch.name}}</b> branch (total: {{branch.count_srcpkgs()}})</h1>

<ul>
%for pkg in branch.get_src_pkgs():
  <li><a href="/{{branch.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
