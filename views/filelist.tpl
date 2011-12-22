<h1>Filelist of package <a href="/{{install.name}}/{{pkg.name}}">{{pkg.name}}</a> in <em>{{install.name}}</em></h1>
<pre>
%for file in pkg.filelist:
{{file}}
%end
</pre>
