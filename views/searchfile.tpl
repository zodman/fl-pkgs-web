%rebase layout title="File search result - %s in %s" % (keyword, install.name)

You have searched for files that names contain <em>{{keyword}}</em> in the <em>{{install.name}}</em> branch. Found <strong>{{len(files)}} results</strong>:

<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr><td>{{path}}</td><td><a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td></tr>
%end
</table>
