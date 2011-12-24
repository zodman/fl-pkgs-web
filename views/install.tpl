<h1>Software Packages in the <b>{{install.name}}</b> branch (total: {{install.count_binpkgs()}})</h1>

<ul>
%for pkg in install.get_pkgs():
  <li><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
