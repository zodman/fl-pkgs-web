<p>Page for the <b>{{install.name}}</b> branch ({{len(install.get_pkgs())}} packages)</p>

<ul>
%for pkg in install.get_pkgs():
  <li><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
