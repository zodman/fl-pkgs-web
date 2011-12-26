%rebase layout title="Package search result - %s in %s" % (keyword, branch.name)

You have searched for packages that names contain <em>{{keyword}}</em> in the <em>{{branch.name}}</em> branch. Found <strong>{{len(pkgs)}} results</strong>:
<ul>
%for pkg in pkgs:
  %if pkg.name.endswith(":source"):
    <li><a href="/{{branch.name}}/source/{{pkg.name.split(":")[0]}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %else:
    <li><a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> ({{pkg.revision}})</li>
  %end
%end
</ul>
