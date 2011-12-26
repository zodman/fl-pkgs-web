%rebase layout title="Package search result - %s in %s" % (keyword, branch.name)

<p>
You have searched for packages that names contain <em>{{keyword}}</em> in the <em>{{branch.name}}</em> branch.
</p>

<p>
Showing {{start}}-{{start + limit - 1}} of <strong>{{total}} results</strong>:
</p>

<ul>
%for pkg in pkgs:
  %if pkg.name.endswith(":source"):
    <li><a href="/{{branch.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %else:
    <li><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %end
%end
</ul>
