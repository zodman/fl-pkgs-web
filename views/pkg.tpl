<h1>Package: {{pkg.name}} ({{pkg.revision}})</h1>
<p>branch <a href="/{{install.name}}">{{install.name}}</a>
<p>full installed size: {{pkg.size}}</p>
<p>source: <a href="/{{install.name}}/source/{{pkg.source.split(":")[0]}}">{{pkg.source}}</a></p>
<p>included:
<ul>
%for p in pkg.included:
  %if pkg.name.startswith("group-"):
      <li><a href="/{{install.name}}/{{p}}">{{p}}</a></li>
  %else:
      <li>{{p}}</li>
  %end
%end
</ul>
</p>
<p>buildtime: {{pkg.buildtime}}</p>
%if pkg.buildlog:
  <p><a href="{{pkg.buildlog}}">buildlog</a></p>
%end
<p>flavors: {{pkg.flavors}}</p>
