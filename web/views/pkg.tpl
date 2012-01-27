%rebase layout title="Details of %s in %s branch" % (pkg.name, branch.name)

%include quick-search branch=branch.name

<h2>Package: {{pkg.name}} ({{pkg.revision}})</h2>
<p>
	<strong>	Branch </strong>
%if 'devel' in branch.name: 
			<a class="label important" href="/{{branch.name}}">{{branch.name}}</a>
%elif 'qa' in branch.name: 
			<a class="label warning" href="/{{branch.name}}">{{branch.name}}</a>
%else:
			<a class="label" href="/{{branch.name}}">{{branch.name}}</a>
%end
	
</p>
<p>source: <a href="/{{branch.name}}/source/{{pkg.source.split(":")[0]}}">{{pkg.source}}</a></p>

<p>full installed size: {{pkg.size}}</p>

%if not pkg.name.startswith("group-"):
	<p><a href="/{{branch.name}}/{{pkg.name}}/filelist">list of files</a></p>
%end
<p>included:</p>
<blockquote>
<ul class="unstyled">
%for p in pkg.included:
  %if pkg.name.startswith("group-"):
      <li><a href="/{{branch.name}}/{{p}}">{{p}}</a></li>
  %else:
      <li>{{p}}</li>
  %end
%end
</ul>
</blockquote>
<p>buildtime: {{pkg.buildtime}} <br/>
%if pkg.buildlog:
  <a href="{{pkg.buildlog}}">buildlog</a>
%end
</p>
<p>flavors: {{pkg.flavors}}</p>
