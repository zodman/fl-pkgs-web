%rebase layout title="File search result - %s in %s" % (keyword, branch.name)

<p>
%if searchon == "path":
  You have searched for paths that end with
%elif searchon == "filename":
  You have searched for filenames that contain
%elif searchon == "fullpath":
  You have searched for paths that contain
%end
<em>{{keyword.lower()}}</em>, in the <em>{{branch.name}}</em> branch.
</p>

<p>
{{"Showing" if truncated else "Found"}} <strong>{{len(files)}} results</strong>:
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
    <td class="file">{{!re.sub(r"(?i)(%s)" % keyword, r'<span class="keyword">\1</span>', path)}}</td>
    <td><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</td>
  </tr>
%end
</table>
%end
