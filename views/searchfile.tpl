Found <strong>{{len(files)}} results</strong> (on {{install.name}} branch):
<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr><td>{{path}}</td><td><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td></tr>
%end
</table>
