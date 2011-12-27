%rebase layout title="File search result - %s in %s" % (keyword, branch.name)

<p>
You have searched for files that names contain <em>{{keyword}}</em> in the
<em>{{branch.name}}</em> branch. Found <strong>{{len(files)}} results</strong>:
</p>

<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr>
    <td class="file">{{!path.replace(keyword, "<span class=\"keyword\">%s</span>" % keyword)}}</td>
    <td><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td>
  </tr>
%end
</table>
