matched pkgs (on {{install.name}} branch):
%if pkgs:
<ul>
%for pkg in pkgs:
  %if pkg.name.endswith(":source"):
    <li><a href="/{{install.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %else:
    <li><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %end
%end
</ul>
%else:
None
%end
