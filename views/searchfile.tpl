%rebase layout title="File search result - %s in %s" % (keyword, branch.name)

<p>
%if searchon == "path":
  You have searched for paths that end with <em>{{keyword}}</em>,
%elif searchon == "filename":
  You have searched for files that contain <em>{{keyword}}</em> in the name,
%elif searchon == "fullpath":
  You have searched for paths that contain <em>{{keyword}}</em>,
%end
in the <em>{{branch.name}}</em> branch. Found <strong>{{len(files)}} results</strong>:
</p>

%if truncated:
<div class="note">
<p>
Note: Your search was too wide so we will only display the first 100 matches.
Please consider using a longer keyword.
</p>
</div>
%end

%if files:
<table>
<tr><th>File</th><th>Package</th></tr>
%for (path, pkg) in files:
  <tr>
    <td class="file">{{!path.replace(keyword, "<span class=\"keyword\">%s</span>" % keyword)}}</td>
    <td><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td>
  </tr>
%end
</table>
%end
