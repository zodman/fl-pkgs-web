matched files:
<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr><td>{{path}}</td><td>{{pkg.name}} ({{pkg.revision}})</td></tr>
%end
</table>
