%rebase layout title="Details of %s in %s branch" % (pkg.name, branch.name)

<h1>Package: {{pkg.name}} ({{pkg.revision}})</h1>
<p>branch <a href="/{{branch.name}}">{{branch.name}}</a></p>
<p>full installed size: {{pkg.size}}</p>
<p>source: <a href="/{{branch.name}}/source/{{pkg.source.split(":")[0]}}">{{pkg.source}}</a></p>
%if not pkg.name.startswith("group-"):
<p><a href="/{{branch.name}}/{{pkg.name}}/filelist">list of files</a></p>
%end
<p>included:</p>
<ul>
%for p in pkg.included:
  %if pkg.name.startswith("group-"):
      <li><a href="/{{branch.name}}/{{p}}">{{p}}</a></li>
  %else:
      <li>{{p}}</li>
  %end
%end
</ul>
<p>buildtime: {{pkg.buildtime}}</p>
%if pkg.buildlog:
  <p><a href="{{pkg.buildlog}}">buildlog</a></p>
%end
<p>flavors: {{pkg.flavors}}</p>
