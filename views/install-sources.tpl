<h1>Source Packages in the <b>{{install.name}}</b> branch (total: {{len(install.get_pkgs())}})</h1>

<ul>
%for pkg in install.get_src_pkgs():
  <li><a href="/{{install.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
