%rebase layout title="Packages in %s branch" % branch.name

<h1>Software Packages in the <b>{{branch.name}}</b> branch (total: {{branch.count_binpkgs()}})</h1>

<ul>
%for pkg in branch.get_pkgs():
  <li><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
