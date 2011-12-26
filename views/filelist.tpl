%rebase layout title="Filelist of %s in %s branch" % (pkg.name, branch.name)

<h1>Filelist of package <a href="/{{branch.name}}/{{pkg.name}}">{{pkg.name}}</a> in <em>{{branch.name}}</em></h1>
<pre>
%for file in pkg.filelist:
{{file}}
%end
</pre>
