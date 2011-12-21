<h1>Software Packages in the <b>{{install.name}}</b> branch (total: {{len(install.get_pkgs())}})</h1>

<ul>
%for pkg in install.get_pkgs():
  <li><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
