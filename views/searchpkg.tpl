Found <strong>{{len(pkgs)}} results</strong> (on {{install.name}} branch):
<ul>
%for pkg in pkgs:
  %if pkg.name.endswith(":source"):
    <li><a href="/{{install.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %else:
    <li><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %end
%end
</ul>
