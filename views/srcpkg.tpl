%rebase layout title="Details of %s in %s branch" % (src.name, install.name)

<h1>Source Package: {{src.name}} ({{src.revision}})</h1>

The following binary packages are built from this source package:
<ul>
%for pkg in src.binpkgs:
  <li><a href=/{{install.name}}/{{pkg.name}}>{{pkg.name}}</a></li>
%end
</ul>
