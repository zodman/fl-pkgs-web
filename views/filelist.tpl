<h1>Filelist of package <em>{{pkg.name}}</em> in <em>{{install.name}}</em></h1>
<pre>
%for file in pkg.filelist:
{{file}}
%end
</pre>
