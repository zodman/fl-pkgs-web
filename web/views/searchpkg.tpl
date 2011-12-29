%rebase layout title="Package search result - %s in %s" % (keyword, branch.name)

<p>
%if searchon == "source":
  You have searched for source packages
%else:
  You have searched for packages that
%end
contain <em>{{keyword}}</em> in the name, in the <em>{{branch.name}}</em> branch.
</p>

<p>
Showing {{start}}-{{min(start + limit - 1, total)}} of <strong>{{total}} results</strong>:
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

%include pager url="/search/%s/package/%s" % (branch.name, keyword), start=start, limit=limit, total=total
