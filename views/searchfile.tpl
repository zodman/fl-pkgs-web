matched files (on {{install.name}} branch):
%if files:
<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr><td>{{path}}</td><td><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td></tr>
%end
</table>
%else:
None
%end
