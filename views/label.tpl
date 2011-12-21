<p>Page for the <b>{{label.branch}}</b> branch ({{len(label.get_pkgs())}} packages)</p>

<ul>
%for pkg in label.get_pkgs():
  <li><a href="/{{label.shortbranch}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
%end
</ul>
