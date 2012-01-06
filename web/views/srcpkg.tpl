%rebase layout title="Details of %s in %s branch" % (src.name, branch.name)

<h1>Source Package: {{src.name}} ({{src.revision}})</h1>

The following binary packages are built from this source package:
<ul>
%for pkg in src.binpkgs:
  <li><a href="/{{branch.name}}/{{pkg}}">{{pkg}}</a></li>
%end
</ul>
